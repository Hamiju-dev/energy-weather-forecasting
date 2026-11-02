# 10. Visualising weather and energy forecasts

The right chart depends on who is looking and what decision they make. Uncertainty should be visible almost everywhere.

## General rules

- **Show uncertainty**: fan charts (P10-P90 band around the median) instead of single lines.
- **Show the timeline honestly**: label time zone (and convert to local time for operators), mark "now", mark gate closures (12:00 CET DA, IDA times).
- **Forecast vs actual** always in the same consistent colours across all dashboards.
- **Mark data problems**: gaps, curtailment, outages, stale forecasts (greyed out or hatched).
- **Normalise** when comparing plants (kWh/kWp, capacity factor, % of capacity).
- **Small multiples** (a grid of small identical charts) for many parks instead of one chart with 40 lines.
- Use colour-blind-safe palettes; sequential palettes for magnitude, diverging for anomalies/errors.

## Chart catalogue by purpose

### Forecast display (trading, operations)
| Chart | What it shows |
|---|---|
| **Fan chart** | Median forecast with shaded quantile bands (P10-P90, P25-P75) plus actuals as they come in |
| **Run-to-run comparison** | Latest forecast vs previous run(s), plus a "delta" bar chart; the core view for traders |
| **Ensemble plume / spaghetti** | Every ensemble member as a thin line; shows spread and bimodality (e.g. "front arrives Tuesday or Wednesday") |
| **Meteogram** | Stacked panels of irradiance, cloud, temperature, wind, gusts, precipitation for a site over 7-10 days, with threshold lines (crane limits, stow limits) |
| **Multi-model comparison** | ICON vs ECMWF vs GFS vs AIFS lines; disagreement is a risk signal |
| **Residual load + price forecast** | Load, wind, solar stacked area with residual load line and price on a second axis |
| **15-min heatmap** | Days × quarter-hours, colour = forecast power or price; spots negative-price risk at a glance |

### Maps
| Chart | Use |
|---|---|
| Irradiance / cloud / wind field maps with park locations | Situational awareness, front passages |
| Satellite loop with park markers | Nowcasting, explaining a bad hour |
| Warning maps (DWD warnings, hail, storms) | Operations, HSE |
| Resource maps (GHI, mean wind) | Development |
| Error maps per park | Spot regional NWP problems or broken sites |

### Performance and losses (asset management)
| Chart | Use |
|---|---|
| **Expected vs actual** time series | Detecting underperformance |
| **Scatter: power vs POA irradiance** (PV) | Clipping, shading, string failures, temperature effects show as patterns |
| **Power curve scatter** (wind), coloured by density or turbulence | Curve deviations, curtailment, icing, yaw/pitch problems |
| **Carpet plot / heatmap** (day of year × time of day) | Recurring shading, outages, curtailment patterns, sensor faults |
| **Loss waterfall** (PVsyst-style) | Theoretical energy → losses by cause → metered energy |
| **Monthly actual vs budget** with P50/P90 band | Budget tracking |
| **Cumulative yield vs budget** (S-curve) | Year-end outlook |
| **Availability and lost-energy bars** by cause | Prioritising O&M |
| **Open-fault ranking** by forecast EUR loss until repair | Field team dispatch |

### Resource and development
| Chart | Use |
|---|---|
| Wind rose (speed by direction) | Layout, wakes |
| Weibull histogram with fitted curve | AEP |
| 12 × 24 matrix (month × hour) | Diurnal/seasonal profile, PPA shape |
| Interannual variability bars | Risk |
| Exceedance (P-value) curve | Financing |
| Duration curve | Grid and BESS sizing |

### Construction and commissioning
| Chart | Use |
|---|---|
| Weather-window calendar (Gantt with workable/unworkable shading) | Daily planning |
| Monthly workability probability bars from hindcast | Schedule contingency |
| Gust meteogram vs lift limits | Go/no-go for lifts |
| Clear-sky vs forecast irradiance for test days | Capacity test planning |

### Forecast evaluation (data science)
| Chart | Use |
|---|---|
| Error vs lead time (MAE/RMSE/CRPS) per model | Where each model wins |
| Skill score vs baseline over lead time | Real improvement |
| Error by hour of day and month (heatmap) | Systematic biases |
| Reliability diagram, PIT histogram, rank histogram | Probabilistic calibration |
| Forecast vs observed scatter / 2D density | Bias, saturation, clipping |
| Error distribution histogram | Tails |
| Taylor diagram | Compare many models at once (correlation, variance, RMSE) |
| Worst-days gallery | Learn from the biggest misses |

### Market analysis
| Chart | Use |
|---|---|
| Price vs residual load scatter | Visualises the merit order |
| Negative-price hours by month/year | Exposure trend |
| Capture rate over time | Cannibalisation |
| Solar infeed vs price heatmap | Price-shape risk |
| Price duration curve | BESS and peaker value |

## Tools

| Need | Tools |
|---|---|
| Static/scientific plots | matplotlib, seaborn, `earthkit-plots`, cartopy for maps, MetPy for meteorology |
| Interactive charts | Plotly, Altair, Bokeh, hvPlot/HoloViews, Datashader for millions of points |
| Maps | folium/Leaflet, pydeck, kepler.gl, xarray + cartopy |
| Dashboards (Python) | Streamlit (fastest to build), Plotly Dash, Panel |
| Ops dashboards on time-series DBs | Grafana with TimescaleDB/InfluxDB/PostgreSQL |
| Business reporting | Power BI, Apache Superset, Metabase |
| Intuition / sanity checks | Windy, Ventusky, meteoblue (compare models visually) |
