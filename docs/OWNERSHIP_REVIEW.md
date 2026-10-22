# Explain and extend the study

Software/analysis completion is separate from human review. Martin has not been recorded as independently verifying every AI-assisted component. Before presenting the project as personal research in an interview, work through these questions and record your own answers in COMPREHENSION_LOG.md. The assistant must not fabricate those answers.

1. Define spot variance, daily integrated variance and realized variance. Why need their log-variogram slopes not agree, even if all are measured without software errors?
2. Derive E[RV|v]=grid IV without price noise, and the additional 2M eta-squared term for independent endpoint log-price noise. Explain why nested returns must be summed before squaring.
3. Explain the OU local exponent 1/2 and the difference between a local limit and an OLS slope over lags 1–10. Why can the integrated-variance slope exceed 1/2 without the OU model changing?
4. Derive RQ=M/3 sum(r^4) under constant Gaussian variance. Explain what qhat describes and why it is not automatically log-RV observation-error variance or microstructure-noise variance.
5. Explain why independent paths, rather than daily observations or overlapping lags, are the Monte Carlo replication unit.
6. Predict the effects of increasing price noise versus sampling every 30 minutes. Then edit a separate config, run a small experiment and compare with your prediction without changing the frozen study results.
7. Explain what the three covariance checks and step-doubling diagnostic validate, and what they leave unresolved. Why do 54 passing tests not establish that real volatility is smooth or rough?
8. Explain the unresolved SPY source discrepancy and why changing filters to match a desired answer would weaken the study.

Suggested CV label before this review: ongoing independent project with AI-assisted implementation. After review, describe the reproducible study and your actual contribution, without claiming publication, a novel estimator, a fitted trading strategy or market latent-H identification.

## Source audit and risk-input case study

Explain: (1) why identical literal sale-condition filters need not preserve identical information; (2) why the condition B has tape-dependent meanings; (3) why an outer join and nullable warnings are needed; (4) why a long sequence of differing risk inputs can be one persistent episode rather than independent shocks; (5) when end-of-day RV can enter the next-session EWMA weight; (6) why a stable five-minute result does not certify integrated variance. Predict the RV/RQ scaling when returns change from decimal to percent units. AI has not completed this review for Martin.
