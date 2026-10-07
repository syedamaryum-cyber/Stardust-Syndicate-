import time
from astropy.io import fits
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

# 🌌 Page Config & Sci-Fi Dark Theme Styling
st.set_page_config(
    page_title="Stardust Syndicate - SPHEREx Blinker",
    page_icon="🔭",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background-color: #0b0f19; color: #e2e8f0; }
    .stSidebar { background-color: #1e293b; }
    h1, h2, h3 { color: #38bdf8 !important; font-family: 'Courier New', monospace; }
    .metric-card { background: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    </style>
""",
    unsafe_allow_html=True,
)

# App Header
st.title("🔭 Stardust Syndicate: SPHEREx Rogue Object Blinker")
st.markdown(
    "### Interactive Astrometric Comparator for **WISE 0855−0714** (The Cold"
    " Ghost)"
)
st.markdown("---")


# Load baseline FITS file safely
@st.cache_data
def load_baseline_fits():
  hdu_0 = fits.open("stardust_target_epoch_0.fits")[0]
  return hdu_0.data, hdu_0.header


try:
  img_data_0, header = load_baseline_fits()

  # Sidebar Telemetry & Witty Mission Flavor
  st.sidebar.header("🎛️ Mission Controls")
  st.sidebar.markdown(
      "**Target:** WISE 0855−0714\n* **Distance:** ~7.2 light-years (Basically"
      " next-door neighbors!)\n* **Temp:** ~250 K / -23°C (Colder than your"
      " fridge 🥶)\n* **Proper Motion:** 8.15\"/yr (Speedy ghost 👻)"
  )

  # Dynamic vibe check based on user timeline slider
  st.sidebar.markdown("---")
  st.sidebar.header("⏳ Temporal Baseline")
  delta_years = st.sidebar.slider(
      "Simulation Time Jump (Years):", 1.0, 15.0, 10.0, 1.0
  )

  chill_factor = (
      "Absolute Zero Nomad 🧊"
      if delta_years > 10
      else "Cruising Stellar Breeze 🌠"
  )
  st.sidebar.info(f"🛰️ **Vibe Check:** {chill_factor}")
  st.sidebar.markdown("---")

  mode = st.sidebar.radio(
      "Display Mode:", ("Manual Blinker Toggle", "⚡ Auto-Blink Animation Loop")
  )

  # Dynamically calculate pixel shifts based on proper motion values
  pixel_scale = 1.375  # arcsec/pixel for WISE
  shift_x_arcsec = (-8123.7 / 1000.0) * delta_years
  shift_y_arcsec = (673.2 / 1000.0) * delta_years

  shift_x_pixels = int(np.round(shift_x_arcsec / pixel_scale))
  shift_y_pixels = int(np.round(shift_y_arcsec / pixel_scale))

  # Build dynamic Epoch 1 image using NumPy matrix manipulation with boundary clipping
  img_data_1 = img_data_0.copy()
  source_y, source_x = np.unravel_index(np.argmax(img_data_0), img_data_0.shape)
  box_size = 15

  stamp = img_data_0[
      source_y - box_size : source_y + box_size,
      source_x - box_size : source_x + box_size,
  ].copy()
  bg_median = np.median(img_data_0)

  # Clear old position and stamp at the shifted proper-motion coordinate
  img_data_1[
      source_y - box_size : source_y + box_size,
      source_x - box_size : source_x + box_size,
  ] = bg_median

  max_y, max_x = img_data_0.shape
  new_y = np.clip(source_y + shift_y_pixels, box_size, max_y - box_size)
  new_x = np.clip(source_x + shift_x_pixels, box_size, max_x - box_size)

  img_data_1[
      new_y - box_size : new_y + box_size, new_x - box_size : new_x + box_size
  ] = stamp

  # Layout columns
  col1, col2 = st.columns([2, 1])

  with col1:
    if mode == "Manual Blinker Toggle":
      epoch_choice = st.radio(
          "Select Epoch View:",
          (
              "Epoch 0: AllWISE Baseline (2010)",
              f"Epoch 1: Shifted (+{int(delta_years)} Yrs)",
          ),
          horizontal=True,
      )

      fig, ax = plt.subplots(figsize=(7, 7))
      fig.patch.set_facecolor("#0b0f19")
      ax.set_facecolor("#0b0f19")

      if "Baseline" in epoch_choice:
        ax.imshow(img_data_0, cmap="inferno", origin="lower")
        ax.set_title(
            "Epoch 0: AllWISE Baseline Survey", color="#38bdf8", fontsize=14
        )
      else:
        ax.imshow(img_data_1, cmap="inferno", origin="lower")
        ax.set_title(
            f"Epoch 1: Shifted +{int(delta_years)} Yrs (ΔX:"
            f" {shift_x_pixels}px, ΔY: {shift_y_pixels}px)",
            color="#f43f5e",
            fontsize=14,
        )

      ax.axis("off")
      st.pyplot(fig)

    else:
      st.markdown("### ⚡ Live Blinker Loop Active (Watching proper motion...)")
      speed = st.slider("Blink Speed (Seconds per frame):", 0.1, 1.5, 0.5)
      frame_slot = st.empty()

      # Auto-blink execution loop
      for _ in range(15):
        fig0, ax0 = plt.subplots(figsize=(6, 6))
        fig0.patch.set_facecolor("#0b0f19")
        ax0.set_facecolor("#0b0f19")
        ax0.imshow(img_data_0, cmap="inferno", origin="lower")
        ax0.set_title("🟢 Epoch 0 (Baseline)", color="#38bdf8")
        ax0.axis("off")
        frame_slot.pyplot(fig0)
        plt.close(fig0)
        time.sleep(speed)

        fig1, ax1 = plt.subplots(figsize=(6, 6))
        fig1.patch.set_facecolor("#0b0f19")
        ax1.set_facecolor("#0b0f19")
        ax1.imshow(img_data_1, cmap="inferno", origin="lower")
        ax1.set_title(
            f"🔴 Epoch 1 (+{int(delta_years)} Yrs Shift)", color="#f43f5e"
        )
        ax1.axis("off")
        frame_slot.pyplot(fig1)
        plt.close(fig1)
        time.sleep(speed)

  with col2:
    st.markdown("### 📊 Telemetry & Analysis")
    st.markdown(
        f"""
        <div class="metric-card">
        <b>🚀 Live Mission Telemetry:</b><br>
        • <b>Timeline Jump:</b> {int(delta_years)} Earth Years<br>
        • <b>Calculated Offset:</b> ΔX = {shift_x_pixels} px, ΔY = {shift_y_pixels} px<br><br>
        <b>🕵️‍♂️ The Backstory:</b><br>
        WISE 0855-0714 is the coolest known brown dwarf out there—a failed star wandering the cosmos like an interstellar ghost. Its massive proper motion makes it the ultimate test subject for SPHEREx time-domain astrometry surveys!
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    st.success(
        "✨ **Status:** The ghost is successfully sprinting across the grid."
    )

except Exception as e:
  st.error(f"⚠️ Telemetry feed interrupted: {e}")