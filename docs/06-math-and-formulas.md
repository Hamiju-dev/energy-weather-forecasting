# 6. The mathematics: formulas you actually need

Organised from sky to money. You rarely implement these by hand (pvlib, windpowerlib, PyWake and scoring libraries do it), but you need to know what they do to debug forecasts.

Notation: angles in degrees unless stated; $G$ = irradiance in W/m²; $T$ = temperature; $v$ = wind speed in m/s; $\rho$ = air density in kg/m³.

---

## A. Solar geometry

Day of year $n$ (1 to 365).

**Solar declination** (Cooper approximation; use the NREL SPA algorithm in production, e.g. `pvlib.solarposition`):

$$\delta = 23.45^\circ \sin\!\left(\frac{360^\circ (284 + n)}{365}\right)$$

**Hour angle** (solar time $t_s$ in hours; 15° per hour, zero at solar noon):

$$\omega = 15^\circ (t_s - 12)$$

Solar time differs from clock time by the longitude offset from the time-zone meridian (4 min per degree) and the equation of time (up to ±16 min).

**Solar zenith angle** $\theta_z$ at latitude $\varphi$:

$$\cos\theta_z = \sin\varphi \sin\delta + \cos\varphi \cos\delta \cos\omega$$

**Extraterrestrial irradiance** (normal to the sun), with solar constant $G_{sc} \approx 1361$ W/m²:

$$G_{0n} = G_{sc}\left(1 + 0.033\cos\frac{360^\circ n}{365}\right), \qquad G_0 = G_{0n}\cos\theta_z$$

**Air mass** (Kasten-Young, $\theta_z$ in degrees):

$$AM = \frac{1}{\cos\theta_z + 0.50572\,(96.07995 - \theta_z)^{-1.6364}}$$

**Angle of incidence** on a surface with tilt $\beta$ and azimuth $\gamma$ (sun azimuth $\gamma_s$):

$$\cos\theta = \cos\theta_z\cos\beta + \sin\theta_z\sin\beta\cos(\gamma_s - \gamma)$$

## B. Irradiance components and clear sky

**Closure equation** (horizontal):

$$GHI = DNI \cos\theta_z + DHI$$

**Clearness index** and **clear-sky index**:

$$k_t = \frac{GHI}{G_{0n}\cos\theta_z}, \qquad k_c = \frac{GHI}{GHI_{\text{clear}}}$$

$k_c$ is the most useful normalisation in solar forecasting: it removes the deterministic daily and seasonal cycle, leaving only the "weather" part. Forecast $k_c$, then multiply back.

**Clear-sky models**: Haurwitz (simplest),

$$GHI_{\text{clear}} = 1098\,\cos\theta_z\,\exp\!\left(\frac{-0.057}{\cos\theta_z}\right)$$

Ineichen-Perez (uses Linke turbidity, the pvlib default), REST2 and McClear (CAMS, use aerosols). Use a model with real aerosol input when dust matters.

**Decomposition** (GHI to diffuse fraction $k_d = DHI/GHI$). Erbs et al. (1982):

$$k_d = \begin{cases} 1 - 0.09\,k_t & k_t \le 0.22 \\ 0.9511 - 0.1604\,k_t + 4.388\,k_t^2 - 16.638\,k_t^3 + 12.336\,k_t^4 & 0.22 < k_t \le 0.80 \\ 0.165 & k_t > 0.80 \end{cases}$$

Better modern options: DIRINT, Engerer2, Yang's models (all in pvlib or the literature).

## C. Plane-of-array (POA) irradiance

$$G_{POA} = G_{b} + G_{d} + G_{r}$$

Beam: $G_b = DNI \cdot \max(0, \cos\theta)$

Ground-reflected, with albedo $\rho_g$: $G_r = GHI \cdot \rho_g \cdot \dfrac{1 - \cos\beta}{2}$

Sky diffuse, isotropic model: $G_d = DHI \cdot \dfrac{1 + \cos\beta}{2}$

The **Perez model** (anisotropic, with circumsolar and horizon brightening) is the industry standard; Hay-Davies is a simpler anisotropic option. Transposition is a significant error source when DNI/DHI come from decomposition.

**Incidence angle modifier** (reflection losses), ASHRAE form with $b_0 \approx 0.05$:

$$IAM(\theta) = 1 - b_0\left(\frac{1}{\cos\theta} - 1\right)$$

**Bifacial**: $G_{\text{eff}} = G_{\text{front}} + \varphi_{bi}\, G_{\text{rear}}$, bifaciality $\varphi_{bi}$ ≈ 0.7 to 0.9 depending on cell technology.

## D. Module temperature

