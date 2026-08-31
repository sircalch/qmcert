"""
Tests for vibrational frequency analysis and stationary point certification.
"""

import numpy as np
import pytest
from qmcert.core.frequencies import classify_stationary_point, simulate_ir_spectrum


def test_classify_minimum():
    # 0 imaginary modes -> Local minimum
    freqs = [120.5, 350.2, 890.1, 1450.0, 3050.2]
    res = classify_stationary_point(freqs, expected_type="MINIMUM")
    assert res.status == "PASS"
    assert res.point_type == "LOCAL_MINIMUM"
    assert res.n_imaginary == 0


def test_classify_transition_state():
    # 1 imaginary mode (-450.0 cm^-1) -> Valid TS
    freqs = [-450.0, 150.2, 420.1, 1200.0]
    res = classify_stationary_point(freqs, expected_type="TRANSITION_STATE")
    assert res.status == "PASS"
    assert res.point_type == "TRANSITION_STATE"
    assert res.n_imaginary == 1
    assert res.imaginary_frequencies[0] == -450.0


def test_classify_false_minimum_with_imaginary_mode():
    # Tested for MINIMUM but has 1 imaginary mode -> FAIL
    freqs = [-122.7, 85.0, 240.1, 1500.0]
    res = classify_stationary_point(freqs, expected_type="MINIMUM")
    assert res.status == "FAIL"
    assert res.n_imaginary == 1
    assert "not a confirmed local minimum" in res.diagnostic_message


def test_simulate_ir_spectrum():
    freqs = [1000.0, 1500.0, 3000.0]
    intensities = [50.0, 100.0, 20.0]
    
    wn, abs_spec = simulate_ir_spectrum(freqs, intensities=intensities)
    assert len(wn) == 2000
    assert len(abs_spec) == 2000
    assert np.isclose(np.max(abs_spec), 100.0)
