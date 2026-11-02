"""Step 4: forecast skill as a function of lead time, raw and bias-corrected.

Forecasts compared, for 10 m wind speed and 2 m temperature:
  ifs, aifs, gfs       raw model output interpolated to the station
  mmm                  multi-model mean: plain average of the three raw models
  <model>_bc, mmm_bc   the same after a running bias correction: for each model,
                       station and lead time, subtract the mean error of the
                       previous BIAS_WINDOW_DAYS runs whose verifying observation
                       was already available when the run started (no look-ahead)
  persistence          latest observation at the same time of day available at the
                       00 UTC start (00 UTC valid: obs at start; 12 UTC: 12 h before)
  climatology          2020-2024 station mean for the same month and hour (out of sample)

Scores are computed for the runs from EVAL_FIRST_INIT onward (May only spins
up the bias correction). Intervals are 95 % bootstrap intervals resampling
whole runs, which keeps the correlation between stations intact (a block
bootstrap in the sense of Kunsch 1989).

Inputs  : data/interim/verification_pairs.csv.gz
          data/interim/observations_at_valid_times.csv.gz
          data/interim/station_climatology_2020_2024.csv
Outputs : data/interim/verification_wide.csv.gz              all forecasts side by side
          data/processed/fig05_skill_by_lead_<variable>.csv
          data/processed/tab07_day_ahead_summary.csv
          data/processed/combination_check.csv
          paper/tables/tab07-day-ahead-summary.tex          (generated)
          paper/generated/values-04-skill.tex               (generated)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

import config as C
from common import write_tex

VARIABLES = {"wind": ("wind_fc", "wind_obs", "m/s"), "t2m": ("t2m_fc", "t2m_obs", "K")}
RAW = ["ifs", "aifs", "gfs"]
FORECASTS = RAW + ["mmm"] + [f"{m}_bc" for m in RAW] + ["mmm_bc"]
REFERENCES = ["persistence", "climatology"]
LABEL = {"ifs": "ECMWF IFS", "aifs": "ECMWF AIFS", "gfs": "NOAA GFS", "mmm": "Multi-model mean",
         "ifs_bc": "ECMWF IFS, bias-corrected", "aifs_bc": "ECMWF AIFS, bias-corrected",
         "gfs_bc": "NOAA GFS, bias-corrected", "mmm_bc": "Multi-model mean, bias-corrected",
         "persistence": "Persistence", "climatology": "Climatology 2020--2024"}
VNAME = {"wind": "Wind", "t2m": "Temp"}
SNAME = {"ifs": "Ifs", "aifs": "Aifs", "gfs": "Gfs", "mmm": "Mmm", "ifs_bc": "IfsBc", "aifs_bc": "AifsBc",
         "gfs_bc": "GfsBc", "mmm_bc": "MmmBc", "persistence": "Persistence", "climatology": "Climatology"}
STEPNAME = {12: "Twelve", 24: "TwentyFour", 36: "ThirtySix", 60: "Sixty", 108: "FourHalfDay", 228: "NineHalfDay"}


# ------------------------------------------------------------------ data
def load_wide() -> pd.DataFrame:
    p = pd.read_csv(C.INTERIM_DIR / "verification_pairs.csv.gz",
                    parse_dates=["init_time_utc", "valid_time_utc"])
    keys = ["init_time_utc", "step_h", "valid_time_utc", "station_id"]
    wide = p.pivot_table(index=keys, columns="model", values=["wind_fc", "t2m_fc"])
    wide.columns = [f"{v}_{m}" for v, m in wide.columns]
    obs = p.groupby(keys)[["wind_obs", "t2m_obs"]].first()
    df = wide.join(obs).reset_index()
    df["hour"] = df.valid_time_utc.dt.hour
    df["month"] = df.valid_time_utc.dt.month

    # running bias correction, past information only
    for var, (fc, ob, _) in VARIABLES.items():
        for m in RAW:
            col = f"{fc}_{m}"
            df[f"{col}_bc"] = np.nan
            for (sid, step), g in df.groupby(["station_id", "step_h"]):
                err = (g[col] - g[ob]).set_axis(g.init_time_utc)
                days = pd.date_range(err.index.min(), err.index.max(), freq="D")
                err = err.reindex(days)
                lag = max(1, math.ceil(step / 24))
                bias = err.rolling(C.BIAS_WINDOW_DAYS, min_periods=C.BIAS_MIN_SAMPLES).mean().shift(lag)
                df.loc[g.index, f"{col}_bc"] = g[col].to_numpy() - bias.reindex(g.init_time_utc).to_numpy()
        df[f"{fc}_mmm"] = df[[f"{fc}_{m}" for m in RAW]].mean(axis=1, skipna=False)
        df[f"{fc}_mmm_bc"] = df[[f"{fc}_{m}_bc" for m in RAW]].mean(axis=1, skipna=False)

    # references
    clim = pd.read_csv(C.INTERIM_DIR / "station_climatology_2020_2024.csv")
    clim = clim.set_index(["station_id", "month", "hour"])[["wind_mean", "t2m_mean"]]
    clim.columns = ["wind_fc_climatology", "t2m_fc_climatology"]
    df = df.join(clim, on=["station_id", "month", "hour"])
    ov = pd.read_csv(C.INTERIM_DIR / "observations_at_valid_times.csv.gz", parse_dates=["valid_time_utc"])
    df["persist_time"] = df.init_time_utc - pd.to_timedelta(np.where(df.hour == 0, 0, 12), unit="h")
    pers = ov.set_index(["station_id", "valid_time_utc"])[["wind_obs", "t2m_obs"]]
    pers.columns = ["wind_fc_persistence", "t2m_fc_persistence"]
    df = df.join(pers, on=["station_id", "persist_time"]).drop(columns="persist_time")
    return df


# ------------------------------------------------------------------ scores
def bootstrap_rmse(err: pd.Series, runs: pd.Series, rng: np.random.Generator) -> tuple[float, float]:
    """95 % interval of RMSE, resampling whole runs."""
    sq = (err ** 2).groupby(runs).agg(["sum", "count"])
    sums, counts = sq["sum"].to_numpy(), sq["count"].to_numpy()
    idx = rng.integers(0, len(sums), size=(C.BOOTSTRAP_SAMPLES, len(sums)))
    rm = np.sqrt(sums[idx].sum(axis=1) / counts[idx].sum(axis=1))
    return float(np.percentile(rm, 2.5)), float(np.percentile(rm, 97.5))


def diebold_mariano(d: np.ndarray) -> tuple[float, float]:
    """DM statistic of a daily loss differential, Newey-West variance with 2 lags."""
    d = d[~np.isnan(d)]
    n, mean = len(d), d.mean()
    gamma = [np.mean((d[l:] - mean) * (d[:n - l] - mean)) for l in range(3)]
    var = gamma[0] + 2 * sum((1 - l / 3) * gamma[l] for l in (1, 2))
    stat = mean / math.sqrt(var / n)
    return stat, math.erfc(abs(stat) / math.sqrt(2))


def zero_crossing(lead: np.ndarray, skill: np.ndarray) -> float:
    """First lead (days) at which skill falls to zero; inf if it never does."""
    for i in range(1, len(lead)):
        if skill[i - 1] > 0 >= skill[i]:
            return lead[i - 1] + skill[i - 1] / (skill[i - 1] - skill[i]) * (lead[i] - lead[i - 1])
    return math.inf


def main() -> None:
    df = load_wide()
    df.to_csv(C.INTERIM_DIR / "verification_wide.csv.gz", index=False, float_format="%.3f",
              date_format="%Y-%m-%dT%H:%M:%SZ")
    ev = df[df.init_time_utc >= pd.Timestamp(C.EVAL_FIRST_INIT, tz="UTC")]
    rng = np.random.default_rng(C.RANDOM_SEED)
    macros: dict[str, float | str] = {}
    summary_rows = []

    for var, (fc, ob, unit) in VARIABLES.items():
        rows = []
        for step, g in ev.groupby("step_h"):
            row = {"step_h": step, "lead_days": step / 24, "valid_hour_utc": step % 24}
            for src in FORECASTS + REFERENCES:
                e = (g[f"{fc}_{src}"] - g[ob]).dropna()
                row[f"n_{src}"] = len(e)
                row[f"bias_{src}"] = e.mean()
                row[f"mae_{src}"] = e.abs().mean()
                row[f"rmse_{src}"] = math.sqrt((e ** 2).mean())
                if src in FORECASTS:
                    lo, hi = bootstrap_rmse(e, g.loc[e.index, "init_time_utc"], rng)
                    row[f"rmse_lo_{src}"], row[f"rmse_hi_{src}"] = lo, hi
            for src in FORECASTS + ["persistence"]:
                row[f"skill_{src}"] = 1 - row[f"rmse_{src}"] ** 2 / row["rmse_climatology"] ** 2
            rows.append(row)
        out = pd.DataFrame(rows)
        out.round(4).to_csv(C.PROCESSED_DIR / f"fig05_skill_by_lead_{var}.csv", index=False)

        noon = out[out.valid_hour_utc == 12]
        for src in FORECASTS:
            z = zero_crossing(noon.lead_days.to_numpy(), noon[f"skill_{src}"].to_numpy())
            macros[f"{VNAME[var]}{SNAME[src]}SkillZeroDays"] = "more than 9.5" if math.isinf(z) else f"{z:.1f}"
        for step, name in STEPNAME.items():
            r = out[out.step_h == step].iloc[0]
            for src in FORECASTS + REFERENCES:
                macros[f"{VNAME[var]}{SNAME[src]}Rmse{name}"] = f"{r[f'rmse_{src}']:.2f}"
            for src in FORECASTS:
                macros[f"{VNAME[var]}{SNAME[src]}Bias{name}"] = f"{r[f'bias_{src}']:.2f}"

        # day-ahead summary (lead 24-48 h)
        da = ev[ev.step_h.isin(C.DAY_AHEAD_STEPS_H)]
        for src in FORECASTS + REFERENCES:
            e = (da[f"{fc}_{src}"] - da[ob]).dropna()
            rec = {"variable": var, "unit": unit, "forecast": LABEL[src], "key": src, "n": len(e),
                   "bias": e.mean(), "mae": e.abs().mean(), "rmse": math.sqrt((e ** 2).mean())}
            if src in FORECASTS:
                rec["rmse_lo"], rec["rmse_hi"] = bootstrap_rmse(e, da.loc[e.index, "init_time_utc"], rng)
            summary_rows.append(rec)
            macros[f"{VNAME[var]}{SNAME[src]}RmseDayAhead"] = f"{rec['rmse']:.2f}"

        se = {s: ((da[f"{fc}_{s}"] - da[ob]) ** 2).groupby(da.init_time_utc).mean() for s in FORECASTS}
        for a, b in (("aifs", "ifs"), ("gfs", "ifs"), ("mmm", "ifs"), ("mmm", "aifs"), ("mmm_bc", "mmm")):
            stat, p = diebold_mariano((se[a] - se[b]).to_numpy())
            macros[f"{VNAME[var]}Dm{SNAME[a]}vs{SNAME[b]}Stat"] = f"{stat:.1f}"
            macros[f"{VNAME[var]}Dm{SNAME[a]}vs{SNAME[b]}P"] = "< 0.001" if p < 0.001 else f"{p:.2f}"
        raw_best = min(RAW, key=lambda m: float(macros[f"{VNAME[var]}{SNAME[m]}RmseDayAhead"]))
        gain = 1 - float(macros[f"{VNAME[var]}MmmBcRmseDayAhead"]) / float(macros[f"{VNAME[var]}MmmRmseDayAhead"])
        macros[f"{VNAME[var]}BcGainPct"] = f"{100 * gain:.0f}"
        gain_mmm = 1 - float(macros[f"{VNAME[var]}MmmRmseDayAhead"]) / float(macros[f"{VNAME[var]}{SNAME[raw_best]}RmseDayAhead"])
        macros[f"{VNAME[var]}MmmGainPct"] = f"{100 * gain_mmm:.0f}"

    summary = pd.DataFrame(summary_rows)
    summary.round(4).to_csv(C.PROCESSED_DIR / "tab07_day_ahead_summary.csv", index=False)

    # Proposition 4: when does the IFS-AIFS average beat the better of the two?
    comb = []
    for var, (fc, ob, _) in VARIABLES.items():
        for kind, (a, b) in {"raw": ("ifs", "aifs"), "bias_corrected": ("ifs_bc", "aifs_bc")}.items():
            for step, g in ev.groupby("step_h"):
                e = pd.DataFrame({"a": g[f"{fc}_{a}"] - g[ob], "b": g[f"{fc}_{b}"] - g[ob]}).dropna()
                s1, s2 = math.sqrt((e.a ** 2).mean()), math.sqrt((e.b ** 2).mean())
                lo, hi = min(s1, s2), max(s1, s2)
                rho = float((e.a * e.b).mean() / (s1 * s2))
                k = hi / lo
                comb.append({"variable": var, "kind": kind, "step_h": step, "rmse_ifs": s1, "rmse_aifs": s2,
                             "ratio_k": k, "error_correlation": rho, "condition_value": k ** 2 + 2 * rho * k,
                             "condition_holds": k ** 2 + 2 * rho * k < 3,
                             "rmse_mean_predicted": math.sqrt((s1 ** 2 + s2 ** 2 + 2 * rho * s1 * s2) / 4),
                             "rmse_mean_actual": math.sqrt((((e.a + e.b) / 2) ** 2).mean()),
                             "mean_beats_best": math.sqrt((((e.a + e.b) / 2) ** 2).mean()) < lo})
    comb = pd.DataFrame(comb)
    comb.round(4).to_csv(C.PROCESSED_DIR / "combination_check.csv", index=False)
    for var in VARIABLES:
        bc = comb[(comb.variable == var) & (comb.kind == "bias_corrected")]
        macros[f"{VNAME[var]}BcCombFailLeads"] = f"{int((~bc.condition_holds).sum())}"
        raw = comb[(comb.variable == var) & (comb.kind == "raw")].set_index("step_h")
        macros[f"{VNAME[var]}RawErrCorrTwelve"] = f"{raw.at[12, 'error_correlation']:.2f}"
        macros[f"{VNAME[var]}RawErrCorrTenDay"] = f"{raw.at[240, 'error_correlation']:.2f}"
        macros[f"{VNAME[var]}BcMaxRatio"] = f"{bc.ratio_k.max():.2f}"
    macros["NumLeadTimes"] = f"{comb.step_h.nunique()}"
    cw = comb[(comb.variable == "wind") & (comb.kind == "raw") & comb.step_h.isin(C.DAY_AHEAD_STEPS_H)]
    macros["WindIfsAifsErrCorrDayAhead"] = f"{cw.error_correlation.mean():.2f}"
    macros["WindIfsAifsRatioDayAhead"] = f"{cw.ratio_k.mean():.2f}"

    write_table(summary)
    write_macros(macros, df, ev)
    print(summary[["variable", "key", "bias", "mae", "rmse"]].round(3).to_string(index=False))


def write_table(summary: pd.DataFrame) -> None:
    lines = ["% Generated by code/04_skill_by_lead_time.py -- do not edit by hand.",
             "\\begin{tabular}{@{}lrrrrrr@{}}", "\\toprule",
             "& \\multicolumn{3}{c}{10\\,m wind speed (m/s)} & \\multicolumn{3}{c}{2\\,m temperature (K)} \\\\",
             "\\cmidrule(lr){2-4}\\cmidrule(l){5-7}",
             "Forecast & Bias & MAE & RMSE [95\\,\\% CI] & Bias & MAE & RMSE [95\\,\\% CI] \\\\", "\\midrule"]
    order = RAW + ["mmm", "SEP"] + [f"{m}_bc" for m in RAW] + ["mmm_bc", "SEP"] + REFERENCES
    for key in order:
        if key == "SEP":
            lines.append("\\addlinespace")
            continue
        w = summary[(summary.variable == "wind") & (summary.key == key)].iloc[0]
        t = summary[(summary.variable == "t2m") & (summary.key == key)].iloc[0]

        def n(x: float) -> str:
            return f"${x:.2f}$"

        def rm(r):
            if pd.notna(r.get("rmse_lo", np.nan)):
                return f"{r.rmse:.2f} [{r.rmse_lo:.2f}, {r.rmse_hi:.2f}]"
            return f"{r.rmse:.2f}"
        name = LABEL[key].replace(", bias-corrected", " (BC)")
        row = f"{name} & {n(w.bias)} & {w.mae:.2f} & {rm(w)} & {n(t.bias)} & {t.mae:.2f} & {rm(t)} \\\\"
        if key == "mmm_bc":
            row = row.replace(name, f"\\textbf{{{name}}}")
        lines.append(row)
    lines += ["\\bottomrule", "\\end{tabular}"]
    (C.PAPER_DIR / "paper" / "tables" / "tab07-day-ahead-summary.tex").write_text("\n".join(lines) + "\n")


def write_macros(macros: dict, df: pd.DataFrame, ev: pd.DataFrame) -> None:
    lines = ["% Generated by code/04_skill_by_lead_time.py -- do not edit by hand."]
    for k, v in macros.items():
        lines.append(f"\\newcommand{{\\val{k}}}{{{v}}}")
    obs_ok = ev.dropna(subset=["wind_obs"])
    lines += [f"\\newcommand{{\\valNumStations}}{{{df.station_id.nunique()}}}",
              f"\\newcommand{{\\valNumRuns}}{{{df.init_time_utc.nunique()}}}",
              f"\\newcommand{{\\valNumEvalRuns}}{{{ev.init_time_utc.nunique()}}}",
              f"\\newcommand{{\\valNumEvalPairs}}{{{len(obs_ok) * 3:,}}}",
              f"\\newcommand{{\\valMeanWindObs}}{{{obs_ok.wind_obs.mean():.1f}}}"]
    write_tex(C.GENERATED_TEX_DIR / "values-04-skill.tex", lines)


if __name__ == "__main__":
    main()
