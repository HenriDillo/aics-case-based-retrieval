# Purpose pool feasibility handling

Recorded 20 October 2026 at 20:30 PHT, before any purpose-pool outcome evaluation. This is an execution-handling addendum to the post-failure decision, not a new scientific setting or an attempt to improve results.

An input-only count of all 155 training folds found one infeasible fold: seed 51024, fold 0 has five assistive-device training records. Excluding the query applicant leaves only four references, so fixed k = 5 cannot be satisfied for those queries. The primary dataset and the other 29 replication datasets satisfy this count check.

Keep all inputs, seeds, folds, exclusions and k unchanged. Record the whole 51024 purpose-pool replication as infeasible for every condition. Do not silently drop its queries, substitute a seed, enlarge its purpose pool or reduce k. Run the primary test and all feasible replications, retaining the failure report. Do not compute a replacement 29-set noise floor or claim that the fixed thirty-set evidence standard passed. Report that standard as unavailable, and report the primary paired test separately. The corrected type-pool comparison is unaffected.

The runner change only adds explicit infeasibility reporting and suppresses an invalid incomplete-set evidence claim. The distance, generator, objective, optimizer and all scientific settings are unchanged. The initial runner and initial frozen hashes are preserved as `runner-frozen-v01.py` and `code-frozen-before-evaluation.json` in the new run directory. A separate updated runner hash is recorded before the purpose comparison.
