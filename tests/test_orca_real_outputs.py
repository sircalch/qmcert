"""
Regression tests on real ORCA 6.1.1 outputs (B3LYP-D3BJ/def2-SVP), inputs in validation/orca_runs/.
Reference values were read directly from the output sections.
"""
import os

import pytest

from qmcert.parsers.orca import parse_orca_output

DATA = os.path.join(os.path.dirname(__file__), "data")


def load(name):
    return parse_orca_output(os.path.join(DATA, name))


def test_planar_ammonia_is_a_first_order_saddle_point():
    d = load("nh3_planar_ts.out")
    assert d["frequencies"] == pytest.approx([-830.27, 1514.10, 1514.39, 3603.10, 3819.36, 3819.76])
    assert sum(f < 0 for f in d["frequencies"]) == 1
    # ORCA omits the imaginary mode from the IR table; intensities stay aligned with frequencies
    assert d["intensities"] == pytest.approx([0.0, 30.52, 30.32, 0.0, 36.65, 36.75])
    assert d["opt_converged"] is True
    assert d["homo_ev"] == pytest.approx(-5.8037)
    assert d["lumo_ev"] == pytest.approx(1.7694)


def test_water_minimum_frontier_orbitals_and_thermochemistry():
    d = load("h2o_min.out")
    assert d["frequencies"] == pytest.approx([1637.68, 3786.99, 3881.94])
    assert d["homo_ev"] == pytest.approx(-7.8409)
    assert d["lumo_ev"] == pytest.approx(1.2983)
    th = d["thermochemistry"]
    assert th.zpve_hartree == pytest.approx(0.02120201)
    assert th.gibbs_free_energy_hartree == pytest.approx(-76.31830552)
    # enthalpy = thermal energy + kT
    assert th.enthalpy_hartree - th.thermal_energy_hartree == pytest.approx(0.00094421, abs=2e-6)


def test_unrestricted_radical_uses_final_s2_and_both_spin_tables():
    d = load("ch3_radical.out")
    assert d["metadata"]["multiplicity"] == 2
    assert d["s2_calculated"] == pytest.approx(0.753698)   # final SCF, not the first geometry
    assert d["homo_ev"] == pytest.approx(-6.2291)
    assert d["lumo_ev"] == pytest.approx(-1.5630)
    assert d["n_scf_cycles"] == 3


def test_triplet_oxygen_single_point():
    d = load("o2_triplet.out")
    assert d["metadata"]["multiplicity"] == 3
    assert d["s2_calculated"] == pytest.approx(2.006549)
    assert d["frequencies"] is None
    assert d["opt_converged"] is None
    assert d["final_energy_hartree"] == pytest.approx(-150.145307, abs=1e-6)
