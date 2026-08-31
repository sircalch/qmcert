"""
Tests for spin contamination and orbital gap analysis.
"""

import pytest
from qmcert.core.wavefunction import evaluate_spin_contamination, evaluate_orbital_gap


def test_spin_contamination_doublet():
    # Doublet: M=2, S=0.5 -> S(S+1) = 0.75
    # Calculated = 0.76 -> Error = 1.33% -> PASS
    res_pass = evaluate_spin_contamination(multiplicity=2, s2_calculated=0.76)
    assert res_pass.status == "PASS"
    assert res_pass.contamination_pct < 5.0
    
    # Calculated = 0.95 -> Severe contamination -> FAIL
    res_fail = evaluate_spin_contamination(multiplicity=2, s2_calculated=0.95)
    assert res_fail.status == "FAIL"
    assert res_fail.contamination_pct > 10.0


def test_orbital_gap():
    res_pass = evaluate_orbital_gap(homo_energy=-7.0, lumo_energy=-1.5, unit="eV")
    assert res_pass["status"] == "PASS"
    assert res_pass["gap_ev"] == 5.5
    
    res_inverted = evaluate_orbital_gap(homo_energy=-2.0, lumo_energy=-4.0, unit="eV")
    assert res_inverted["status"] == "FAIL"
