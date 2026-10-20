# Reproduce the post failure amendments

This runbook supersedes the earlier wait-for-adviser execution restriction under Henri’s explicit 20 October 2026 instruction. It does not claim Ma’am Grace’s agreement. Historical runbooks, drafts and results remain preserved.

The new run is `research/generated/post-test-correction-2026-10-20-v1`. Use the new versioned Chapter 4 file `chapter-4-2026-10-20-v02-post-test.md` after finalization. The current manuscript source is Chapters 1–3 v27, 20 October 2026. The prototype still uses the historical equal-weight type-pool CSV; these are separate offline research comparisons.

## Inputs and checks

Use Python 3.12.10 and the existing pinned backend dependencies. Preserve the original source bundle and existing reconciled primary plus seeds 51001–51030. The accompanying evidence archive contains corrected datasets and manifests; the earlier full archive contains the historical inputs and runs. Restore them under their recorded `research/generated` paths when reproducing from a fresh checkout. The original primary base is reconstructed by `research.reconciled.build(output)`; each replication is reconstructed with `research.reconciled.build(output, master_seed)` using the recorded seed. Compare CSV hashes against the preserved manifests before proceeding.

First run the actual vendor `research.vendor.amount_rule_v2.check_pairs` on all four pairs in each existing condition and verify all four pairs are present. The delivered pre-correction reports record that check. Do not rely on its silent handling of absent pair members.

The corrected generator uses the shifted bounded available-field formula in `POST_TEST_DECISION_2026-10-20_v01.md`. It immediately checks all four pairs after every forty-case generation, checks reversed record order, complete-score identity, p00 amount identity, unchanged non-amount values, cost/floor/cap constraints and CSV round trips. Generation stops on a failure. All 31 corrected sets must pass before evaluation.

## Execute in order

Run from the repository root. Use a separate checkout and a new, absent output directory for a genuinely fresh reproduction; change the runner’s `DEST` only to that new directory. Never delete or overwrite the delivered run.

```powershell
.venv/Scripts/python.exe -m research.post_test_runner_20261020 --phase prepare
.venv/Scripts/python.exe -m research.post_test_runner_20261020 --phase type
.venv/Scripts/python.exe -m research.post_test_runner_20261020 --phase purpose
```

Existing finished outputs are reused on a resume. The purpose phase requires the original corrected type phase to finish first. Scientific settings remain fixed: p50 main, k5, plain money, categorical duration, existing folds/seeds, 200 evaluations, shared 39 weights, four conditions and the thirty-replication evidence standard. Earlier transformation selection is historical and is not rerun.

The first delivered execution used the initial frozen runner for type-pool comparisons. The preserved `runner-frozen-v01.py` reproduces that execution. Before purpose outcomes were evaluated, an input-only audit identified an infeasible purpose-pool replication. The updated runner adds explicit reporting of that condition; it does not change any successful fit or scientific setting. Both hashes and the dated feasibility addendum accompany the run.

## Infeasibility must remain visible

Seed 51024, training fold 0 contains five assistive-device records. After excluding the query applicant, four eligible references remain, so fixed k5 is infeasible. Record that entire purpose-pool replication as unavailable for every condition. Do not drop queries, replace a seed, enlarge the pool, change a fold or reduce k. The other 29 replication runs remain available. Do not replace the fixed thirty-set noise floor with a 29-set calculation. The full purpose-pool weight-evidence standard is unavailable; the primary paired Wilcoxon result is reported separately.

## Reporting and review

Report the retained original failure, corrected type-pool test and corrected purpose-pool test, whatever they show. Preserve the exact post-failure disclosure in Chapter 4. Current sources must cite v27. No social worker participated, and no UAT or SUS was conducted. Chapter 5 is Rygan’s assignment, and the recommendations must not commit the team to returning to CIS.

The evidence includes every generated CSV, complete traces for successful fits, primary predictions/errors, applicant folds, timing repeats, sensitivity, infeasibility report, calibration and code hashes. Independent scalar checks compare all 320 fixed-case outcomes, and an independent SciPy check verifies all eight primary Wilcoxon p-values. The private pair key is excluded from distribution.
