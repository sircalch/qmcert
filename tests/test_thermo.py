"""
Tests for thermochemistry and Grimme quasi-RRHO corrections.
"""

import pytest
from qmcert.core.thermo import calculate_quasi_rrho_corrections


def test_quasi_rrho_corrections():
    # Mix of low-frequency (< 100 cm^-1) and high-frequency modes
    freqs = [35.0, 75.0, 150.0, 500.0, 1200.0, 3000.0]
    res = calculate_quasi_rrho_corrections(freqs, temperature=298.15, cutoff_wavenumber=100.0)
    
    assert res["n_low_freq_modes"] == 2
    assert res["s_harmonic_cal_mol_k"] > 0
    assert res["s_quasi_rrho_cal_mol_k"] > 0
    # Quasi-RRHO should produce a small delta G correction
    assert isinstance(res["delta_g_quasi_rrho_hartree"], float)
