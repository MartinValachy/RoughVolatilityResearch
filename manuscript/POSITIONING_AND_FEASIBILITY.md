# Positioning and feasibility - 20 October 2026

The basic proposition that nonrough volatility can look rough through an imperfect realized proxy is established. A defensible publication cannot rest on rediscovering it. The most promising direction is a bounded replication and extension that quantifies how much **identification, predictive loss and a specified risk decision** can differ under comparable observation laws. The current checkpoint demonstrates that this question is feasible computationally, while exposing data and inferential gates that must be resolved before empirical claims.

## What is already established

Gatheral-Jaisson-Rosenbaum motivate rough stochastic volatility through scaling and forecasting evidence, while explicitly recognizing the difference between short-window and daily integrated proxies (S01, author-version pp 7-8, 20-21). Cont-Das show why consistency for integrated variance does not preserve spot-path regularity, and develop a normalized-variation estimator (S02, pp 4-7, 12-14). Their statistic is not interchangeable with an OLS log-variogram slope.

Noise awareness is not evidence against roughness by definition. Fukasawa-Takabatake-Westphal model a local Gaussian log RV error, prove consistency under their high-frequency regime, and still report rough empirical behavior (S03, pp 4-7; differently titled 2022 journal successor). Bolko and coauthors correct realized-measure moments within GMM and likewise report low H (S04, pp 12-15 and journal abstract). These papers rule out the original proposal's unconditional prediction that noise correction should restore H=0.5.

Roughness and persistence are separate modeling dimensions. Bennedsen-Lunde-Pakkanen explicitly decouple them, offer a noise-aware offset estimator, and compare forecasts (S05, pp 6, 13-17, 37-38). The newer composite-likelihood work also highlights memory-dependent inference and proxy distortion (S06, pp 3-5, 36-37). Finite-factor approximations to rough dynamics are established prior art, including Abi Jaber-El Euch's Markovian approximations (S21, Section 3). Our covariance matching is not a new approximation paradigm.

## Closest overlaps and required narrowing

The September 2026 **Rough HAR** preprint is closer than the draft register suggested. It does not only add an MA1 forecasting term. Section 4 explicitly considers a latent ARMA with observed log RV error variance fixed to 2/78 and tests the noise-only restriction; the authors also warn that a discrete-time MA coefficient is not literal continuous-time path roughness (S07, pp 12-13, 23-24). A claim that this source ignores measurement error would be incorrect.

Mouti's August 2026 preprint already combines cross-asset scaling, measurement-error corrections, mean reversion and known-truth simulations (S08, pp 7-13). A simple frequency/noise correction study therefore has substantial overlap. Our independent audit reproduces the Brownian special case but leaves 13/48 cells of its deterministic Table 2 outside a prespecified tolerance; both spectral-integral implementations agree in checked cells. This is an unresolved replication discrepancy, not a declaration that the paper's empirical conclusions fail.

Shi-Yu-Zhang already compare continuous/discrete forecasts using an inverse-volatility risk-parity utility criterion (S09, pp 22-25). HARQ is an established observation-precision benchmark, and Patton establishes conditions for evaluating variance forecasts with imperfect proxies (S11, p 11; S12, pp 3-5). We cannot claim first economic evaluation of rough forecasts. A possible narrower extension is matched observation treatment, a flexible nonrough covariance control, calibrated uncertainty, and a transparently implementable risk application. Whether the complete combination is novel remains unestablished: the novelty matrix distinguishes inspected evidence from unassessed sections.

## What the executed pilot contributes

These are **illustrative results**, not final empirical findings. The pilot produced 1400 independent latent daily paths across 62 observation cells, 100 continuous-time Brownian OU price paths, and 225000 baseline forecasts. Exact source references and run IDs are in the companion report/claim ledger.

The useful design finding is the flexible persistence control. For one prespecified rough Cauchy daily log IV law, a finite OU mixture matches the observable covariance much more closely than a two-factor OU with fixed rates. On 1250 noisy daily observations, the computed Gaussian KL divergence is 0.00144. A Pinsker calculation bounds the power of an exact-size 5% test between these two known laws by about 7.68%. The independent Monte Carlo power estimate is 8%, with 2.71 percentage-point MCSE. This is a concrete low-power example, not a universal impossibility theorem for volatility data. Known-law forecasts and allocations are also close, but we have not registered numerical equivalence margins, so the result is not called equivalence.

The daily Gaussian model does not integrate a rough spot process. Closing that gap is essential before interpreting this example as evidence about latent **spot** volatility. The Brownian Level B experiment separately confirms that finite sampling, aggregation and price noise can be isolated numerically. This provides a workable path to a controlled extension without expanding the model list.

## A feasible complete research paper

Keep one source-grounded rough spot DGP, a two-factor diffusion and the fixed flexible diffusion control; study a small prespecified observation grid, with transparent feasible baselines and comparable noise-aware fits. First replicate a relevant estimator's finite-sample behavior. Then report calibrated classification power, paired forecast loss and risk sensitivity as separate panels, with a small documented equity application. A rigorous negative or inconclusive result is acceptable if the precision is informative.

The public SPY example is useful for learning the data pipeline but not yet a main sample. It has only 750 development observations, six missing early-close sessions and unresolved RQ units/session counts. VOLARE currently requires an account; the identified official author data archive returned 403 locally. These problems do not block simulation work, but they do block empirical noise calibration and the original 1250-day rolling contest. The final 2020-2025 test remains unopened.

Before publication, reconcile journal/preprint versions, inspect remaining supplementary code/data rights, resolve the source-data definitions, validate the rough spot-to-IV mapping and calibrate inference. The user has reclassified this as independent research, so the original bachelor-thesis feasibility/registration question is retired. No publication readiness, supervision or registration is implied by this memo.
