# Rough or Just Noisy? — executable thesis research plan

**For:** Martin Valachy  
**Version:** 1.0 · 20 October 2026  
**Working title:** *Rough or Just Noisy? Measurement Error, Apparent Roughness, and the Decision Value of Volatility Forecasts*  
**Status:** research protocol draft. No new empirical result, replication or formal novelty claim is established by this document.

## 1. The project to execute

Investigate **when distinguishing genuinely rough latent volatility from nonrough volatility observed with error changes a forecast or a risk-sizing decision**.

The project has three separate outputs:

1. **Identification:** map the observation conditions under which rough and nonrough processes can be distinguished.
2. **Prediction:** compare forecasts after treating measurement error and persistence fairly.
3. **Decision value:** measure whether remaining differences change volatility control and net investor outcomes.

An accurate forecast does not, by itself, identify the true continuous-time mechanism. Conversely, evidence of roughness does not imply a profitable trading strategy. Keep these claims separate throughout.

An identification limit must be stated explicitly: if two candidate models induce the same joint distribution for the available observations and evaluation targets, those data cannot distinguish them. Approximate agreement on a finite grid can likewise imply low power. Structural claims therefore depend on the model class, observation assumptions and sampling design.

Martin's preferred format is a mathematical foundation, controlled simulations, real data and an interpretable risk application. Primary horizons are 1, 5 and 22 trading days. No crypto, commodities, neural-network project or full options-pricing calibration is needed. This is a substantial bachelor thesis with optional research extensions, rather than an attempt to resolve every rough-volatility controversy.

**Use plentiful compute to reduce numerical and statistical uncertainty.** It cannot create historical observations, remove data restrictions or make two observationally equivalent models identifiable.

### Planning basis and limits

