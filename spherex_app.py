"""SPHEREx Sky Blink as a browser app.   Run:  streamlit run spherex_app.py
Needs spherex_blink.py in the same folder.  pip install streamlit numpy pillow matplotlib
(real data also: astropy astroquery reproject)"""
import io
import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import spherex_blink as sb

# Positions propagated to ~2026.0 from approximate catalogue values.
PRESETS = {
    "WISE 0855-0714 (fast brown dwarf)": ("133.7682", "-7.2428", 4),
    "Barnard's Star": ("269.4462", "4.7676", 6),
    "Epsilon Indi (A + Ba/Bb)": ("330.9766", "-56.8351", 14),
    "RW Aurigae (variable)": ("76.9565", "30.4014", 4),
    "R Draconis (Mira variable)": ("248.178", "66.755", 4),
    "Custom": ("133.7682", "-7.2428", 4),
}

st.set_page_config(page_title="SPHEREx Sky Blink", layout="wide")
st.title("SPHEREx Sky Blink")
st.caption("Enter a patch of sky and watch how it changes over time. Moving objects jump between frames.")

with st.sidebar:
    name = st.selectbox("Target", list(PRESETS))
    ra0, dec0, fov0 = PRESETS[name]
    ra_s = st.text_input("RA (deg or 08h55m10.8s)", ra0, key=f"ra_{name}")
    dec_s = st.text_input("Dec (deg or -7d14m42s)", dec0, key=f"dec_{name}")
    fov = st.slider("Field of view (arcmin)", 2, 30, fov0, key=f"fov_{name}")
    band = st.selectbox("Band", ["Colour composite", "D1 0.75-1.09 um", "D2 1.09-1.62 um", "D3 1.62-2.42 um",
                                 "D4 2.42-3.82 um", "D5 3.82-4.42 um", "D6 4.42-5.00 um"])
    mode = st.selectbox("Display", ["raw", "first", "median"],
                        format_func={"raw": "Raw epoch", "first": "Difference vs first epoch",
                                     "median": "Difference vs median"}.get)
    bin_days = st.slider("Co-add exposures within (days)", 5, 120, 30)
    fps = st.slider("Blink speed (frames/sec)", 1, 8, 2)
    demo = st.checkbox("Use simulated data (offline demo)", True)
    with st.expander("Advanced"):
        collection = st.text_input("IRSA collection", "spherex_qr")
        max_images = st.number_input("Max exposures", 10, 1000, 200)
        maskbits = st.number_input("FLAGS bits to mask (0 = none)", 0, 2**31 - 1, 0)


@st.cache_data(show_spinner="Getting SPHEREx images...")
def load(ra, dec, fov, demo, collection, max_images, maskbits):
    N = max(16, round(fov * 60 / sb.PIX))
    return sb.simulate(N) if demo else sb.fetch_irsa(ra, dec, fov, N, collection, max_images, maskbits)


try:
    ra, dec = sb.parse_coord(ra_s, True), sb.parse_coord(dec_s, False)
except Exception:
    st.error("Could not read those coordinates.")
    st.stop()

try:
    exps = load(ra, dec, fov, demo, collection, int(max_images), int(maskbits))
except Exception as e:
    st.error(f"Could not fetch real data: {e}")
    st.info("Tick 'Use simulated data' in the sidebar to try the app offline.")
    st.stop()
if not exps:
    st.warning("No SPHEREx exposures cover that position yet.")
    st.stop()

if demo:
    st.warning("Showing simulated data, not real SPHEREx images.")
groups = sb.RGB_GROUPS if band == "Colour composite" else [[int(band[1]) - 1]]
epochs, cube = sb.build_cube(exps, bin_days, groups)
rgb = sb.to_rgb(cube, mode)
buf = io.BytesIO()
frames = sb.write_gif(rgb, epochs, buf, 560, fps)  # kept in memory, nothing saved to disk

t1, t2, t3 = st.tabs(["Blink", "Step through epochs", "Spectrum"])
with t1:
    st.image(buf.getvalue(), width=560)
    st.caption(f"{len(epochs)} epochs, {rgb.shape[1]}x{rgb.shape[2]} px, north up, east left. "
               "In difference modes a mover appears as a bright/dark pair.")
    st.download_button("Download this GIF (optional)", buf.getvalue(), "blink.gif", "image/gif")
with t2:
    i = st.slider("Epoch", 1, len(epochs), 1) - 1
    st.image(frames[i], width=560, caption=f"Epoch {i + 1}/{len(epochs)}: {sb.mjd_to_date(epochs[i])}")
with t3:
    pts = [(e["lam"], np.nanmean(e["img"][e["img"].shape[0] // 2 - 1:e["img"].shape[0] // 2 + 2,
                                         e["img"].shape[1] // 2 - 1:e["img"].shape[1] // 2 + 2])
            - np.nanmedian(e["img"]), e["det"]) for e in exps if np.isfinite(e["lam"])]
    if pts:
        p = np.array(pts)
        fig, ax_spec = plt.subplots(figsize=(7, 3.5))
        fig.patch.set_facecolor('#0B0E14')
        ax_spec.set_facecolor('#0B0E14')

        scatter = ax_spec.scatter(p[:, 0], p[:, 1], c=p[:, 2], cmap="turbo", s=14, edgecolor='none')
        ax_spec.set_xlabel("Wavelength (µm)", color="#E0E6ED", fontfamily="monospace")
        ax_spec.set_ylabel("Flux Intensity", color="#E0E6ED", fontfamily="monospace")
        ax_spec.set_title("On-the-Fly Aperture Spectrum (All Epochs)", color="#00FFCC", fontfamily="monospace", fontweight="bold")

        ax_spec.tick_params(colors="#8F9CAE")
        ax_spec.grid(True, color="#00ffcc", alpha=0.2)

        cbar = fig.colorbar(scatter, ax=ax_spec)
        cbar.set_label("Detector Band / Channel", color="#E0E6ED")
        cbar.ax.yaxis.set_tick_params(color="#8F9CAE")
        plt.setp(cbar.ax.get_yticklabels(), color="#8F9CAE")

        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("No valid wavelength headers found for the selected exposure set.")