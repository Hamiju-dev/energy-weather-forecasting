# Research

Research outputs of this repository. Each paper is a self-contained **research compendium**: the PDF, its LaTeX source, the data behind every number and the code that produced it.

## Papers

| No. | Title | Date | PDF | Status |
|---|---|---|---|---|
| 01 | [Weather Forecasting for Renewable Energy: Requirements by Technology, Department and Horizon, with Evidence from Three Global Models over Germany](01-weather-forecasting-for-renewable-energy/) | 2 Nov 2026 | [PDF](01-weather-forecasting-for-renewable-energy/weather-forecasting-for-renewable-energy.pdf) | complete |

## How the papers are organised

- [`STYLE_GUIDE.md`](STYLE_GUIDE.md): the house format (layout, colour palette, figure and table rules, naming, reproducibility rules).
- [`template/`](template/): the shared LaTeX style `ewf-paper.sty` and a starter `main.tex`. Each paper keeps a frozen copy of the style so that later changes never alter a finished paper.
- One folder per paper, `NN-short-title/`, with the same inner structure:

```
NN-short-title/
├── README.md        abstract, key results, how to reproduce
├── <title>.pdf      the paper
├── Makefile         make fetch | make analysis | make paper
├── paper/           LaTeX source (sections, figures, tables, generated numbers, references)
├── code/            numbered pipeline scripts and config
├── data/            raw manifests, interim data, processed figure data, literature facts
└── supplement/      extended material
```

## Building a paper

Requirements: Python 3.11+ with the packages in `code/requirements.txt`, and a TeX Live installation with `latexmk`, `pgfplots` and `natbib`.

```bash
cd research/01-weather-forecasting-for-renewable-energy
```

```bash
make analysis paper
```
