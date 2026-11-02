#!/usr/bin/env python3
"""
SPHEREx sky blink backend module for FITS data ingestion, re-projection, and GIF generation.
"""
import argparse
import re
import numpy as np
from PIL import Image, ImageDraw

PIX = 6.2  # arcsec per SPHEREx pixel
DET = [(.75, 1.09), (1.09, 1.62), (1.62, 2.42), (2.42, 3.82), (3.82, 4.42), (4.42, 5.0)]  # microns
RGB_GROUPS = [[4, 5], [2, 3], [0, 1]]  # R, G, B detector channel indices


def parse_coord(s, is_ra):
    s = str(s).strip()
    if not s:
        raise ValueError("Coordinate string is empty")

    parts = re.findall(r"[+-]?\d+(?:\.\d+)?", s)
    if not parts:
        raise ValueError(f"Invalid coordinate string: {s}")

    sign = -1 if any(ch == "-" for ch in s) and not any(ch == "+" for ch in s) else 1
    values = [abs(float(p)) for p in parts]
    x = values[0] + (values[1] / 60 if len(values) > 1 else 0) + (values[2] / 3600 if len(values) > 2 else 0)
    if is_ra:
        x *= 15
    return -x if sign < 0 else x


def fetch_irsa(ra, dec, fov, N, collection, max_images, maskbits):
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    from astropy.io import fits
    from astropy.wcs import WCS
    from astroquery.ipac.irsa import Irsa
    from reproject import reproject_interp

    c = SkyCoord(ra * u.deg, dec * u.deg)
    tw = WCS(naxis=2)
    tw.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    tw.wcs.crval = [ra, dec]
    tw.wcs.crpix = [N / 2 + .5, N / 2 + .5]
    tw.wcs.cdelt = [-PIX / 3600, PIX / 3600]

    tbl = Irsa.query_sia(pos=(c, fov * u.arcmin), collection=collection)
    rows = [r for r in tbl if "fits" in str(r["access_format"]).lower()][:max_images]
    out = []
    for i, r in enumerate(rows):
        try:
            with fits.open(r["access_url"], cache=True) as h:
                im = h["IMAGE"]
                hd0 = h[0].header
                det = int(im.header.get("DETECTOR", hd0.get("DETECTOR", 1)))
                mjd = float(im.header.get("MJD-AVG", hd0.get("MJD-AVG", im.header.get("MJD-OBS", 60810))))
                data = np.array(im.data, dtype=float)
                if maskbits and "FLAGS" in h:
                    data[(np.array(h["FLAGS"].data) & maskbits) != 0] = np.nan
                w = WCS(im.header)
                stamp, _ = reproject_interp((data, w), tw, shape_out=(N, N))
                lam = np.nan
                try:
                    ww = WCS(im.header, fobj=h, key="W")
                    x, y = w.world_to_pixel(c)
                    lam = float(np.ravel(ww.pixel_to_world_values(x, y)[0])[0])
                except Exception:
                    pass
            out.append(dict(mjd=mjd, det=det - 1, lam=lam, img=stamp))
        except Exception:
            continue
    return out


def simulate(N, seed=3):
    rng = np.random.default_rng(seed)
    stars = [(rng.uniform(-1, 1, 2) * N * PIX / 2, rng.uniform(.02, .5) ** 1, rng.uniform(1, 3)) for _ in range(30)]
    mover = dict(off=np.array([0., 0.]), pm=np.array([-8.0, 0.7]), amp=.003, s=-6.5)
    yy, xx = np.mgrid[0:N, 0:N]
    out = []
    for e in range(6):
        yr = 2025.37 + e * .25
        for d in range(6):
            for k in range(3):
                lam = DET[d][0] + (k * 6 + 3) * (DET[d][1] - DET[d][0]) / 17
                img = rng.normal(0, .03 / np.sqrt(2), (N, N))
                srcs = [(o, a, s, 0) for o, a, s in stars]
                srcs.append((mover["off"] + mover["pm"] * (yr - 2026), mover["amp"], mover["s"], 0))
                srcs.append((np.array([40., 30.]), 2.0, 1.8, 1))
                for off, amp, s, var in srcs:
                    f = amp * (lam / 1.6) ** -s * ((1 + .8 * np.sin(2 * np.pi * yr * 365.25 / 245) * (1.5 / lam) ** 1.5) if var else 1)
                    x, y = N / 2 - off[0] / PIX, N / 2 - off[1] / PIX
                    img += f * np.exp(-((xx + .5 - x) ** 2 + (yy + .5 - y) ** 2) / (2 * .9 ** 2))
                out.append(dict(mjd=60810 + (yr - 2025.37) * 365.25 + d * 2 + k * .5, det=d, lam=lam, img=img))
    return out


def build_cube(exps, bin_days, dets_wanted):
    if not exps:
        return [], np.empty((0, len(dets_wanted), 0, 0), dtype=float)

    mjd0 = min(e["mjd"] for e in exps)
    bins = sorted({int((e["mjd"] - mjd0) // bin_days) for e in exps})
    N = exps[0]["img"].shape[0]
    cube = np.full((len(bins), len(dets_wanted), N, N), np.nan)
    epochs = []
    for bi, b in enumerate(bins):
        sel = [e for e in exps if int((e["mjd"] - mjd0) // bin_days) == b]
        if not sel:
            continue
        epochs.append(np.mean([e["mjd"] for e in sel]))
        for gi, g in enumerate(dets_wanted):
            stk = []
            for e in sel:
                if e["det"] in g:
                    im = e["img"] - np.nanmedian(e["img"])
                    stk.append(im)
            if stk:
                cube[bi, gi] = np.nanmean(stk, axis=0)
    return epochs, cube


def to_rgb(cube, mode):
    if cube.size == 0:
        return np.empty((0, 0, 0, 3), dtype=np.uint8)

    c = cube.copy()
    if mode == "first":
        c = c - c[0:1]
    elif mode == "median":
        c = c - np.nanmedian(c, axis=0, keepdims=True)
    diff = mode in ("first", "median")
    c = np.nan_to_num(c)
    sig = max(1.4826 * np.median(np.abs(c - np.median(c))), 1e-12)
    z = c / sig
    zmax = max(np.percentile(np.abs(z), 99.8), 5)
    v = np.arcsinh(z) / np.arcsinh(zmax)
    v = .5 + .5 * v if diff else v
    v = np.clip(v, 0, 1)
    if v.shape[1] == 1:
        v = np.repeat(v, 3, axis=1)
    return (v.transpose(0, 2, 3, 1) * 255).astype(np.uint8)


def mjd_to_date(m):
    return str(np.datetime64("1858-11-17") + np.timedelta64(int(m), "D"))


def write_gif(rgb, epochs, out, size, fps):
    frames = []
    for im, m in zip(rgb, epochs):
        p = Image.fromarray(im).resize((size, size), Image.BICUBIC)
        d = ImageDraw.Draw(p)
        d.text((10, 8), f"MJD {m:.1f} ({mjd_to_date(m)})", fill=(255, 255, 255))
        d.line([(size // 2 - 8, size // 2), (size // 2 + 8, size // 2)], fill=(0, 255, 204))
        d.line([(size // 2, size // 2 - 8), (size // 2, size // 2 + 8)], fill=(0, 255, 204))
        frames.append(p)
    if not frames:
        raise ValueError("No frames available to write to GIF")
    frames[0].save(out, format="GIF", save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
    return frames