NOCT model:

$$T_c = T_a + \frac{NOCT - 20}{800}\, G_{POA}$$

Faiman model (pvlib defaults $U_0 = 25$ W/m²K, $U_1 = 6.84$ W·s/m³K):

$$T_c = T_a + \frac{G_{POA}}{U_0 + U_1 \, v_{\text{wind}}}$$

Sandia (SAPM) model: $T_m = G_{POA}\, e^{a + b\, v} + T_a$, $\;T_c = T_m + \dfrac{G_{POA}}{1000}\Delta T$.

## E. PV power

**PVWatts-style DC power** (temperature coefficient $\gamma \approx -0.003$ to $-0.004$ per K for modern c-Si):

$$P_{DC} = P_{DC,0}\,\frac{G_{POA,\text{eff}}}{1000}\,\big[1 + \gamma\,(T_c - 25)\big]$$

**AC power with inverter efficiency and clipping:**

$$P_{AC} = \min\big(\eta_{inv}(P_{DC})\cdot P_{DC},\; P_{AC,\max}\big)$$

then subtract losses: soiling, snow, mismatch, wiring, transformer, availability, export limit.

**Worked example.** 10 MWp plant, $G_{POA}$ = 800 W/m², $T_c$ = 45 °C, $\gamma$ = -0.35 %/K:
$P_{DC}$ = 10 × 0.8 × (1 - 0.0035 × 20) = 7.44 MW. With 12 % other losses: ~6.5 MW AC.

More detailed: single-diode models (De Soto / CEC), Sandia array performance model, spectral corrections, snow (Marion model), soiling (Kimber, HSU model using PM2.5/PM10 and rain), degradation (~0.3 to 0.7 %/year).

## F. Wind power

**Power in the wind and turbine power** (rotor area $A = \pi D^2/4$):

$$P = \tfrac{1}{2}\,\rho\,A\,v^3\,C_p, \qquad C_{p,\max} = \frac{16}{27} \approx 0.593 \;\text{(Betz limit)}$$

**Worked example.** Rotor 150 m (A = 17,671 m²), ρ = 1.225, v = 8 m/s: wind power = 0.5 × 1.225 × 17,671 × 512 ≈ 5.54 MW; with $C_p$ = 0.45 the turbine makes ≈ 2.5 MW.

Because of $v^3$, a 10 % wind speed error gives about 33 % power error ($1.1^3 = 1.331$) in the steep part of the power curve, and almost none above rated speed.

**Air density** from pressure $p$ (Pa) and temperature $T$ (K), $R_d$ = 287.05 J/(kg·K) (use virtual temperature for humidity):

$$\rho = \frac{p}{R_d\, T}$$

**Density normalisation of wind speed** (IEC 61400-12-1, pitch-regulated turbines; $\rho_0$ = reference density of the power curve):

$$v_n = v\left(\frac{\rho}{\rho_0}\right)^{1/3}$$

**Vertical extrapolation (shear).** Power law with shear exponent $\alpha$ (≈ 0.1 to 0.14 offshore/neutral, 0.2 to 0.4 over forests or on stable nights):

$$v(z) = v(z_r)\left(\frac{z}{z_r}\right)^{\alpha}$$

Log law with roughness length $z_0$, friction velocity $u_*$, von Kármán constant $\kappa$ = 0.4 and stability correction $\psi_m(z/L)$ (Monin-Obukhov length $L$):

$$v(z) = \frac{u_*}{\kappa}\left[\ln\frac{z}{z_0} - \psi_m\!\left(\frac{z}{L}\right)\right]$$

**Turbulence intensity:** $TI = \sigma_v / \bar{v}$.

**Wind speed distribution (Weibull)** with scale $c$ and shape $k$ (k = 2 is the Rayleigh case):

$$f(v) = \frac{k}{c}\left(\frac{v}{c}\right)^{k-1} e^{-(v/c)^k}, \qquad F(v) = 1 - e^{-(v/c)^k}, \qquad \bar{v} = c\,\Gamma\!\left(1 + \tfrac{1}{k}\right)$$

Mean wind power density: $\overline{WPD} = \tfrac{1}{2}\rho\, c^3\, \Gamma(1 + 3/k)$.

**Annual energy production:**

$$AEP = 8760 \int_0^\infty P(v)\, f(v)\, dv \;\times\; (1 - \text{losses})$$

**Power curve fit** (smooth logistic approximation, useful for ML features):

$$P(v) = \frac{P_{\text{rated}}}{1 + e^{-k(v - v_0)}}$$

