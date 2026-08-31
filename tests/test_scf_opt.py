"""
Tests for SCF and geometry optimization convergence criteria.
"""

import pytest
from qmcert.core.scf_opt import evaluate_scf_convergence, evaluate_geometry_optimization


def test_scf_convergence():
    res_pass = evaluate_scf_convergence(True, 15, energy_diff=1e-8)
    assert res_pass["status"] == "PASS"
    
    res_fail = evaluate_scf_convergence(False, 128)
    assert res_fail["status"] == "FAIL"


def test_opt_convergence():
    res_pass = evaluate_geometry_optimization(True, 12, energies_trajectory=[-100.0, -100.05, -100.052])
    assert res_pass["status"] == "PASS"
    assert res_pass["total_energy_change_hartree"] < 0
    
    res_fail = evaluate_geometry_optimization(False, 50)
    assert res_fail["status"] == "FAIL"
