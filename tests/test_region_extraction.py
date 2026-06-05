from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common import DEFAULT_CONFIG
from region_utils import build_region_rows, fasta_header


def test_region_lengths_are_correct() -> None:
    sequence = "M" * 866
    rows = {row["region_name"]: row for row in build_region_rows(sequence, DEFAULT_CONFIG)}
    assert rows["full_length_1_866"]["length"] == 866
    assert rows["extracellular_20_866"]["length"] == 847
    assert rows["chain_36_866"]["length"] == 831


def test_region_slices_are_one_based_inclusive() -> None:
    sequence = "".join(chr(ord("A") + (i % 20)) for i in range(866))
    rows = {row["region_name"]: row for row in build_region_rows(sequence, DEFAULT_CONFIG)}
    assert rows["extracellular_20_866"]["sequence"] == sequence[19:866]
    assert rows["chain_36_866"]["sequence"] == sequence[35:866]


def test_fasta_headers_match_task() -> None:
    assert fasta_header("full_length_1_866", DEFAULT_CONFIG) == "FGA_P02671_full_length_1_866"
    assert fasta_header("extracellular_20_866", DEFAULT_CONFIG) == "FGA_P02671_extracellular_20_866"
    assert fasta_header("chain_36_866", DEFAULT_CONFIG) == "FGA_P02671_chain_36_866"
