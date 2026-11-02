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

The forecasting tool lives in `src/ewf/` (package), `app/` (web app), `plants/` (plant files) and `tests/`. Keep the layering: `weather/` only fetches and converts model data, `resample.py` and `pv.py` are pure computations, `forecast.py` orchestrates, `report.py` and `cli.py` handle output. Run `pytest -m "not network"` before committing, and the live test when touching downloads. Charts use the same palette as the papers (IFS blue, AIFS orange, GFS aqua, blend black). Outputs carry the ECMWF attribution.

## Naming

Folders kebab-case; Python scripts `NN_verb_object.py` in run order; data files snake_case with units in column names and `_utc` for times; figure and table files numbered in order of appearance (`figNN-...tex`, `figNN_...csv`).

## Writing

Plain language: no em dashes, no filler, numbers with units. State limitations explicitly.

## Data licences

Open-Meteo's free API is non-commercial only. Prefer primary open sources that allow commercial use (DWD, ECMWF open data, NOAA, Copernicus) and record each source's licence in the paper's `data/README.md`.
