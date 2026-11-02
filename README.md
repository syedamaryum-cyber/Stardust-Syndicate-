# Stardust Syndicate

Stardust Syndicate is a Streamlit app for exploring a FITS-based astrometric comparison of a cold brown dwarf candidate.

## Features
- Loads a local FITS baseline image robustly from the repository directory
- Simulates a shifted epoch image using proper-motion style offsets
- Lets you compare images manually or in a looping animation
- Provides a sci-fi themed mission dashboard for quick exploration

## Quick start
1. Install dependencies:
   python -m pip install -r requirements.txt
2. Launch the app:
   python -m streamlit run app.py

The app expects the FITS file `stardust_target_epoch_0.fits` to be present in the project root.

## SPHEREx Sky Blink

The session's SPHEREx browser app and backend are `spherex_app.py` and
`spherex_blink.py`. Launch the app with:

```bash
python -m streamlit run spherex_app.py
```

It starts in offline simulated-data mode. The optional real-data mode queries
IRSA and requires the astronomy dependencies listed in `requirements.txt`.

## Copilot sessions

See [COPILOT_SESSIONS.md](COPILOT_SESSIONS.md) for the available session inventory and history notes.
