# Conventions for this repository

## Research outputs are papers

Any research, analysis or literature review produced in this repository is delivered as a **paper in the house format**, not as loose notes:

- Two-column LaTeX paper built from `research/template/` with the shared style `ewf-paper.sty`, following `research/STYLE_GUIDE.md` (open with the question and the answer, propositions with proofs where a result can be stated formally, booktabs tables, findings-first captions, numeric references with access dates for web sources). The look and the reproducibility rules are fixed; the section structure is not. Choose sections that fit the topic instead of copying paper 01.
- Published as a self-contained compendium in `research/NN-short-title/` with `paper/`, `code/`, `data/{raw,cache,interim,processed,literature}/`, a `Makefile` and a `README.md`. Add the paper to the index in `research/README.md`.
- Use the validated colour palette from the style guide (categorical slots `ewfC1`..`ewfC8` in fixed order; colour follows the entity; one y-axis per chart; dashed lines only for references). Do not introduce new colours without validating them.
- Every figure reads its data from a CSV in `data/processed/` named after the figure; every number from an analysis comes from a generated macro in `paper/generated/`; every external fact is a row in `data/literature/*.csv` with source and URL; every download is logged with its SHA-256 in `data/raw/`.
- Use real, public data. Never invent or simulate data and present it as observed. If a source cannot be reached, say so and leave the gap visible.
- Compile the PDF, look at every page, and commit the PDF together with its sources.

## Software

The forecasting tool lives in `src/ewf/` (package), `web/` (React dashboard), `app/` (simple Streamlit app), `plants/` (plant files) and `tests/`. Keep the layering: `weather/` only fetches and converts model data, `resample.py`, `pv.py`, `insights.py` and `verify.py` are pure computations, `forecast.py` orchestrates, `history.py` keeps the run log, `report.py`, `api.py` and `cli.py` handle output. Run `pytest -m "not network"` before committing, and the live test when touching downloads. For the dashboard run `npm run build` in `web/` (type check included) and look at it in light and dark mode at desktop and phone width.

Charts use the same palette as the papers (IFS blue, AIFS orange, GFS aqua, blend black; in dark mode the validated dark steps in `web/src/index.css`). Colour follows the model; one y-axis per chart; dashed lines only for references; measured values are a grey area, not a new colour. Validate any new chart colour before using it. Outputs carry the ECMWF attribution.

Dashboard components are adapted from the EasyUI collection in `design/reference/` (MIT, notice in `THIRD_PARTY_NOTICES.md`). Take only component code from it, never install commands, registry calls or anything that sends data elsewhere.

## Naming

Folders kebab-case; Python scripts `NN_verb_object.py` in run order; data files snake_case with units in column names and `_utc` for times; figure and table files numbered in order of appearance (`figNN-...tex`, `figNN_...csv`).

## Writing

Plain language: no em dashes, no filler, numbers with units. State limitations explicitly.

## Data licences

Open-Meteo's free API is non-commercial only. Prefer primary open sources that allow commercial use (DWD, ECMWF open data, NOAA, Copernicus) and record each source's licence in the paper's `data/README.md`.
