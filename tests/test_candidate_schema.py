from __future__ import annotations

import sys
import importlib.util
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common import DEFAULT_CONFIG
from ranking import FINAL_COLUMNS


def _load_collect_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "07_collect_raw_designs.py"
    spec = importlib.util.spec_from_file_location("collect_raw_designs", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_final_candidate_schema_contains_required_fields() -> None:
    required = {
        "peptide_id",
        "target",
        "target_uniprot",
        "target_patch",
        "uniprot_region",
        "hotspot_residues",
        "core_sequence",
        "core_length",
        "final_synthesis_format",
        "cyclization",
        "mean_iptm",
        "best_iptm",
        "mean_interface_pae",
        "best_interface_pae",
        "peptide_plddt",
        "interface_contacts",
        "pose_consistency_rmsd",
        "cys_cys_geometry",
        "net_charge",
        "hydrophobicity_flag",
        "sequence_filter_pass",
        "negative_screen_flag",
        "final_score",
        "priority",
        "notes",
    }
    assert required.issubset(set(FINAL_COLUMNS))


def test_final_synthesis_format_construction() -> None:
    prefix = DEFAULT_CONFIG["peptide_design"]["final_format_prefix"]
    suffix = DEFAULT_CONFIG["peptide_design"]["final_format_suffix"]
    core = "CAGTSNQPLC"
    assert f"{prefix}{core}{suffix}" == "Biotin-PEG4-GSG-CAGTSNQPLC-NH2"


def test_rejected_colabdesign_csv_is_not_collected_as_candidate() -> None:
    collect = _load_collect_module()
    assert collect._is_candidate_csv(Path("candidates.csv")) is True
    assert collect._is_candidate_csv(Path("rejected_non_scheme_A.csv")) is False


def test_unoptimized_colabdesign_candidate_is_rejected() -> None:
    collect = _load_collect_module()
    record = {
        "method": "ColabDesign-cyclic-binder",
        "notes": json.dumps(
            {
                "init_sequence": "CAGTSNQPLC",
                "final_sequence_changed": False,
            }
        ),
    }
    assert collect._unoptimized_colabdesign_reason(record, "CAGTSNQPLC") == "final_sequence_changed=false"


def test_changed_colabdesign_candidate_is_kept() -> None:
    collect = _load_collect_module()
    record = {
        "method": "ColabDesign-cyclic-binder",
        "notes": json.dumps(
            {
                "init_sequence": "CAGTSNQPLC",
                "final_sequence_changed": True,
            }
        ),
    }
    assert collect._unoptimized_colabdesign_reason(record, "CAGTANQPLC") == ""
