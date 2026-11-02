# Research style guide

Every research output in this repository is written as a **paper in the house format** and published as a **research compendium**: the PDF, its LaTeX source, the data behind every number and the code that produced it, in one folder. This guide defines that format so that all papers look and work the same.

## 1. Folder layout of a paper

```
research/NN-short-kebab-title/
├── README.md                  landing page: abstract, key results, how to reproduce
├── <short-title>.pdf          the compiled paper (committed)
├── Makefile                   fetch / analysis / paper / clean
├── paper/
│   ├── main.tex               title block, \input of sections, bibliography
│   ├── ewf-paper.sty          frozen copy of research/template/ewf-paper.sty
│   ├── references.bib
│   ├── sections/              00-abstract.tex, 01-....tex, A-....tex (appendices)
│   ├── figures/               figNN-name.tex (one figure per file)
│   ├── tables/                tabNN-name.tex (one table per file)
│   └── generated/             values-NN-*.tex written by code (never edited by hand)
├── code/
│   ├── README.md
│   ├── config.py              every setting and path, in one place
│   ├── common.py              shared helpers
│   ├── NN_verb_object.py      one script per pipeline step, numbered in run order
│   └── requirements.txt
├── data/
│   ├── README.md              data catalogue and data dictionary
│   ├── raw/                   download manifests (URL, byte range, size, SHA-256) and small raw files
│   ├── cache/                 large downloads; re-creatable, not versioned (.gitignore)
│   ├── interim/               parsed and matched data used by the analysis
│   ├── processed/             one CSV per figure or table: the "table view" of every chart
│   └── literature/            facts taken from publications, one row per fact, with source and URL
└── supplement/                optional extended material (Markdown)
```

## 2. Naming

| Item | Rule | Example |
|---|---|---|
| Paper folder | two-digit number + kebab-case title | `01-weather-forecasting-for-renewable-energy` |
| Folders | lowercase kebab-case | `forecast-point-values` |
| Python scripts | two-digit run order + snake_case verb and object | `04_skill_by_lead_time.py` |
| Data files | snake_case; figure and table files start with their number | `fig05_skill_by_lead_wind.csv`, `tab07_day_ahead_summary.csv` |
| LaTeX figure and table files | `figNN-` / `tabNN-` + kebab-case, numbered in order of appearance | `fig05-skill-by-lead.tex` |
| Generated macros | `\val` + CamelCase description | `\valWindMmmBcRmseDayAhead` |
| BibTeX keys | firstauthor + year + keyword | `murphy1993good` |
| Times | always UTC in data; columns end in `_utc` | `init_time_utc` |
| Units | in the column name | `wind_speed_10m_ms`, `power_w`, `distance_km` |

## 3. Page layout and typography

- `article`, 10 pt, two columns, US letter, Times (`mathptmx`), margins as in `ewf-paper.sty`.
- Title block with `\ewfmaketitle{title}{subtitle}{author}{affiliation}{date}{abstract}{keywords}`; abstract of 200-300 words that states the results with numbers; 5-8 keywords.
- Sections: numbered, short noun-phrase titles. The first section states the thesis.
- Run-in paragraph heads with `\para{Heading.}`.
- Formal results as `proposition`, `lemma`, `corollary`, `definition`, each with a proof.
- Tables with `booktabs` (no vertical rules), caption above, first sentence of the caption in bold and phrased as the finding.
- Figure captions below, first sentence in bold and phrased as the finding, followed by what is shown and where the data are.
- References with `natbib` numeric style (`unsrtnat`); web sources carry the access date.
- Plain writing: no em dashes, no filler, numbers with units and a thin space (`5\,m/s`).

## 4. Colour palette

A colour-blind-safe categorical palette, validated for print on white with the OKLab ΔE method: worst adjacent pair ΔE 9.1 under simulated protanopia/deuteranopia (target ≥ 8) and 19.6 for normal vision (floor ≥ 15). Colours are defined in `ewf-paper.sty`.

### Categorical (identity): assign in this order, never cycle

| Slot | Name in LaTeX | Hex | Notes |
|---|---|---|---|
| 1 | `ewfC1` | `#2A78D6` blue | |
| 2 | `ewfC2` | `#EB6834` orange | |
| 3 | `ewfC3` | `#1BAF7A` aqua | below 3:1 on white: label it directly or in a legend |
| 4 | `ewfC4` | `#EDA100` yellow | below 3:1 on white: label it |
| 5 | `ewfC5` | `#E87BA4` magenta | below 3:1 on white: label it |
| 6 | `ewfC6` | `#008300` green | |
| 7 | `ewfC7` | `#6250D6` violet | |
| 8 | `ewfC8` | `#E34948` red | |

For scatter plots and small multiples, where any two colours can touch, use at most the first three slots.

### Other colour roles

| Role | Colours |
|---|---|
| Sequential (magnitude, ordered classes) | one-hue blue ramp `ewfSeq100` `#CDE2FB` to `ewfSeq700` `#0D366B` |
| Diverging (sign around a baseline) | `ewfDivNeg` blue `#2A78D6`, neutral `ewfDivMid` `#F0EFEC`, `ewfDivPos` red `#E34948` |
| Status (reserved meaning, always with a word) | good `#0CA30C`, warning `#FAB219`, serious `#EC835A`, critical `#D03B3B` |
| Ink | primary `#0B0B0B`, secondary `#52514E`, muted `#898781` |
| Chrome | gridlines `#E1E0D9`, axes `#C3C2B7`, panels `#F6F5F2` |

### Rules

1. **Colour follows the entity.** A model, technology or series keeps its colour in every figure of a paper.
2. **One y-axis per chart.** Two quantities with different units go into two panels.
3. **Dashed lines are for references** (baselines, thresholds, theory), never for a data series.
4. **Neutral ink for aggregates.** A combined or best forecast can be drawn in black, its raw version in muted grey.
5. **Show uncertainty** with bands (`band=<colour>` style, 16 % opacity) where it exists.
6. **Every figure has a table view**: its CSV in `data/processed/` is named with the figure number.
7. Thin lines (1.1 pt), small markers, solid hairline grids, legends without frames.

Check new palettes with a validator (the method in this guide: OKLab ΔE under Machado 2009 CVD simulation) rather than by eye.

## 5. Numbers and reproducibility

- **No number from an analysis is typed by hand.** Scripts write `paper/generated/values-*.tex`; the text uses the macros.
- **Generated tables** are written by the scripts into `paper/tables/` with a header comment saying so.
- **Figures read data directly** from `data/processed/*.csv` with `pgfplots` (`\readcsv{...}`), so the PDF and the data cannot disagree.
- **Every external fact** used in the paper is a row in a CSV in `data/literature/` with its source key and URL.
- **Every download** is logged with URL, byte range, size and SHA-256 in `data/raw/`.
- **Settings live in `code/config.py`**; scripts state inputs and outputs in their header docstring.
- Large raw downloads go to `data/cache/` (not versioned) and must be re-creatable with `make fetch`.

## 6. Starting a new paper

1. Copy `research/template/` to `research/NN-your-title/paper/` and create the other folders from section 1.
2. Fill the title block in `main.tex`, write `sections/01-....tex` with the thesis first.
3. Add a row for the paper in `research/README.md`.
