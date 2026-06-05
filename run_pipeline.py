from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


FULL_STEPS = [
    "00_check_environment.py",
    "01_extract_fga_sequence.py",
    "02_prepare_fga_regions.py",
    "03_prepare_structures.py",
    "04_map_fga_structure.py",
    "05_select_surface_patches.py",
    "06_make_design_jobs.py",
    "07_collect_raw_designs.py",
    "08_filter_sequences.py",
    "09_prepare_complex_prediction_jobs.py",
    "10_score_complex_predictions.py",
    "11_negative_screen.py",
    "12_rank_candidates.py",
    "13_export_final_report.py",
]

PREPARE_STEPS = [
    "00_check_environment.py",
    "01_extract_fga_sequence.py",
    "02_prepare_fga_regions.py",
    "03_prepare_structures.py",
    "04_map_fga_structure.py",
    "05_select_surface_patches.py",
    "06_make_design_jobs.py",
    "13_export_final_report.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="FGA Cys-Cys 环肽设计 pipeline 总入口。")
    parser.add_argument("--config", default="config/project.yaml")
    parser.add_argument("--mode", choices=["prepare", "full"], default="full")
    args = parser.parse_args()

    steps = PREPARE_STEPS if args.mode == "prepare" else FULL_STEPS
    for step in steps:
        script = ROOT / "scripts" / step
        cmd = [sys.executable, str(script), "--config", args.config]
        print(f"\n[run_pipeline] Running {step}")
        result = subprocess.run(cmd, cwd=ROOT)
        if result.returncode != 0:
            print(f"[run_pipeline] Step failed: {step} exit={result.returncode}", file=sys.stderr)
            return result.returncode
    print("\n[run_pipeline] Pipeline completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
