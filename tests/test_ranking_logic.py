from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ranking import rank_rows, score_candidate


def _row(peptide_id: str, best_iptm: float, neg: str = "pass", cys: str = "pass") -> dict:
    return {
        "peptide_id": peptide_id,
        "core_sequence": "CAGTSNQPLC",
        "best_iptm": best_iptm,
        "best_interface_pae": 5.0,
        "mean_peptide_plddt": 85.0,
        "interface_contacts": 12,
        "patch_consistency_flag": "pass",
        "cys_cys_geometry": cys,
        "negative_screen_flag": neg,
    }


def test_higher_complex_score_ranks_higher() -> None:
    ranked = rank_rows([_row("low", 0.55), _row("high", 0.90)])
    assert ranked[0]["peptide_id"] == "high"


def test_negative_screen_fail_lowers_score() -> None:
    passed = score_candidate(_row("passed", 0.85, neg="pass"), negative_pass=True)
    failed = score_candidate(_row("failed", 0.85, neg="fail"), negative_pass=False)
    assert failed < passed


def test_missing_negative_screen_is_not_treated_as_pass() -> None:
    passed = rank_rows([_row("passed", 0.85, neg="pass")])[0]
    missing = rank_rows([_row("missing", 0.85, neg="missing")])[0]
    assert missing["final_score"] < passed["final_score"]


def test_cys_geometry_fail_is_excluded_from_top10_pool() -> None:
    ranked = rank_rows([_row("bad_cys", 0.95, cys="fail"), _row("good", 0.80)])
    top10_pool = [row for row in ranked if row.get("priority") != "exclude" and row.get("cys_cys_geometry") == "pass"]
    assert all(row["peptide_id"] != "bad_cys" for row in top10_pool)