**Wake deficit, Jensen/Park model** (thrust coefficient $C_T$, distance $x$, rotor diameter $D$, wake decay $k_w$ ≈ 0.075 onshore, 0.04 to 0.05 offshore):

$$\frac{v_{\text{wake}}}{v_\infty} = 1 - \frac{1 - \sqrt{1 - C_T}}{\left(1 + 2 k_w x / D\right)^2}$$

Modern alternatives: Bastankhah-Porté-Agel Gaussian wakes, TurbOPark (in PyWake/FLORIS).

**Ice accretion** (Makkonen): $dM/dt = \alpha_1\alpha_2\alpha_3\, w\, v\, A$ with liquid water content $w$ and collision, sticking and accretion efficiencies $\alpha_i$.

**Extreme wind:** fit annual maxima with a Gumbel distribution to get the 50-year return value $V_{50}$.

## G. Hydro, load and grid

**Hydropower:**

$$P = \eta\,\rho_w\, g\, Q\, H$$

Example: Q = 100 m³/s, H = 50 m, η = 0.9 gives 0.9 × 1000 × 9.81 × 100 × 50 ≈ 44 MW.

**Catchment water balance:** $dS/dt = P_{\text{precip}} - ET - Q$.
**Degree-day snowmelt:** $M = DDF \cdot \max(0, T - T_0)$.

**Heating and cooling degree days** (base often 18 °C / 65 °F; Germany uses 20/15 for *Gradtagzahlen*, UK often 15.5 °C):

$$HDD = \sum_{\text{days}} \max(0, T_{\text{base}} - \bar{T}), \qquad CDD = \sum_{\text{days}} \max(0, \bar{T} - T_{\text{base}})$$

**Dynamic line rating** (IEEE 738 / CIGRE TB 601), steady-state heat balance of a conductor:

$$q_{\text{convective}}(v, T_a) + q_{\text{radiative}} = q_{\text{solar}} + I^2 R(T_c)$$

Solve for the current $I$ that keeps conductor temperature $T_c$ at its limit.

## H. Forecasting baselines and statistical models

**Persistence:** $\hat{y}_{t+h} = y_t$.

**Smart persistence** (solar; persists the clear-sky index instead of power):

$$\hat{P}_{t+h} = k_{c,t}\cdot P_{\text{clear},\,t+h}$$

**Climatology:** average for that time of day and season.

**Model Output Statistics (MOS):** linear regression from NWP outputs to the target, $\hat{y} = a + \sum_i b_i x_i$, trained per site and lead time.

**Kalman filter bias correction** (recursive, adapts to slow drifts):

$$\hat{b}_t = \hat{b}_{t-1} + K_t\,(e_t - \hat{b}_{t-1})$$

**Forecast combination:** $\hat{y} = \sum_i w_i \hat{y}_i$, with weights from inverse error variance or a stacking regression.

**Quantile regression** for quantile level $\tau$: minimise the pinball loss (below) instead of squared error. Works with linear models, gradient boosting (LightGBM `objective="quantile"`) or neural nets.

**EMOS / NGR** (ensemble model output statistics) for an ensemble with mean $\bar{x}$ and variance $s^2$, parameters fitted by minimising CRPS:

$$Y \mid X \sim \mathcal{N}\big(a + b\,\bar{x},\; c + d\, s^2\big)$$

(For bounded variables like power use truncated or censored distributions.)

**Split conformal prediction** (distribution-free intervals): using calibration residuals, the interval is $\hat{y} \pm q_{1-\alpha}(|r|)$; adaptive variants exist for time series.

**Geographic smoothing:** for $N$ sites with equal error variance $\sigma^2$ and average error correlation $\bar{r}$, the relative error of the sum scales as

$$\frac{\sigma_{\Sigma}}{N\sigma} = \sqrt{\frac{1 + (N-1)\,\bar{r}}{N}}$$

which is why portfolio forecasts are much more accurate than single-site ones, but never better than $\sqrt{\bar{r}}$.

## I. Error metrics

With forecast $\hat{y}_t$, observation $y_t$, error $e_t = \hat{y}_t - y_t$, $N$ samples, capacity $C$:

| Metric | Formula | Notes |
|---|---|---|
| Bias (MBE) | $\frac{1}{N}\sum e_t$ | Systematic over/under-forecast |
| MAE | $\frac{1}{N}\sum \lvert e_t\rvert$ | Optimised by the median; linked to imbalance volume |
| RMSE | $\sqrt{\frac{1}{N}\sum e_t^2}$ | Optimised by the mean; punishes big misses |
| nMAE, nRMSE | MAE/C, RMSE/C | **Always state the normaliser** (capacity, mean, daytime only?) |
| MAPE | avoid | Explodes near zero (night, calm) |
| Skill score | $SS = 1 - \dfrac{RMSE_{\text{model}}}{RMSE_{\text{reference}}}$ | Reference: persistence, smart persistence, climatology, or a simple NWP model |

