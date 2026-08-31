"""
Tests for quality scoring, reporting, and CLI demo execution in QMCert.
"""

import os
import tempfile
import pytest
from qmcert.core.scoring import assess_qm_quality
from qmcert.core.thermo import ThermochemistryData
from qmcert.reporters.plot_generator import generate_qm_figures
from qmcert.reporters.manuscript_prep import generate_qm_manuscript_assets
from qmcert.reporters.html_report import generate_qm_html_report
from qmcert.cli import run_demo


def test_full_qm_validation_pipeline():
    meta = {
        "engine": "ORCA",
        "version": "5.0.4",
        "functional": "B3LYP",
        "basis_set": "def2-TZVP",
        "dispersion": "D3BJ",
        "solvent_model": "Gas Phase",
        "charge": 0,
        "multiplicity": 1
    }
    freqs = [120.0, 450.0, 1200.0, 3050.0]
    intens = [10.0, 40.0, 80.0, 100.0]
    
    thermo = ThermochemistryData(
        temperature_k=298.15,
        pressure_atm=1.0,
        zpve_hartree=0.085,
        thermal_energy_hartree=-154.20,
        enthalpy_hartree=-154.19,
        gibbs_free_energy_hartree=-154.24,
        entropy_cal_mol_k=95.4,
        quasi_rrho_gibbs_hartree=None,
        quasi_rrho_entropy_cal_mol_k=None
    )
    
    report = assess_qm_quality(
        metadata=meta,
        scf_converged=True,
        n_scf_cycles=12,
        opt_converged=True,
        n_opt_steps=8,
        frequencies=freqs,
        intensities=intens,
        expected_point_type="MINIMUM",
        multiplicity=1,
        s2_calculated=0.0,
        homo_ev=-6.8,
        lumo_ev=-1.2,
        thermochemistry=thermo
    )
    
    assert report.overall_status == "PASS"
    assert report.frequency_result.point_type == "LOCAL_MINIMUM"
    assert report.scf_result["status"] == "PASS"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Plot generation
        plots = generate_qm_figures(report, tmpdir, formats=["png", "svg"])
        assert len(plots) > 0
        for p in plots:
            assert os.path.exists(p)
            
        # Manuscript assets
        assets = generate_qm_manuscript_assets(report, tmpdir)
        assert os.path.exists(assets["summary_csv"])
        assert os.path.exists(assets["summary_tex"])
        assert os.path.exists(assets["methods_text"])
        assert os.path.exists(assets["citation_bib"])
        
        # HTML report
        html_p = os.path.join(tmpdir, "report.html")
        generate_qm_html_report(report, html_p, methods_text="Sample methods", citation_bib="@software{}")
        assert os.path.exists(html_p)
        assert os.path.getsize(html_p) > 500


def test_cli_demo_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_demo(output_dir=tmpdir)
        assert os.path.exists(os.path.join(tmpdir, "report.html"))
        assert os.path.exists(os.path.join(tmpdir, "qmcert_summary_table.csv"))
        assert os.path.exists(os.path.join(tmpdir, "citation.bib"))