The [preferred Notion proposal](https://app.notion.com/p/3fb65199416f81f1a80fd091e66595b3) was read on 20 October 2026. It records the intended writing window as after the August 2027 exams through approximately January/February 2028, and a planning allowance of 18 ECTS / about 540 hours. These are planning inputs from the proposal, not a fresh verification of UZH registration rules.

This plan incorporates a preliminary live literature scan. Some primary pages and selected full-text sections were inspected; most papers have not yet received a complete methodological audit. The older 20-slide ZIP was identified but its contents were not audited for this plan. No paper corpus or market dataset has been downloaded in this planning phase.

## 2. What must change in the earlier proposal

| Earlier assumption | Rule for this study |
|---|---|
| Finding low H in noisy smooth simulations is the main novelty | Treat it as replication and calibration. It is established territory. |
| Fukasawa–Takabatake–Westphal is only a challenge to roughness | Their noise-aware estimation also finds empirical evidence of roughness. Read the full argument and include this counterevidence. |
| Correcting noise should bring estimated H to 0.5 | Test the prediction under a specified DGP, sampling interval and lag band. Aggregation and mean reversion may prevent this. |
| A constant can always be subtracted from the variogram | That requires restrictive assumptions. Model correlated and state-dependent error separately. |
| Smoothness, roughness and memory are interchangeable | Local regularity, finite-lag scaling and long-run dependence are distinct. |
| A smooth Kalman model versus an uncorrected rough model is a fair mechanism test | Give both structural families the same noise information and comparable estimation opportunities. Include a flexible persistence control. |
| Insignificance means economic equivalence | Use predefined equivalence/noninferiority margins and confidence intervals, with an explicit inconclusive outcome. |
| Raw TAQ is the natural starting point | Start with documented realized measures. Obtain a small raw-price validation sample only when it answers an unresolved question. |
| More models or more grid searches make the thesis stronger | Freeze a small primary contest. Use additional compute for replication, coverage, power and numerical accuracy. |

**Close overlap requiring priority review:** Mouti's August 2026 preprint, [*Rough Volatility Across Assets*](https://arxiv.org/html/2608.16749v1), includes simulations, measurement-error correction and mean-reversion contamination. It is a preprint, and its formulas and empirical claims still require verification. Its scope makes a simple “noise correction across assets” novelty claim unsafe.

**Proposed contribution, still provisional:** a controlled map of *identification, forecast loss and decision regret* under matched rough/nonrough alternatives, followed by a small empirical application using the same protocol. Search specifically for prior versions of this combined experiment before describing it as new.

## 3. Research questions and registered claims

| ID | Question | Primary estimand | What would count as a useful result? |
|---|---|---|---|
| RQ1 | When does observation error or temporal aggregation imitate roughness? | Bias, RMSE and interval coverage of H; rejection rates under nonrough truth | A calibrated boundary between reliable, unreliable and inconclusive inference |
| RQ2 | Does roughness add predictive value after noise and persistence controls? | Paired out-of-sample QLIKE differences | A gain, practical equivalence, or a clearly bounded inconclusive result |
| RQ3 | Does model choice affect risk sizing? | Risk-tracking error and net certainty-equivalent return differences | A measured decision benefit or an upper bound on its practical size |
| RQ4 | Do empirical changes across estimators/frequencies match simulated signatures? | Within-asset change in estimates and forecasts | Compatibility with specified mechanisms; not proof of the true mechanism |

### Replace directional assumptions with falsifiable tests

- **H1:** quantify how often a specified nonrough DGP produces an apparently low H at each sample length, noise level and lag band. No universal bias claim.
- **H2:** estimate how often a rough forecast beats log-HAR under nonrough truth, and whether that advantage survives the noise-aware nonrough competitor.
- **H3:** test whether the best prespecified rough and nonrough forecasts are practically distinguishable within a registered margin.
- **H4:** compare frequency/estimator response patterns with simulations. Do not register “H must return to 0.5” as an unconditional empirical hypothesis.

Do not choose hypotheses, margins or primary models after observing final test results.

## 4. Literature acquisition and evidence protocol

### 4.1 Corpus construction

Start with the source register shipped with this plan. For each paper:

1. Resolve the publisher DOI and author/repository version; deduplicate working-paper and journal versions.
2. Download a lawful full text and supplements where accessible. Record unavailable items rather than substituting a guessed method.
3. Save title, authors, dates, version, URL, access date, license, SHA-256 and local relative path.
4. Extract text while retaining the PDF for equations, tables and page references.
5. Inspect formulas and assumptions visually in the source; extracted text alone is insufficient for notation.
6. Locate official replication code; record repository commit and license. Review before execution.
7. Write one evidence card covering the exact model, observation layer, target, estimator, sample, results, limitations and relevance.
8. Add backward references and forward citations only when they address a specific gap in the evidence map.

Use search phrases such as “rough volatility measurement error forecasting economic value”, “noise robust roughness identification”, “rough HAR measurement noise”, “volatility forecasting latent state space realized variance”, and “rough volatility mean reversion finite sample”. Repeat the novelty search before registration and before the final write-up. Do not schedule a recurring search unless separately requested.

### 4.2 Priority reading order

| Priority | Work | Why it is needed |
|---|---|---|
| 1 | Cont & Das (2024), *Rough Volatility: Fact or Artefact?* | Main artefact argument and a nonparametric estimator |
| 1 | Fukasawa, Takabatake & Westphal (2019 preprint / 2022 journal successor) | Estimation error, noise-aware likelihood and evidence supporting roughness |
| 1 | Bolko et al. (2023), *A GMM Approach to Estimate the Roughness of Stochastic Volatility* | Measurement-error-aware estimation and counterevidence |
| 1 | Mouti (2026), *Rough Volatility Across Assets* | Closest newly located overlap |
| 1 | Gatheral, Jaisson & Rosenbaum (2018), *Volatility Is Rough* | Original scaling and forecasting framework |
| 2 | Bennedsen, Lunde & Pakkanen (2022), *Decoupling the Short- and Long-Term Behavior of Stochastic Volatility* | Distinguishing roughness from persistence |
| 2 | Bennedsen, Christensen & Christensen (2026), *To Be or Not to Be: Roughness or Long Memory in Volatility?* | Modern estimation and dependence controls |
| 2 | Bennedsen et al. (2026), *The “Rough” HAR Model* | Recent parsimonious forecasting comparator; exact equations still to audit |
| 2 | Shi, Yu & Zhang (2025), *Realized Volatility Forecasting: Continuous versus Discrete Time Models* | Forecasting and economic-value overlap; full text must be retrieved |
| 2 | Corsi (2009); Bollerslev, Patton & Quaedvlieg (2016) | HAR and HARQ benchmarks |
| 2 | Patton (2011), *Volatility Forecast Comparison Using Imperfect Volatility Proxies* | Evaluation with noisy targets |
| 3 | Andersen, Bollerslev & Meddahi (2011) | Forecasting and price microstructure noise |
| 3 | Barndorff-Nielsen et al. (2008), realized kernels | A price-noise-robust realized measure |
| 3 | Chong et al. (2024), central limit theorems; minimax companion | What valid roughness inference requires |
| 3 | Diebold–Mariano; stationary bootstrap; Model Confidence Set | Dependence-aware forecast inference |
| 3 | Moreira & Muir (2017) | Economic motivation; their inverse-variance rule is not identical to our constant-volatility rule |
| Data | Cipollini et al. (2026), VOLARE; official WRDS documentation | Definitions, coverage, access and reproducibility |

### 4.3 Evidence card schema

For every source create: source_id, full citation, version, peer-review status, access level, source pages/sections, exact claim, model assumptions, noise assumptions, data and horizon, reproduced item, replication status, contradictions, and “what our thesis adds”.

Maintain a novelty matrix with columns: known-truth simulation; realistic RV construction; price noise; aggregation; robust H inference; matched persistence; out-of-sample forecasts; risk decisions; uncertainty. Fill “not found in inspected sections” rather than “absent” until full text has been checked.

**Gate G0:** write a two-page positioning memo. If a paper already executes the proposed experiment, narrow to an independently justified replication/extension. A rigorous replication may still be a valid bachelor contribution, subject to supervisor agreement.

## 5. Mathematical specification and formula audit

All formulas below are starting specifications to derive, check numerically and reconcile with the selected paper. They are not new empirical findings.

### 5.1 Separate the objects

Let s be continuous time measured in trading days and let v_s be instantaneous variance per trading day:

\[
d\log S_s=(\mu_s-\tfrac12v_s)\,ds+\sqrt{v_s}\,dW_s,\qquad
p^{obs}_{s_i}=\log S_{s_i}+\eta_{s_i}.
\]

For day t:

\[
IV_t=\int_{t-1}^{t}v_s\,ds,\quad
RV_t^{(M)}=\sum_{i=1}^{M}(p^{obs}_{t_i}-p^{obs}_{t_{i-1}})^2,\quad
x_t=\log IV_t,\quad y_t=\log RV_t.
\]

Keep **log spot variance**, **log integrated variance**, **realized variance** and **realized volatility** separate in code and text. Daily integration is an observation operator, not an innocuous relabeling of a spot process.

There are at least three distinct effects:

- Finite-sampling error: RV differs from IV even at efficient prices.
- Market microstructure noise: observed prices differ from efficient prices.
- Aggregation and nonlinear transformation: IV and log IV have different dynamics from spot variance and log spot variance.

Jumps add another distinction between integrated continuous variance and quadratic variation. Start without jumps; add them as a declared robustness case.

### 5.2 Noisy variogram

Use the toy observation model y_t=x_t+e_t. For stationary centered errors:

\[
m_y(k)=E[(y_{t+k}-y_t)^2]
=m_x(k)+2\{\gamma_e(0)-\gamma_e(k)\}
+2E[(x_{t+k}-x_t)(e_{t+k}-e_t)].
\]

If errors are independent of the latent process and independent over time with variance q:

\[
m_y(\Delta)=c\Delta^{2H}+2q
\]

when the latent variogram has that power-law form. Then the local population slope gives

\[
H_{\mathrm{eff}}(\Delta)
=\tfrac12\frac{d\log m_y(\Delta)}{d\log\Delta}
=H\,\frac{c\Delta^{2H}}{c\Delta^{2H}+2q}.
\]

This explains attenuation under the toy assumptions. It is not an exact formula for arbitrary RV error.

For heteroskedastic, serially uncorrelated exogenous error, subtract the pair-specific expected q_t+q_{t+k}, not an arbitrary global constant. Correlated error requires covariance terms. A negative corrected variogram is a diagnostic of instability or misspecification; do not silently clip it and report H.

### 5.3 Quarticity-based sampling variance

For one-day intervals of length one, no price noise or jumps and suitable diffusion assumptions:

\[
IQ_t=\int_{t-1}^{t}v_s^2ds,\qquad
RQ_t=\frac{M}{3}\sum_{i=1}^{M}r_{t,i}^4,
\]

\[
\operatorname{Var}(RV_t-IV_t\mid v)\approx\frac{2IQ_t}{M},\qquad
\operatorname{Var}(\log RV_t-\log IV_t\mid v)
\approx\frac{2IQ_t}{M\,IV_t^2}.
\]

The plug-in diagnostic is qhat_t=2 RQ_t/(M RV_t^2). Derive the delta-method approximation and its scaling. Log errors need not have zero mean: a second-order approximation gives a mean correction near -IQ_t/(M IV_t^2). Include that bias or test its materiality.

**Critical restriction:** this is finite-sampling uncertainty under stated assumptions, not a universal estimator of price microstructure noise. Realized kernels and pre-averaging have different variance formulas. Nested sampling grids create correlated errors. Validate before using qhat in an observation likelihood.

### 5.4 Nonrough does not mean differentiable

A Brownian OU process is locally H=0.5 but is not differentiable. Use “diffusion/nonrough” rather than implying smooth calculus paths.

For stationary dX_s=-kappa(X_s-mu)ds+nu dB_s:

\[
m_X(\Delta)=\frac{\nu^2}{\kappa}(1-e^{-\kappa\Delta}),\qquad
H_{\mathrm{eff}}(\Delta)=\frac12\frac{\kappa\Delta}{e^{\kappa\Delta}-1}.
\]

The effective slope is below 0.5 at finite lags even without observation error. Derive this special case and compare it with simulated OU paths. This is a useful benchmark against which to audit newer fOU contamination formulas. Large daily lags do not identify small-time regularity automatically.

### 5.5 Gaussian projection and retransformation

For a jointly Gaussian latent log-variance target X_f and observed history Y:

\[
E[X_f\mid Y]=\mu_f+K_{fY}K_{YY}^{-1}(Y-\mu_Y),
\]
\[
\operatorname{Var}(X_f\mid Y)=K_{ff}-K_{fY}K_{YY}^{-1}K_{Yf}.
\]

Solve linear systems; do not explicitly invert covariance matrices. Include observation noise in K_YY. Check the covariance is positive definite.

For a Gaussian log-variance with conditional mean a and variance b:

\[
E[e^{X_f}\mid Y]=e^{a+b/2}.
\]

For the h-day **average variance** target,

\[
V_{t,h}=\frac1h\sum_{j=1}^{h}IV_{t+j},
\quad
\widehat V_{t,h}=\frac1h\sum_{j=1}^{h}\exp(a_{t,j}+b_{t,j}/2).
\]

Do not exponentiate an average log variance and call it average variance. If the Gaussian model concerns spot log variance, obtain daily integrated forecasts through numerical integration/simulation. A daily Gaussian log-IV approximation must be labeled and validated.

Log-HAR also needs a training-only retransformation correction, checked by horizon. HARQ must follow the source's actual specification; do not invent a log-HARQ by changing labels.

### 5.6 Loss and risk rule

Primary forecast loss, up to forecast-independent terms:

\[
L_{t,h}(\widehat V)=\log\widehat V+\frac{\widetilde V_{t,h}}{\widehat V}.
\]

All predictions must be finite and positive. This QLIKE form tolerates a zero proxy and avoids logging the realized target. Its robustness to a noisy proxy depends on conditional unbiasedness conditions; compare rankings against true IV in simulation and across empirical evaluation proxies.

Annualized forecast volatility is sqrt(252 Vhat). For annual target sigma_star:

\[
w_t=\min\left(w_{\max},
\frac{\sigma_\star}{\sqrt{252\,\widehat V_{t,1}}}\right).
\]

Core settings: sigma_star=10% and w_max=1, with a registered w_max=2 extension including borrowing costs. The h=5/22 forecast exercises are core statistical results; weekly/monthly trading policies are secondary and need their own holding-period accounting.

**Gate G1:** formula notebook contains derivations, dimensional checks, assumptions, source-page references and numerical limiting-case checks. Martin independently explains the central derivations.

## 6. Data acquisition plan

### 6.1 Preferred order

| Tier | Source | Required use | Gate / limitation |
|---|---|---|---|
| A | VOLARE | Fast public-data pilot and possibly main daily panel | Verify actual asset list, dates, sampling frequencies, estimator definitions, licensing and overnight treatment |
| B | Official replication datasets | Reproduce one or two published results | Check version, license, definitions and coverage |
| C | WRDS NYSE TAQ or entitled WRDS-derived intraday indicators | Small validation sample, then custom RV/noise diagnostics | Verify Martin's actual entitlement; a supervisor alone does not automatically grant a subscription |
| D | CRSP or another documented entitled daily-return source | Adjusted returns and overnight component | Confirm total-return, split and timestamp conventions |
| E | OptionMetrics / VIX information | Optional extension after core results | Implied quantities are not the same estimand as realized physical variance |

Public provider descriptions verify that VOLARE supplies realized measures and WRDS offers TAQ-related products. **No personal access, exact common sample or download permission has been tested.** Do not infer raw-price access from access to realized statistics.

### 6.2 Candidate panel and periods

- Primary asset: SPY, if available with required measures.
- Candidate small panel: SPY, QQQ, IWM, EFA, TLT. Final inclusion depends on the provider inventory and a common history; lock the list before test evaluation.
- Intended period: 2007–2025, only if common documented coverage supports it.
- Provisional split: training 2007–2016, validation 2017–2019, final historical test 2020–2025.
- These dates are design choices, not statements of dataset coverage. If infeasible, register replacement dates from the inventory before examining model comparisons.
- Reserve 2026 data, if later available, for a separately versioned confirmation exercise. Historical tests are not literally unseen to the world; document any pilot peeking.
- A cross-section of 20–50 stocks is optional. Define the universe with historical membership/availability rules; avoid selecting today's survivors because their results look convenient.

Primary equal-asset summaries use within-asset loss normalization or paired differences with a declared scale. Do not let one high-variance asset dominate a pooled average.

### 6.3 Required fields

See data_dictionary.csv. Minimum: stable asset ID, date, session, RV and frequency, RQ and convention, robust realized measure, returns, overnight flag, price/return units, calendar, observation count, provenance and quality flags. For raw validation also need timestamps, trade/quote conditions, prices, sizes and the relevant exchange/session documentation.

### 6.4 Cleaning and validation

1. Download metadata and a small sample first; preserve raw files unchanged with hashes.
2. Normalize time zones using the exchange calendar, including DST and early closes.
3. Apply documented trade/quote-condition filters. Audit crossed/locked quotes and stale prices if using quotes.
4. Construct fixed session grids. Record prior-tick/interpolation rules and the maximum permitted stale gap.
5. Construct RV at 1, 5, 15 and 30 minutes only where data support it. Do not promise a frequency unavailable in a precomputed archive.
6. Record missing bars and prices, duplicates, outliers, trading halts and adjustment rules.
7. Recompute a small set of daily measures independently; compare to provider output with declared tolerances.
8. Inspect volatility-signature plots and the behavior of RV/RQ/robust measures.
9. Explain all exclusions and report how they change results.

**Session alignment:** initial identification studies use regular-session IV/RV. An overnight holding strategy requires close-to-close variance/return alignment and an explicit overnight forecast. Either add that component for every model or use an explicitly implementable open-to-close policy with documented execution delay. Do not evaluate an overnight strategy using only intraday risk.

**Gate G2:** freeze a data card, entitlement record, field mapping, sample coverage table, exclusion log and hashes. If raw data remain unavailable, retain the public-data thesis and narrow claims about price noise.

## 7. Simulation program

### 7.1 Three levels

**Level A — analytical toy.** Daily Gaussian latent log variance plus independent, then heteroskedastic/correlated observation errors. Check the identities in Section 5. This is a diagnostic, not the main realistic market experiment.

**Level B — efficient-price experiment.** Simulate continuous-time latent volatility and efficient prices. Integrate true daily variance, sample the same price paths at different grids and reconstruct RV/RQ. Separate spot-path regularity from daily integrated behavior.

**Level C — observed-price experiment.** Add price microstructure noise, bid–ask-like dependence, irregular/stale observations and optional jumps. Use documented parameter ranges from the development data. Add one complication at a time.

### 7.2 DGP families

| Family | Role |
|---|---|
| Rough Gaussian log-spot volatility, stationary fOU or another fully specified positive-definite covariance model | Known rough truth; H in {0.05, 0.10, 0.20, 0.35} |
| One-factor Brownian OU log volatility | Transparent nonrough control and analytic checks |
| Two-factor OU log volatility | Nonrough model with fast and persistent components |
| Flexible finite-factor OU mixture | Check whether a rough model merely has a better finite-grid covariance fit |
| Optional regime shifts, leverage and jumps | Misspecification stress cases, not the initial primary grid |

Normalize v_s=exp(mu+X_s-Var(X_s)/2) where X is centered stationary Gaussian, so mean variance is exp(mu). Define the exact stationary initialization and burn-in. Use a validated fOU simulator rather than treating fractional Brownian motion as independent increments.

For finite factor mixtures, every finite model remains locally diffusion-like while approximating rough covariance over a finite observed grid. Label this as an identification challenge. Include both a simple two-factor and a more flexible control; otherwise a rough-model win can reflect persistence flexibility.

### 7.3 Matching and fairness

Use two designs:

- **Mechanism isolation:** match mean variance, stationary log-variance dispersion and selected development-sample autocovariances, then vary roughness/noise.
- **Estimated practical fit:** each family estimates its parameters from the same observed training information.

Document matching error. Do not calibrate a nonrough process to be deliberately inferior, and do not hand the rough model true parameters while estimating its rival. Give stochastic model families both noise-aware and noise-ignorant variants. Keep the observation operator and available history identical.

### 7.4 Initial experiment grid

- H: 0.05, 0.10, 0.20, 0.35; Brownian control H=0.50.
- Observation noise-to-latent log-increment variance ratios: 0, 0.25, 1, 4 in the toy study.
- Latent mean-reversion half-lives: 5, 22, 126 trading days, with the exact two-factor combinations declared.
- Samples: 1,250 and 5,000 daily observations.
- RV grids: 1, 5, 15, 30 minutes where applicable.
- H-estimation lag bands: 1–5, 1–10 and 1–22 days; 1–10 is primary.
- Forecast horizons: 1, 5, 22 days.

Do not multiply every axis blindly. Use a small crossed primary grid, then targeted stress cells. Freeze primary cells before large production runs.

### 7.5 Numerical validity and compute allocation

1. Pilot 100 independent paths per primary cell to debug and estimate runtime/Monte Carlo variability.
2. Choose production replication counts for precision, before inspecting favorable effects.
3. Default 2,500 paths per selected cell: worst-case Monte Carlo standard error for a rejection probability is about 1 percentage point.
4. If a registered contrast needs tighter precision, use a preregistered precision rule up to 10,000 paths; worst-case standard error is about 0.5 percentage points.
5. For mean losses, report the paired Monte Carlo standard error, not only the path count.
6. Use independent random streams per cell/replicate and common random numbers for paired observation treatments where valid.
7. Validate a subset with an independent covariance/simulation method and finer intraday grids; report discretization error relative to the scientific effect.
8. Cache sufficient statistics and model fits. Keep benchmark timing, failed fits and all seeds.

Parallelize independent simulation paths and bootstrap draws. GPUs are optional after accuracy checks; floating-point differences and repeated random seeds can invalidate an impressive-looking large run. Use double precision for covariance and likelihood work unless error analysis supports otherwise.

### 7.6 Simulation outputs

For each registered cell report H bias/RMSE, interval coverage, false roughness declarations under nonrough truth, power under rough truth, fit failure rate, forecast losses against **true IV**, losses against noisy proxies, exposure disagreement and decision regret.

Two oracle diagnostics:

- Known-parameter forecast using exactly the competitors' observed information.
- Latent-state-information forecast as a clearly privileged bound.

Neither may be mixed into the feasible empirical model ranking. Future realized IV is an outcome, never a forecast input.

**Gate G3:** toy identities and efficient-price construction pass; known-truth estimator behavior and uncertainty are reported before interpreting empirical H estimates.

## 8. Estimation and forecast contest

### 8.1 Model set

| ID | Model | Purpose |
|---|---|---|
| M0 | Last observed variance / historical scale benchmark | Detect basic pipeline failures |
| M1 | EWMA | Simple adaptive baseline |
| M2 | Log-HAR | Standard daily/weekly/monthly benchmark |
| M3 | HARQ in its validated source specification | Measurement-uncertainty-aware regression |
| M4 | Rough Gaussian/fOU projection with observation noise | Structural rough competitor |
| M5 | Two-factor diffusion state-space model with observation noise | Main nonrough competitor |
| M6 | Prespecified flexible finite-factor diffusion model with noise | Persistence/covariance fairness check |
| M7 | The 2026 Rough HAR specification, after exact replication audit | Current parsimonious comparator |

M4 without noise and M5 without noise are ablations. Use identical input measures and history limits for the primary comparison. Adding an estimator-specific feature to only one model is a secondary information-set experiment.

A Kalman filter is exact only for a valid linear Gaussian observation/state system. Modeling log daily IV as Gaussian is an approximation to the integrated continuous-time model. Validate that approximation in simulation. If it fails materially, use validated quadrature/simulation filtering or explicitly limit the claim to a reduced-form forecasting model.

### 8.2 Chronological protocol

- Fit using a rolling window of 1,250 days, refitting every 22 trading days.
- Require a sufficient prespecified warm-up for every model.
- Use expanding windows only as registered robustness.
- Define direct or projected multi-horizon forecasts separately; do not mix target definitions.
- Choose tuning settings on training/validation data only.
- For h-step training labels, use only labels whose complete future horizon has matured by the fit time. Purge labels that cross split boundaries.
- Fit transformations, normalization, smearing, noise calibration and regularization within the same available-information set.
- Save each forecast before loading its realized evaluation outcome.
- Record forecast origin, information cutoff, execution time, training end, parameters, input hashes, convergence and forecast value.

Implement simple models first. Freeze the validation-selected primary rough/nonrough comparison before opening the final test. Every later change becomes a new protocol version and sensitivity result.

### 8.3 H estimation

Naive variogram slopes are descriptive diagnostics. Add at least one literature-grounded noise-aware inferential estimator after checking its assumptions and numerical feasibility.

Report lag-band sensitivity and sampling uncertainty. Ordinary regression standard errors across overlapping lag moments are not valid automatically. Use a justified estimator-specific inference method, with simulation coverage checks. If no implemented method has acceptable coverage, report descriptive apparent scaling and avoid formal claims about latent H.

## 9. Forecast evaluation and inference

### 9.1 Endpoints and hierarchy

Primary statistical endpoint: h=1 QLIKE difference, M4 versus M5, on SPY; repeat on an equal-weight small-panel summary. Primary economic endpoint: h=1 risk-tracking error difference. Define this hierarchy before the final run.

Secondary endpoints: h=5/22 QLIKE, true-IV MSE in simulation, empirical proxy MSE, calibration plots, turnover, net certainty-equivalent return and drawdown.

Use the same primary evaluation proxy for every model. In simulation evaluate against both truth and proxies. Empirically rotate evaluation proxies as sensitivity checks; the robust estimator is still not ground truth.

### 9.2 Dependence and multiple testing

- Analyze paired loss differences at common forecast origins.
- Use dependence-aware confidence intervals and Diebold–Mariano-style/HAC diagnostics where assumptions support them.
- Overlapping h-day targets induce dependence; h-1 lags alone need not capture all persistence.
- Primary resampling: jointly resample all assets and models by date using stationary blocks. Provisional mean block length 44 days; report 22/66-day sensitivity and check calibration in simulation.
- Use 4,999 bootstrap draws initially; increase only for a registered precision need.
- Account for refitting uncertainty where required by the inference target; a bootstrap over saved losses does not automatically reproduce parameter-selection uncertainty.
- Apply Holm correction to the limited primary comparison family. Use the Model Confidence Set as a secondary summary, not proof of equivalence.
- Do not treat assets, overlapping targets, or bootstrap replicates as independent historical observations.

If long memory or structural breaks invalidate conventional methods, demonstrate the limitation using the simulated DGPs and restrict inferential claims. A bootstrap does not repair every dependence problem.

### 9.3 Practical equivalence

Before test evaluation, set margins with reference to validation-scale losses and the decision objective. Starting proposals, to be ratified at registration:

- Forecast loss margin: 1% of the validation mean QLIKE score expressed in the **nonnegative ratio-based form**, not 1% of log(Vhat)+V/Vhat, whose level depends on variance units.
- Economic margin: 25 basis points of annual net certainty-equivalent return.
- Risk-tracking margin: a declared absolute/relative difference tied to the investor's volatility target.

For the ratio-based QLIKE, use V/Vhat-log(V/Vhat)-1 on strictly positive validation proxies; specify any zero handling. Fix the resulting numerical margin in the protocol before the test. Report results under a small prespecified margin sensitivity set.

Use a two-one-sided-test or corresponding 90% confidence-interval construction at a 5% equivalence level. If the interval is too wide, label the comparison **inconclusive**. Distinguish equivalence from one-sided noninferiority.

**Gate G4:** a mock report with simulated outputs demonstrates correct coverage, labels, scaling and inference. No new test-data tuning afterward.

## 10. Economic application

Use a transparent long-only risky asset plus cash policy. This is a risk-sizing application, not stock selection.

Core risk target: 10% annualized, no leverage. Freeze the policy and trading timestamp. Primary daily statistical study remains regular-session variance until overnight alignment is solved.

For a close-to-close implementation, combine each model's intraday forecast with the same prespecified overnight-component method and a coherent daily variance definition. Availability and execution must be realistic. Otherwise implement an open-to-close policy with a conservative delay and forecast information available before entry.

Define net returns with cash yield, turnover costs and, in the leveraged extension, financing costs. Record drifted pretrade weights: turnover is not always just the difference between consecutive target weights.

Primary risk-tracking score:

\[
RTE=\frac1T\sum_t\left(252\,w_t^2\,\widetilde V_{t,1}-\sigma_\star^2\right)^2.
\]

Use an evaluation variance aligned with the return interval. Also report realized annualized strategy volatility and the fraction of dates the exposure cap binds. A cap can make different models produce identical exposures.

Secondary mean–variance annualized certainty equivalent:

\[
CE_\gamma=252\,\overline r_{net}-\frac{\gamma}{2}\,252\,\widehat{\operatorname{Var}}(r_{net}),
\quad \gamma=5
\]

with sensitivity gamma in {2,10}. Label this a specified mean–variance criterion, not exact expected CRRA utility.

Start transaction-cost sensitivities at 0, 1, 5 and 10 basis points per unit traded; these are illustrative scenarios until calibrated to the asset and execution convention. Add cash and borrowing inputs explicitly. Compare fixed exposure, trailing-RV targeting and forecast targeting.

Report turnover, leverage/cap usage, maximum drawdown, risk tracking, net CE and uncertainty. Sharpe and cumulative wealth are secondary descriptions. No expected positive return finding is assumed.

For h=5/22, use a frozen nonoverlapping rebalance schedule with holding-period forecasts and daily mark-to-market accounting. Treat alternative staggered schedules as sensitivity. Do not count overlapping strategy windows as independent portfolios.

Decision regret in simulation means the utility/risk loss relative to a correctly defined feasible-information oracle, with privileged latent-information bounds shown separately.

## 11. Interpretation rules

| Result | Permitted interpretation |
|---|---|
| Nonrough simulations yield low naive H | The diagnostic can be misleading under those specified conditions |
| Rough forecasts win under nonrough truth | Predictive success alone does not identify roughness |
| Noise-aware models are practically equivalent with tight intervals | Model choice has limited value within the registered margin and setting |
| No significant difference with wide intervals | Evidence is insufficient |
| Corrected empirical H stays low | The tested error correction does not remove apparent roughness; its assumptions still matter |
| Corrected empirical H rises | Estimates are sensitive to measurement treatment; this alone does not prove nonrough latent volatility |
| Rough model beats simple OU but not flexible OU | Persistence/covariance flexibility may explain part of the gain |
| No economically material gain | A useful bound on the decision value, if precision is adequate |

Do not choose a preferred mechanism because it produces a better story. Negative or mixed results can still produce a strong thesis through validated design, precise estimates and transparent limitations.

## 12. Reproducibility and execution structure

Use a dedicated research workspace outside the read-only synced sources. The eventual project should contain:

- protocol/: versioned protocol, hypotheses, decisions and amendments.
- literature/: evidence cards, references and lawful documents.
- data/raw/: immutable inputs; data/derived/: reproducible outputs.
- manifests/: source versions, licenses, hashes and data provenance.
- configs/: experiment and estimation specifications.
- src/: data, simulators, models, evaluation and reporting modules.
- tests/: mathematical identities, simulator/covariance checks, leakage and accounting checks.
- runs/: run metadata, seeds, code/environment versions, logs and failures.
- results/: machine-readable tables and figure inputs.
- thesis/: text, bibliography and reproducible figures.

The companion experiment_plan.json is a specification, not implemented software. Future command names such as acquire, validate, simulate, forecast and report are interfaces to build later, not claims that those commands already exist.

Lock software dependencies and record hardware, numeric precision and runtimes. Each scientific run needs a unique run ID, protocol version, configuration hash, data hash, code version, random-stream map and status. Separate exploratory and registered results.

Meaningful checks: exact OU covariance; noise-free limits; known-noise variogram; positivity/normalization; Gaussian retransformation; covariance simulation; horizon alignment; matured-label checks; all-model common dates; strategy turnover/cash accounting; numerical refinement. Re-run only checks affected by a change.

Maintain a claim-to-evidence ledger. Every reported number must resolve to a run/table; every literature claim to a source/page. Do not let AI-generated summaries substitute for reading the cited method.

Public reproduction may include code, synthetic data and permitted derived outputs. Restricted raw data remain in the entitled environment. Check derived-output sharing permissions before packaging.

## 13. Work packages, outputs and gates

The 540-hour allocation is a planning model, including Martin's reading, understanding and writing. It is not a promise that AI can replace this work.

| Phase | Human-hour budget | Concrete output | Exit condition |
|---|---:|---|---|
| P0 Literature and novelty | 45 | Source cards, novelty matrix, positioning memo | G0: defensible narrowed contribution |
| P1 Formula and observation audit | 45 | Derivations, numerical checks, model specification | G1: assumptions and estimands explicit |
| P2 Data access and pilot | 45 | Data card, small clean panel, coverage/exclusion audit | G2: usable lawful data and aligned fields |
| P3 Simulation infrastructure and replication | 90 | Validated simulators; 1–2 published figures/tables reproduced | G3: known-truth behavior understood |
| P4 Primary simulation and forecasting | 95 | Frozen model contest, production simulation, forecast panel | G4: protocol locked; implementation validated |
| P5 Economics and inference | 65 | Risk/utility results, intervals and decision map | Common sample and valid accounting |
| P6 Robustness | 45 | Prespecified stress checks and limitations | Main claims survive or are narrowed |
| P7 Writing and reproduction | 70 | Thesis, figures, code/data guide, presentation | Independent rerun and supervisor-ready draft |
| P8 Contingency | 40 | Data/method fixes and final review | Unresolved issues disclosed |
| **Total** | **540** | | |

Calendar logic: preparation now can cover literature and learning; formal empirical work must respect the eventual supervisor's rules about work before registration. Use relative phases until registration and deadlines are confirmed. No supervisor contact or application/calendar change is part of this request.

### Minimum complete thesis

A complete literature positioning, audited observation model, one rough and two nonrough DGPs, validated H diagnostics, a small daily empirical panel, log-HAR/HARQ and noise-aware rough/nonrough forecasts, h=1/5/22 statistical evaluation, and one daily risk-sizing application.

### Extension order

1. Matched flexible persistence control and estimator/frequency sensitivity.
2. Liquidity/noise differences across a small stock cross-section.
3. Jumps and leverage.
4. Multi-asset risk allocation, only with validated covariance forecasts.
5. VIX/option-implied information.

Some observation-noise robustness is essential to the core scientific question; it is not all an optional extension. Full volatility-surface calibration, deep learning and massive cross-asset coverage remain outside this plan.

## 14. Expected figures, tables and thesis structure

**Figures:** observation layers; same latent path under several measurement schemes; true versus apparent H; bias/coverage heatmap; frequency and lag-band sensitivity; forecast-loss map; exposure disagreement; risk/utility regret map; empirical forecast calibration; strategy risk/turnover summary.

**Tables:** literature novelty matrix; data/quality card; replication accuracy; DGP parameters and matching errors; primary forecast contest with intervals; practical-equivalence conclusions; economic outcomes and costs; failures/robustness.

**Chapters:** introduction and contribution; literature; mathematical/observation framework; data and protocol; controlled simulations; empirical forecasting; economic application; limitations and conclusion. Put extensive grids, proofs and software details in appendices. Confirm length/style requirements with the supervisor.

## 15. What the assistant should do in the next research session

Read NEXT_SESSION_PROMPT.txt and execute the preparation stage in order:

1. Load this protocol and companion files; preserve the existing Notion proposal.
2. Verify current institutional, data-use and AI-disclosure requirements from official sources before producing material for formal submission.
3. Acquire priority full texts/supplements/code and complete the evidence ledger.
4. Audit the closest overlaps, including the 2026 papers.
5. Produce the two-page novelty/feasibility memo, including any required narrowing.
6. Audit formulas and derive the toy and OU identities.
7. Inspect actual public data inventory and download only a pilot slice.
8. Implement and validate the toy experiment; reproduce one published result.
9. Report what passed, failed and remains unknown, with files and evidence.
10. Freeze a revised empirical protocol before production experiments.

This session prepares a plan. It does not silently start a large data download or claim research findings.

## 16. Current status and unresolved decisions

**Completed now:** preferred proposal read; preliminary source discovery; methodological corrections identified; staged plan, data schema, source register and experiment specification prepared.

**Not yet completed:** full-text corpus, replication audit, data entitlement tests, actual downloads, code implementation, calibration, power/coverage experiments, empirical estimates and thesis writing.

**Still to decide from evidence:** exact data coverage; feasible roughness inference method; source-faithful Rough HAR implementation; whether daily Gaussian approximations are adequate; primary evaluation proxy; execution/overnight design; exact equivalence margins; supervisor requirements and final novelty claim.

## 17. Primary-source links

- [S01 Gatheral, Jaisson & Rosenbaum — Volatility Is Rough](https://arxiv.org/abs/1410.3394)
- [S02 Cont & Das — Rough Volatility: Fact or Artefact?](https://link.springer.com/article/10.1007/s13571-024-00322-2)
- [S03 Fukasawa, Takabatake & Westphal — Is Volatility Rough?](https://arxiv.org/abs/1905.04852)
- [S04 Bolko et al. — GMM roughness estimation](https://arxiv.org/abs/2010.04610)
- [S05 Bennedsen, Lunde & Pakkanen — Decoupling](https://arxiv.org/abs/1610.00332)
- [S06 Bennedsen, Christensen & Christensen — Roughness or Long Memory](https://arxiv.org/abs/2403.12653)
- [S07 Bennedsen et al. — The “Rough” HAR Model](https://arxiv.org/abs/2609.21587)
- [S08 Mouti — Rough Volatility Across Assets](https://arxiv.org/html/2608.16749v1)
- [S09 Shi, Yu & Zhang — Continuous versus Discrete Time Models](https://fba.um.edu.mo/wp-content/uploads/2025/10/VolatilityForecast_draft8.pdf)
- [S10 Corsi — HAR](https://doi.org/10.1093/jjfinec/nbp001)
- [S11 Bollerslev, Patton & Quaedvlieg — Exploiting the Errors](https://scholars.duke.edu/publication/1072550)
- [S12 Patton — Imperfect Volatility Proxies](https://public.econ.duke.edu/~ap172/Patton_vol_proxies_JoE_2011.pdf)
- [S13 Andersen, Bollerslev & Meddahi — Forecasting and Microstructure Noise](https://www.tse-fr.eu/publications/journal-article/realized-volatility-forecasting-and-market-microstructure-noise)
- [S14 Barndorff-Nielsen et al. — Realized Kernels](https://ora.ox.ac.uk/objects/uuid%3A6d31a2ea-e395-4626-8699-c829a4869eea)
- [S15 Chong et al. — Central Limit Theorems](https://arxiv.org/abs/2210.01216)
- [S16 Chong et al. — Minimax Theory](https://arxiv.org/abs/2210.01214)
- [S17 Diebold & Mariano — Comparing Predictive Accuracy](https://www.nber.org/papers/t0169)
- [S18 Politis & Romano — Stationary Bootstrap](https://doi.org/10.1080/01621459.1994.10476870)
- [S19 Hansen, Lunde & Nason — Model Confidence Set](https://doi.org/10.3982/ECTA5771)
- [S20 Moreira & Muir — Volatility-Managed Portfolios](https://www.nber.org/papers/w22208)
- [D01 Cipollini et al. — VOLARE](https://arxiv.org/abs/2602.19732)
- [D02 Official VOLARE platform](https://volare.unime.it/)
- [D03 Official WRDS TAQ product documentation](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/nyse-trade-and-quote-taq/)
- [D04 Official WRDS Intraday Indicators](https://wrds-www.wharton.upenn.edu/pages/grid-items/wrds-intraday-indicators/)