Decomposition: $RMSE^2 = \text{bias}^2 + \sigma_e^2$ (systematic vs random part).

**Probabilistic metrics:**

Pinball (quantile) loss for quantile $q$ at level $\tau$:

$$L_\tau(y, q) = \begin{cases} \tau\,(y - q) & y \ge q \\ (1 - \tau)\,(q - y) & y < q \end{cases}$$

Continuous Ranked Probability Score, for predictive CDF $F$ (generalises MAE to distributions; lower is better):

$$CRPS(F, y) = \int_{-\infty}^{\infty}\big(F(x) - \mathbf{1}\{x \ge y\}\big)^2\, dx$$

For an ensemble of $M$ members $x_i$:

$$CRPS = \frac{1}{M}\sum_i \lvert x_i - y\rvert - \frac{1}{2M^2}\sum_i\sum_j \lvert x_i - x_j\rvert$$

Brier score for a binary event (e.g. "ramp > 30 % within 1 h", "negative price"): $BS = \frac{1}{N}\sum (p_t - o_t)^2$.

Also check **reliability** (PIT histograms, rank histograms, reliability diagrams), **sharpness** (average interval width) and **coverage** (share of observations inside the stated interval). Use the **Diebold-Mariano test** to check that one model is significantly better than another.

## J. Decision maths: the optimal bid

If over-forecasting (being short) costs $c_s$ per MWh and under-forecasting (being long) costs $c_l$ per MWh, the expected-cost-minimising bid is the quantile

$$q^* = F^{-1}\!\left(\frac{c_l}{c_l + c_s}\right)$$

(the classic "newsvendor" result). If shortfalls are three times as expensive as surpluses, bid the 25 % quantile, not the median. This is the strongest argument for probabilistic forecasts.

## K. Yield assessment and performance

**P-values** (normal approximation; $z_{90}$ = 1.282, $z_{75}$ = 0.674, $z_{99}$ = 2.326):

$$P_X = P_{50}\,(1 - z_X\,\sigma_{\text{total}})$$

Independent uncertainties combine as $\sigma_{\text{total}} = \sqrt{\sum_i \sigma_i^2}$; for an N-year average, the interannual part shrinks: $\sigma_{\text{IAV},N} = \sigma_{\text{IAV}}/\sqrt{N}$.

Example: P50 = 10 GWh, $\sigma_{\text{total}}$ = 8 % gives P90 (1 year) = 10 × (1 - 1.282 × 0.08) ≈ 8.97 GWh.

**Performance Ratio** (IEC 61724-1):

$$PR = \frac{E_{AC} / P_{STC}}{H_{POA} / G_{STC}}, \qquad G_{STC} = 1000\ \text{W/m}^2$$

**Temperature-corrected PR** (NREL weather-corrected PR, $\gamma$ negative, $\overline{T}_c$ = annual mean cell temperature):

$$PR_{\text{corr}} = \frac{\sum_t E_{AC,t}}{\sum_t P_{STC}\,\frac{G_{POA,t}}{1000}\,\big[1 + \gamma\,(T_{c,t} - \overline{T}_c)\big]\,\Delta t}$$

**Lost energy** (Ertragsausfall) during an outage, with $P^{\text{exp}}$ from a reference (neighbouring inverters, irradiance model, power curve):

$$E_{\text{lost}} = \sum_{t \in \text{outage}} \max\big(0,\; P^{\text{exp}}_t - P^{\text{meas}}_t\big)\,\Delta t$$

**Forecast of future loss** of an open fault until repair at time $t_r$ (feeds repair prioritisation):

$$\mathbb{E}[\text{Loss}] = \sum_{t = \text{now}}^{t_r} \hat{P}^{\text{component}}_t\,\Delta t \cdot \hat{p}_t$$

**Availability**: time-based $A_t = t_{\text{available}} / t_{\text{total}}$; energy-based (IEC 61400-26-2) $A_E = E_{\text{actual}} / (E_{\text{actual}} + E_{\text{lost}})$.

## L. Construction weather windows

Probability that an activity needing $d$ consecutive hours below thresholds (e.g. $v_{\text{hub}} < 10$ m/s and $H_s < 1.5$ m) can start in a given month: count, over many historical years of hindcast data, the fraction of start hours followed by $d$ workable hours. Feed these probabilities (or resampled historical weather years) into a Monte Carlo schedule model to get P50/P90 completion dates.
