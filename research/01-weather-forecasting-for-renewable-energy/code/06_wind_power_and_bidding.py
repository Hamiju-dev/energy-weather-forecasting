"""Step 6: from wind-speed error to power error and to the optimal bid.

Part A, power-curve amplification (Proposition 1). Observed and forecast 10 m
wind speeds are scaled to a pseudo hub height with a neutral power law
(alpha = 1/7) and passed through the power curve of a common onshore turbine
(Vestas V126/3450 from the OEDB turbine library bundled with windpowerlib).
Applying the *same* transformation to forecast and observation isolates how
the curve amplifies relative errors. The resulting "pseudo power" is not the
output of any real wind farm.

Part B, bidding under asymmetric imbalance costs (Proposition 3). Day-ahead
pseudo-power forecasts from the bias-corrected multi-model mean are turned
into quantile forecasts with conditional empirical quantiles: the June runs
(training) give, for each class of forecast power (config.BID_FORECAST_BINS),
the tau-quantile of the observed pseudo power; the July runs (test) are bid
at that quantile and scored with a cost of BID_COST_SHORT per unit of
shortfall and BID_COST_LONG per unit of surplus.

Inputs  : data/interim/verification_wide.csv.gz, windpowerlib bundled OEDB data
Outputs : data/raw/turbine-power-curves/oedb_power_curves_windpowerlib-0.2.2.csv
          data/processed/fig07a_power_curve.csv
          data/processed/fig07b_partial_load_elasticity.csv
          data/processed/power_error_by_lead.csv
          data/processed/fig07c_bid_cost_vs_quantile.csv
          paper/generated/values-06-power.tex
"""

from __future__ import annotations

import os
import shutil

import numpy as np
import pandas as pd
import windpowerlib

import config as C
from common import write_tex


def power_curve() -> tuple[np.ndarray, np.ndarray, float]:
    src = os.path.join(os.path.dirname(windpowerlib.__file__), "oedb", "power_curves.csv")
    dst = C.POWER_CURVE_RAW_DIR / f"oedb_power_curves_windpowerlib-{windpowerlib.__version__}.csv"
    C.POWER_CURVE_RAW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    df = pd.read_csv(dst)
    row = df[df.turbine_type == C.TURBINE_TYPE].iloc[0]
    v = np.array([float(c) for c in df.columns[1:]])
    p = row.iloc[1:].astype(float).to_numpy()
    ok = ~np.isnan(p)
    v, p = v[ok], p[ok]
    rated = p.max()
    return v, p, rated


def to_power(v10: np.ndarray, v_curve, p_curve, rated) -> np.ndarray:
    v_hub = v10 * (C.HUB_HEIGHT_M / 10.0) ** C.SHEAR_EXPONENT
    return np.interp(v_hub, v_curve, p_curve, left=0.0, right=0.0) / rated


