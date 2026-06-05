from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from sequence_filters import filter_candidate_sequence


def test_valid_cys_cys_candidate_passes() -> None:
    result = filter_candidate_sequence("CAGTSNQPLC")
    assert result["sequence_filter_pass"] is True


def test_non_c_start_fails() -> None:
    result = filter_candidate_sequence("AAGTSNQPLC")
    assert result["starts_with_cys"] is False
    assert result["sequence_filter_pass"] is False


def test_non_c_end_fails() -> None:
    result = filter_candidate_sequence("CAGTSNQPLA")
    assert result["ends_with_cys"] is False
    assert result["sequence_filter_pass"] is False


def test_internal_cys_fails() -> None:
    result = filter_candidate_sequence("CAGTCNQPLC")
    assert result["internal_cys_count"] == 1
    assert result["sequence_filter_pass"] is False


def test_too_short_fails() -> None:
    result = filter_candidate_sequence("CAGTPLC")
    assert result["core_length_pass"] is False
    assert result["sequence_filter_pass"] is False


def test_too_long_fails() -> None:
    result = filter_candidate_sequence("CAGTSNQPLAGTSNQPLLC")
    assert result["core_length_pass"] is False
    assert result["sequence_filter_pass"] is False


def test_high_charge_fails() -> None:
    result = filter_candidate_sequence("CKKKKQTSLC")
    assert result["charge_pass"] is False
    assert result["sequence_filter_pass"] is False


def test_long_hydrophobic_run_fails() -> None:
    result = filter_candidate_sequence("CAVILMFAGC")
    assert result["hydrophobicity_pass"] is False
    assert result["sequence_filter_pass"] is False
