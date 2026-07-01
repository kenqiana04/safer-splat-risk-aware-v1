# Publish Notes

This repository is a clean publish snapshot for the Risk-Aware V1 SAFER-Splat reproduction work.

## Source

- Upstream code base: `chengine/safer-splat`
- Local source commit used for this snapshot: `adfeba258f34aa949011638b54243cfb595568d2`
- Added reproduction work lives under `work/risk_aware_cbf/` and `reproduction/`.

## Included

- Official SAFER-Splat source files needed by the wrappers.
- Risk-Aware V0/V1 wrapper scripts and analysis scripts.
- Markdown reports, summary CSVs, metrics JSONs, plots, and lightweight logs.
- Flight and stonehenge validation summaries.

## Excluded

The following generated artifacts are intentionally excluded because they are too large for normal GitHub storage or are derived from reproducible runs:

- `data/`
- `outputs/`
- model checkpoints such as `*.ckpt`, `*.pt`, `*.pth`
- full Gaussian attribute tables such as `flight_gaussian_attributes.csv`
- full risk score tables such as `flight_risk_score_table_v0.csv`
- per-step trajectory CSVs
- active-constraint detailed CSVs
- Python cache files

The reports and summary files in `work/risk_aware_cbf/` record the key metrics needed to inspect the experiments without committing the large raw artifacts.

## Claim Boundary

The reported `min_safety_h` values are official SAFER-Splat safety-function values, not meter clearance.
The Risk-Aware V1 work here is a wrapper-level prototype and does not claim a new CBF theorem.