def main() -> None:
    v_curve, p_curve, rated = power_curve()
    pd.DataFrame({"wind_speed_hub_ms": v_curve, "power_w": p_curve,
                  "power_normalised": p_curve / rated}).to_csv(
        C.PROCESSED_DIR / "fig07a_power_curve.csv", index=False)

    w = pd.read_csv(C.INTERIM_DIR / "verification_wide.csv.gz", parse_dates=["init_time_utc"])
    w = w[w.init_time_utc >= pd.Timestamp(C.EVAL_FIRST_INIT, tz="UTC")]
    frames = []
    for model in ["ifs", "aifs", "gfs", "mmm", "mmm_bc"]:
        f = w[["init_time_utc", "step_h", "station_id", f"wind_fc_{model}", "wind_obs"]].dropna()
        frames.append(f.rename(columns={f"wind_fc_{model}": "wind_fc"}).assign(model=model))
    allm = pd.concat(frames, ignore_index=True)
    allm["p_fc"] = to_power(allm.wind_fc.to_numpy(), v_curve, p_curve, rated)
    allm["p_obs"] = to_power(allm.wind_obs.to_numpy(), v_curve, p_curve, rated)

    rows = []
    for (model, step), g in allm.groupby(["model", "step_h"]):
        rel_wind = (g.wind_fc - g.wind_obs).abs().mean() / g.wind_obs.mean()
        rel_power = (g.p_fc - g.p_obs).abs().mean() / g.p_obs.mean()
        rows.append({"model": model, "step_h": step, "lead_days": step / 24,
                     "wind_mae_ms": (g.wind_fc - g.wind_obs).abs().mean(),
                     "power_mae_pct_capacity": 100 * (g.p_fc - g.p_obs).abs().mean(),
                     "power_rmse_pct_capacity": 100 * np.sqrt(((g.p_fc - g.p_obs) ** 2).mean()),
                     "relative_wind_error": rel_wind, "relative_power_error": rel_power,
                     "amplification": rel_power / rel_wind,
                     "mean_capacity_factor_obs": g.p_obs.mean()})
    perr = pd.DataFrame(rows)
    perr.round(4).to_csv(C.PROCESSED_DIR / "power_error_by_lead.csv", index=False)

    # Proposition 1 locally: log-elasticity for pairs where forecast and observation are at partial load
    k = (C.HUB_HEIGHT_M / 10.0) ** C.SHEAR_EXPONENT
    v_ci = v_curve[np.argmax(p_curve > 0)]
    v_r = v_curve[np.argmax(p_curve >= rated)]
    da_all = allm[(allm.model == "mmm_bc") & allm.step_h.isin(C.DAY_AHEAD_STEPS_H)]
    vf, vo = da_all.wind_fc * k, da_all.wind_obs * k
    pl = da_all[(vf > v_ci + 0.5) & (vo > v_ci + 0.5) & (vf < v_r) & (vo < v_r)
                & (np.abs(np.log(vf / vo.where(vo > 0))) > 0.02)]
    elast = (np.log(pl.p_fc / pl.p_obs) / np.log(pl.wind_fc / pl.wind_obs)).rename("elasticity")
    hist_edges = np.arange(2.5, 5.01, 0.1)
    counts, _ = np.histogram(elast.clip(hist_edges[0], hist_edges[-1] - 1e-9), bins=hist_edges)
    pd.DataFrame({"elasticity_bin_low": hist_edges[:-1].round(2), "elasticity_bin_high": hist_edges[1:].round(2),
                  "elasticity_bin_mid": (hist_edges[:-1] + 0.05).round(3),
                  "share_of_pairs": (counts / counts.sum()).round(5), "pairs": counts}).to_csv(
        C.PROCESSED_DIR / "fig07b_partial_load_elasticity.csv", index=False)

    # ---------------- Part B: bidding
    da = allm[(allm.model == "mmm_bc") & allm.step_h.isin(C.DAY_AHEAD_STEPS_H)].copy()
    da["err"] = da.p_obs - da.p_fc
    train = da[da.init_time_utc <= pd.Timestamp(C.BID_TRAIN_LAST_INIT, tz="UTC")]
    test = da[da.init_time_utc > pd.Timestamp(C.BID_TRAIN_LAST_INIT, tz="UTC")]

    def cost(bid, obs, c_short, c_long):
        return np.mean(c_short * np.maximum(bid - obs, 0) + c_long * np.maximum(obs - bid, 0))

    taus = np.round(np.arange(0.05, 0.951, 0.025), 3)
    train = train.assign(cls=pd.cut(train.p_fc, C.BID_FORECAST_BINS))
    test = test.assign(cls=pd.cut(test.p_fc, C.BID_FORECAST_BINS))
    out = []
    for tau in taus:
        q = train.groupby("cls", observed=False).p_obs.quantile(tau)
        bid = test.cls.map(q).astype(float).to_numpy()
        out.append({"tau": tau,
                    "cost_asymmetric": cost(bid, test.p_obs, C.BID_COST_SHORT, C.BID_COST_LONG),
                    "cost_symmetric": cost(bid, test.p_obs, 1.0, 1.0),
                    "share_below_bid": float(np.mean(test.p_obs.to_numpy() <= bid))})
    bc = pd.DataFrame(out)
    point_asym = cost(test.p_fc, test.p_obs, C.BID_COST_SHORT, C.BID_COST_LONG)
    point_sym = cost(test.p_fc, test.p_obs, 1.0, 1.0)
    bc["cost_asymmetric_point_forecast"] = point_asym
    bc["cost_symmetric_point_forecast"] = point_sym
    bc.round(5).to_csv(C.PROCESSED_DIR / "fig07c_bid_cost_vs_quantile.csv", index=False)

    tau_star = C.BID_COST_LONG / (C.BID_COST_LONG + C.BID_COST_SHORT)
    best = bc.loc[bc.cost_asymmetric.idxmin()]
    at_star = bc.loc[(bc.tau - tau_star).abs().idxmin()]
    da_rows = perr[(perr.model == "mmm_bc") & perr.step_h.isin(C.DAY_AHEAD_STEPS_H)]
    lines = ["% Generated by code/06_wind_power_and_bidding.py -- do not edit by hand.",
             f"\\newcommand{{\\valTurbine}}{{{C.TURBINE_TYPE}}}",
             f"\\newcommand{{\\valRatedKw}}{{{rated / 1000:,.0f}}}",
             f"\\newcommand{{\\valElasticityMedian}}{{{elast.median():.2f}}}",
             f"\\newcommand{{\\valElasticityQOne}}{{{elast.quantile(0.25):.2f}}}",
             f"\\newcommand{{\\valElasticityQThree}}{{{elast.quantile(0.75):.2f}}}",
             f"\\newcommand{{\\valElasticityN}}{{{len(elast):,}}}",
             f"\\newcommand{{\\valElasticityShareAboveThree}}{{{100 * (elast >= 3).mean():.0f}}}",
             f"\\newcommand{{\\valAmplificationDA}}{{{da_rows.amplification.mean():.1f}}}",
             f"\\newcommand{{\\valRelWindErrDA}}{{{100 * da_rows.relative_wind_error.mean():.0f}}}",
             f"\\newcommand{{\\valRelPowerErrDA}}{{{100 * da_rows.relative_power_error.mean():.0f}}}",
             f"\\newcommand{{\\valPowerMaeDA}}{{{da_rows.power_mae_pct_capacity.mean():.1f}}}",
             f"\\newcommand{{\\valCapFactorObs}}{{{100 * da_rows.mean_capacity_factor_obs.mean():.0f}}}",
             f"\\newcommand{{\\valTauStar}}{{{tau_star:.2f}}}",
             f"\\newcommand{{\\valTauBest}}{{{best.tau:.3f}}}",
             f"\\newcommand{{\\valCostBest}}{{{best.cost_asymmetric:.4f}}}",
             f"\\newcommand{{\\valCostStarAboveBestPct}}{{{100 * (at_star.cost_asymmetric / best.cost_asymmetric - 1):.1f}}}",
             f"\\newcommand{{\\valCostAtStar}}{{{at_star.cost_asymmetric:.4f}}}",
             f"\\newcommand{{\\valCostPoint}}{{{point_asym:.4f}}}",
             f"\\newcommand{{\\valCostSavingPct}}{{{100 * (1 - at_star.cost_asymmetric / point_asym):.0f}}}",
             f"\\newcommand{{\\valBidTrainN}}{{{len(train):,}}}",
             f"\\newcommand{{\\valBidTestN}}{{{len(test):,}}}",
             f"\\newcommand{{\\valAmplificationMin}}{{{perr.amplification.min():.1f}}}",
             f"\\newcommand{{\\valAmplificationMax}}{{{perr.amplification.max():.1f}}}",
             f"\\newcommand{{\\valCostSymAtMedian}}{{{bc.loc[(bc.tau - 0.5).abs().idxmin()].cost_symmetric:.4f}}}",
             f"\\newcommand{{\\valCostSymPoint}}{{{point_sym:.4f}}}"]
    write_tex(C.GENERATED_TEX_DIR / "values-06-power.tex", lines)
    print(perr[perr.step_h.isin([12, 36, 120, 240])])
    print(bc.loc[[bc.cost_asymmetric.idxmin()]], point_asym)


if __name__ == "__main__":
    main()
