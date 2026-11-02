# Paper 01: Weather Forecasting for Renewable Energy
#
#   make            analysis + paper (uses the data already in data/interim)
#   make fetch      download observations and forecasts again (about 12 GB is read,
#                   a few MB are kept; takes 20-30 minutes)
#   make analysis   rebuild every table, figure CSV and number from data/interim
#   make paper      build the PDF and copy it to the folder root
#   make clean      remove LaTeX build files

PY  ?= python3
PDF := weather-forecasting-for-renewable-energy.pdf

.PHONY: all fetch analysis paper clean

all: analysis paper

fetch:
	cd code && $(PY) 01_fetch_station_observations.py
	cd code && $(PY) 02_fetch_model_forecasts.py

analysis:
	cd code && $(PY) 03_build_verification_pairs.py
	cd code && $(PY) 04_skill_by_lead_time.py
	cd code && $(PY) 05_spatial_aggregation.py
	cd code && $(PY) 06_wind_power_and_bidding.py
	cd code && $(PY) 07_pv_clear_sky_chain.py

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	cp paper/main.pdf $(PDF)

clean:
	cd paper && latexmk -C
