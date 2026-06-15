# FGA RFpeptides Route Changelog 2026-06-15

Status: process adjustment after boss review.

## Summary

The RFpeptides article-style route keeps the existing Stage -1 target-site
rediscovery logic, then adds an optional fpocket cross-check as supplementary
pocket/groove evidence.

fpocket is not a replacement for the existing scoring logic and is not a final
pass/fail gate.

## What Changed

- `scripts/18_discover_rfpeptides_target_sites.py`
  - Keeps FreeSASA/RSA exposure logic.
  - Keeps geometry, occlusion, chemical-anchor, and `site_quality_tier` logic.
  - Adds optional fpocket native-context cross-check.
  - Runs fpocket on the full native cleaned PDB, not Stage 0 crop PDBs.
  - Writes raw fpocket outputs to `00_site_discovery/fpocket_native_context/`.
  - Adds fpocket support fields to candidate CSVs and quality review markdown.
  - Handles missing or failed fpocket runs without failing Stage -1.

- `scripts/19_prepare_rfpeptides_article_inputs.py`
  - Prepares Stage 0 target crops, renumbering maps, site-residue tables, and
    hotspot files for reviewed high/medium sites.
  - Does not run RFpeptides generation.

- `scripts/20_make_rfpeptides_article_jobs.py`
  - Prepares the Stage 1 RFpeptides command table and run script for the
    current RFpep_Site_2 pilot scope.
  - Keeps full RFpeptides parameters for a small pilot rather than reducing
    required constraints.
  - Avoids conda activation failure by enabling `set -u` after conda activation.

## New Stage -1 fpocket Options

```text
--enable-fpocket
--fpocket-bin fpocket
--fpocket-distance-strong 6.0
--fpocket-distance-moderate 10.0
--fpocket-distance-weak 12.0
```

## fpocket Status Values

```text
not_run: fpocket cross-check was not requested
not_available: fpocket executable was not available; Stage -1 continues
failed: fpocket ran or launched unsuccessfully; Stage -1 continues
completed: fpocket completed and parsed pocket evidence was attached
```

## fpocket Support Values

```text
strong_support: pocket distance to hotspot <= 6 A
moderate_support: pocket distance to hotspot <= 10 A, or pocket distance to site <= 6 A
weak_support: pocket distance to site <= 12 A
no_nearby_pocket: no nearby pocket/groove was detected
not_evaluated: fpocket was not run, unavailable, or failed
```

## Recommended Stage -1 Command

```bash
cd /mnt/c/SH/fga_cyclic_peptide_design

./.conda/fga-cyclic-design/python.exe scripts/18_discover_rfpeptides_target_sites.py \
  --config config/project.yaml \
  --output-root results/rfpeptides_article_route_clean_20260615_fpocket \
  --max-candidates 100 \
  --propose-sites 10 \
  --hotspots-per-site 4 \
  --rsa-surface-threshold 0.20 \
  --proposal-max-uniprot-overlap-fraction 0.20 \
  --proposal-min-uniprot-center-distance 25 \
  --proposal-min-center-distance 18 \
  --enable-fpocket \
  --fpocket-bin fpocket
```

If fpocket is not installed on the current machine, the script records
`fpocket_status=not_available` and still writes the original Stage -1 outputs.

## Interpretation Rule

fpocket support may help prioritize manual PyMOL review, especially for
pocket/groove-like sites near selected hotspots. It must not be used as a hard
reject condition and does not change `site_quality_tier`.
