# 🔭 Stardust Syndicate: SPHEREx Rogue Object Blinker

> *An interactive astrometric time-domain blinker designed to hunt and visualize the proper motion of ultra-cold rogue worlds (like WISE 0855−0714) using FITS data.* 🌌🛰️

---

## 🚀 Mission Overview
Built for the **NASA Space Apps Challenge**, this tool acts as an automated observatory blink comparator. By taking baseline AllWISE/NEOWISE FITS surveys and applying dynamic proper-motion vector matrices via **NumPy**, it allows researchers to instantly spot hyper-speed substellar wanderers across variable temporal baselines (1–15 years).

---

## 🛠️ Tech Stack & Dependencies
* **Language:** Python 3.14+
* **Framework:** Streamlit (Sci-fi dark-themed interactive dashboard)
* **Astrometry & Data:** Astropy (FITS file parsing & WCS handling)
* **Visualization:** Matplotlib (`inferno` deep-space colormaps)
* **Matrix Engine:** NumPy (Dynamic coordinate shifts & boundary clamping)

---

## ⚡ Quick Start Guide (Local Deployment)

Want to spin up the observatory on your local machine? Follow these simple steps:

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/stardust-spherex-blinker.git](https://github.com/YOUR_USERNAME/stardust-spherex-blinker.git)
   cd stardust-spherex-blinker