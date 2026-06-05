# FGA ColabDesign Guardrails - 2026-06-03

This note records the major fix after discovering that earlier ColabDesign runs were not producing optimized peptide sequences.

## What Went Wrong

- Earlier batches used `GREEDY_ITERS=0`.
- The model ran, but exported hard peptide sequences did not change.
- All 800 collected candidates had `core_sequence == init_sequence`.
- Those results are not valid optimized production candidates.
- A later semigreedy test with `GREEDY_ITERS=32` failed because the wrapper used `add_seq=True`.
- In ColabDesign, `add_seq=True` adds a huge sequence bias. This both locks the initial sequence and creates a 3D bias shape that semigreedy cannot broadcast back to `(L,20)`.

## What Was Changed

- `scripts/external/run_colabdesign_cyclic_binder.py`
  - Added salted random initialization through `--init_seed_salt`.
  - Candidate notes now include `init_sequence`, `init_seed_salt`, and `final_sequence_changed`.
  - Run summaries include `num_changed_sequences`.
  - Removed `add_seq=True` and global `rm_aa="C"`.
  - Added explicit Cys-Cys position bias: terminal Cys residues are locked, internal Cys is disallowed, internal non-Cys positions remain designable.

- `scripts/06_make_design_jobs.py`
  - Generated ColabDesign job scripts now default to `GREEDY_ITERS=32`.
  - Generated jobs pass `--init_seed_salt "$INIT_SEED_SALT"`.

- `scripts/external/run_colabdesign_safe_batch.sh`
  - Default `GREEDY_ITERS` changed from 0 to 32.

- `scripts/external/run_colabdesign_chunk_batch.sh`
  - Default `GREEDY_ITERS` changed from 0 to 32.

- `scripts/07_collect_raw_designs.py`
  - Skips unoptimized ColabDesign candidates.
  - Writes skipped records to `results/raw_designs/FGA_unoptimized_candidates_skipped.csv`.

- `scripts/10_score_complex_predictions.py`
  - Skips manual complex score rows whose `peptide_id` is not found in hard-filtered candidates.

- `scripts/12_rank_candidates.py` and `scripts/ranking.py`
  - Missing negative screen is no longer treated as pass.

## Current State After Guardrails

Old unoptimized results are quarantined:

```text
FGA_raw_candidates.csv rows=0
FGA_unoptimized_candidates_skipped.csv rows=800
FGA_hard_filtered_candidates.csv rows=0
complex_prediction_jobs.csv rows=0
FGA_top50_candidates.csv rows=0
FGA_top10_synthesis_priority.csv rows=0
```

## Required Validation Before Scaling

A tiny debug validation after the `add_seq=True` fix passed:

```text
init  CRYDRGAIKGSIYC
core  CRYDRGAGKGSIYC
changed True
```

The failed partial `seed30000/30005/30010/30015` outputs and the debug `seed39999` output were removed.

Run a small batch first:

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

export GPU_LIST=0,1
export DESIGNS_TOTAL_PER_JOB=20
export DESIGNS_PER_PROCESS=5
export MAX_RETRIES=2
export PSSM_ITERS=80
export GREEDY_ITERS=32
export START_SEED_BASE=30000
export INIT_MODE=random

bash scripts/external/run_colabdesign_chunk_batch.sh \
  Patch_A_L14_colabdesign \
  Patch_B_L14_colabdesign \
  Patch_C_L14_colabdesign
```

Then verify:

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

python3 - <<'PY'
import csv, glob, json
rows = []
for p in glob.glob("results/raw_designs/colabdesign_outputs/Patch_*_L14_colabdesign_chunk_seed300*_n005/candidates.csv"):
    for r in csv.DictReader(open(p, newline="")):
        n = json.loads(r["notes"])
        rows.append((r["patch_id"], r["core_sequence"], n["init_sequence"], n.get("final_sequence_changed")))
print("rows:", len(rows))
print("unique final seq:", len({r[1] for r in rows}))
print("changed:", sum(bool(r[3]) for r in rows))
for r in rows[:10]:
    print(r)
PY
```

Only scale up if `changed > 0`. If `changed == 0`, stop and debug before any larger run.

## Scientific Integrity Rule

Do not present any peptide as final unless it has passed real generation, hard sequence filtering, complex prediction/scoring, negative screening, and final ranking.

## 2026-06-03 Terminal Cys Mutation Lock

The previous Cys-Cys constraint used a position-specific bias at `model.restart(...)`.
That bias strongly steers logits and mutation sampling, but it does not by itself
prevent ColabDesign semigreedy from selecting a terminal position and mutating it.

Fix applied:

- `scripts/external/run_colabdesign_cyclic_binder.py`
  - Adds `lock_terminal_cys_mutations(...)`.
  - Wraps `model._mutate` so every semigreedy mutant is restored to terminal Cys
    before AlphaFold prediction/scoring.
  - Writes `terminal_cys_mutation_lock: true` into candidate notes and run summary.

Validation:

```text
job_id: Patch_B_L14_colabdesign_chunk_seed61003_n003
num_designs_requested: 3
num_changed_sequences: 3
num_scheme_A_candidates: 3
terminal_cys_mutation_lock: true
```

The low-iteration validation output directory was removed after checking so it
cannot be collected into production candidates.

Post-fix cleanup:

```text
Moved 172 pre-lock output directories from:
results/raw_designs/colabdesign_outputs

to:
results/raw_designs/archived_pre_terminal_lock_20260603
```

Production implication:

- Do not use older outputs produced before this lock as production candidates.
- Re-run validation/production after this fix.
- Keep `GREEDY_ITERS > 0`; otherwise semigreedy mutation locking is not exercised.

## Current Agreed Post-Fix Run Scope

The first clean post-fix validation should use A/B only, four peptide lengths
each:

```bash
Patch_A_L12_colabdesign
Patch_A_L14_colabdesign
Patch_A_L16_colabdesign
Patch_A_L18_colabdesign
Patch_B_L12_colabdesign
Patch_B_L14_colabdesign
Patch_B_L16_colabdesign
Patch_B_L18_colabdesign
```

Validation parameters:

```bash
GPU_LIST=0,1
DESIGNS_TOTAL_PER_JOB=20
DESIGNS_PER_PROCESS=5
MAX_RETRIES=2
PSSM_ITERS=80
GREEDY_ITERS=32
START_SEED_BASE=0
```

If validation is normal, scale the same 8 jobs to:

```bash
DESIGNS_TOTAL_PER_JOB=100
```

Patch_C is not part of the first clean post-fix production scope. Add it only
after A/B results justify expanding.

## Post-Fix Validation Result Before Full Production

The first clean post-fix validation run was stopped intentionally after enough
outputs were available for inspection.

Result:

```text
Complete output directories: 18
Incomplete directories from intentional stop: 2
Requested designs in complete directories: 90
Changed sequences: 90
Scheme-A Cys-Cys candidates: 90
Rejected non-scheme-A rows: 0
terminal_cys_mutation_lock: true for all 90 accepted rows
Bad Cys-Cys scheme rows: 0
Unique sequences: 90
Duplicate sequences: 0
```

Completed validation coverage:

```text
Patch_A L12: 20/20
Patch_A L14: 20/20
Patch_A L16: 20/20
Patch_A L18: 20/20
Patch_B L12: 10/20 before intentional stop
```

The validation outputs were archived and active output was cleared:

```text
results/raw_designs/archived_post_lock_validation_20260603_171231
results/raw_designs/colabdesign_outputs is empty
```

This validation is sufficient to proceed to full production generation with the
same A/B eight-job scope.
