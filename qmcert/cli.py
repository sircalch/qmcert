"""
Command Line Interface (CLI) for QMCert.
"""

import sys
import os
import argparse
import numpy as np

from qmcert import __version__
from qmcert.parsers.generic_qm import parse_qm_output
from qmcert.core.scoring import assess_qm_quality
from qmcert.core.thermo import ThermochemistryData
from qmcert.reporters.plot_generator import generate_qm_figures
from qmcert.reporters.manuscript_prep import generate_qm_manuscript_assets
from qmcert.reporters.html_report import generate_qm_html_report


def print_banner():
    banner = rf"""
   ____  __  __  _____          _   
  / __ \|  \/  |/ ____|        | |  
 | |  | | \  / | |     ___ _ __| |_ 
 | |  | | |\/| | |    / _ \ '__| __|
 | |__| | |  | | |___|  __/ |  | |_ 
  \___\_\_|  |_|\_____\___|_|   \__| v{__version__}

 Quantum Chemistry Quality & Reproducibility Assessment Toolkit
 Monreal-Hernández et al., 2026
"""
    print(banner)


def run_demo(output_dir: str = "qmcert_demo_output"):
    """
    Simulates a high-accuracy ORCA DFT calculation (wB97X-D3BJ/def2-TZVP, Geometry Optimization + Frequencies,
    local minimum with 0 imaginary frequencies, singlet, complete thermochemistry) and executes the certification pipeline.
    """
    print(f"\n[QMCert] Running demonstration mode...")
    os.makedirs(output_dir, exist_ok=True)
    
    metadata = {
        "engine": "ORCA",
        "version": "6.0.0",
        "functional": "wB97X-D3BJ",
        "basis_set": "def2-TZVP",
        "dispersion": "D3BJ",
        "solvent_model": "CPCM (Water)",
        "charge": 0,
        "multiplicity": 1,
        "raw_command": "! wB97X-D3BJ def2-TZVP CPCM(Water) Opt Freq"
    }
    
    # 3N-6 = 30 vibrational modes (for 12-atom molecule)
    freqs = [
        45.2, 85.0, 112.4, 156.8, 220.1, 310.5, 412.0, 520.4, 618.2, 730.0,
        845.6, 920.1, 1025.4, 1150.2, 1220.8, 1315.0, 1420.5, 1480.0, 1560.2, 1640.8,
        1720.5, 2850.1, 2920.4, 2980.0, 3010.5, 3050.2, 3100.0, 3450.2, 3600.0, 3720.4
    ]
    intensities = [
        2.5, 5.1, 12.0, 8.4, 15.2, 30.1, 45.0, 80.5, 120.0, 95.2,
        60.4, 40.1, 110.5, 180.2, 220.4, 90.1, 75.0, 140.2, 350.0, 210.4,
        450.8, 85.0, 120.4, 95.0, 45.2, 60.1, 30.0, 280.4, 190.2, 310.5
    ]
    
    thermo = ThermochemistryData(
        temperature_k=298.15,
        pressure_atm=1.0,
        zpve_hartree=0.18520,
        thermal_energy_hartree=-425.82045,
        enthalpy_hartree=-425.81951,
        gibbs_free_energy_hartree=-425.87520,
        entropy_cal_mol_k=117.21,
        quasi_rrho_gibbs_hartree=None,
        quasi_rrho_entropy_cal_mol_k=None
    )
    
    energies_traj = [-425.95000, -425.98500, -426.00200, -426.00510, -426.00565]
    
    print("  -> Performing stationary point certification, spin purity analysis, and SCF convergence check...")
    report = assess_qm_quality(
        metadata=metadata,
        scf_converged=True,
        n_scf_cycles=12,
        opt_converged=True,
        n_opt_steps=5,
        frequencies=freqs,
        intensities=intensities,
        expected_point_type="MINIMUM",
        multiplicity=1,
        s2_calculated=0.0000,
        homo_ev=-7.25,
        lumo_ev=-1.15,
        thermochemistry=thermo,
        energies_trajectory=energies_traj
    )
    
    print("  -> Generating simulated IR spectrum and optimization trajectory figures...")
    generate_qm_figures(report, output_dir)
    
    print("  -> Drafting manuscript Methods text snippet, summary LaTeX tables, and BibTeX citations...")
    assets = generate_qm_manuscript_assets(report, output_dir)
    
    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_txt = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        bib_txt = f.read()
        
    html_p = os.path.join(output_dir, "report.html")
    print(f"  -> Writing interactive report to {html_p}...")
    generate_qm_html_report(report, html_p, methods_text=methods_txt, citation_bib=bib_txt)
    
    print("\n" + "="*70)
    print(f" [RESULT] Overall Quantum Chemistry Certification: {report.overall_status}")
    print(f" [SCORE]  {report.validation_score}")
    print("="*70)
    print(f" * Method / Basis   : {report.metadata['functional']}/{report.metadata['basis_set']} ({report.metadata['engine']})")
    if report.scf_result:
        print(f" * SCF Convergence  : Converged in {report.scf_result['n_cycles']} iterations | Status: {report.scf_result['status']}")
    if report.geometry_result:
        print(f" * Geometry Opt     : Converged in {report.geometry_result['n_steps']} steps | Status: {report.geometry_result['status']}")
    if report.frequency_result:
        fr = report.frequency_result
        print(f" * Stationary Point : {fr.point_type} ({fr.n_imaginary} imag modes, lowest: {fr.lowest_frequency:.1f} cm^-1) | Status: {fr.status}")
    if report.spin_result:
        sr = report.spin_result
        print(f" * Spin <S^2>       : <S^2> = {sr.s2_calculated:.4f} (error = {sr.contamination_pct:.2f}%) | Status: {sr.status}")
    if report.orbital_result:
        print(f" * HOMO-LUMO Gap    : {report.orbital_result['gap_ev']:.2f} eV | Status: {report.orbital_result['status']}")
    if report.quasi_rrho_correction:
        qr = report.quasi_rrho_correction
        print(f" * Quasi-RRHO DeltaG: {qr['delta_g_quasi_rrho_hartree']*627.509:.3f} kcal/mol ({qr['n_low_freq_modes']} low modes)")
    print("="*70)
    print(f"\nAll outputs successfully saved to: {os.path.abspath(output_dir)}/")
    print(f"Open {os.path.abspath(html_p)} in your browser to inspect the full report.\n")


def run_assess(args):
    """
    Evaluates user-provided calculation output files.
    """
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    input_file = args.input
    if not input_file:
        print("[Error] Please specify a calculation output file with --input.", file=sys.stderr)
        sys.exit(1)
        
    print(f"\n[QMCert] Parsing quantum chemistry output from {input_file}...")
    parsed_data = parse_qm_output(input_file)
    meta = parsed_data.get("metadata", {})
    print(f"  -> Detected Engine: {meta.get('engine', 'Unknown')}, Method: {meta.get('functional', 'DFT')}/{meta.get('basis_set', 'Unknown')}")
    
    exp_point = "TRANSITION_STATE" if args.ts else "MINIMUM"
    
    print("  -> Performing quantum chemistry quality certification...")
    report = assess_qm_quality(
        metadata=meta,
        scf_converged=parsed_data.get("scf_converged", True),
        n_scf_cycles=parsed_data.get("n_scf_cycles", 15),
        opt_converged=parsed_data.get("opt_converged"),
        n_opt_steps=parsed_data.get("n_opt_steps"),
        frequencies=parsed_data.get("frequencies"),
        intensities=parsed_data.get("intensities"),
        expected_point_type=exp_point,
        multiplicity=meta.get("multiplicity", 1),
        s2_calculated=parsed_data.get("s2_calculated"),
        homo_ev=parsed_data.get("homo_ev"),
        lumo_ev=parsed_data.get("lumo_ev"),
        thermochemistry=parsed_data.get("thermochemistry"),
        energies_trajectory=parsed_data.get("energies_trajectory")
    )
    
    print("  -> Generating simulated IR spectrum and optimization curves...")
    generate_qm_figures(report, output_dir)
    
    print("  -> Generating manuscript text, LaTeX summary table, and BibTeX citations...")
    assets = generate_qm_manuscript_assets(report, output_dir)
    
    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_txt = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        bib_txt = f.read()
        
    html_p = os.path.join(output_dir, "report.html")
    print(f"  -> Writing HTML quality report to {html_p}...")
    generate_qm_html_report(report, html_p, methods_text=methods_txt, citation_bib=bib_txt)
    
    print("\n" + "="*70)
    print(f" [RESULT] Overall Quantum Chemistry Certification: {report.overall_status}")
    print(f" [SCORE]  {report.validation_score}")
    print("="*70)
    if report.frequency_result:
        fr = report.frequency_result
        print(f" * Stationary Point : {fr.point_type} ({fr.n_imaginary} imag modes) | Status: {fr.status}")
    if report.scf_result:
        print(f" * SCF Convergence  : Status: {report.scf_result['status']}")
    if report.spin_result:
        print(f" * Spin <S^2>       : Status: {report.spin_result.status}")
    print("="*70)
    print(f"\nReport ready at: {os.path.abspath(html_p)}\n")


def print_citation():
    bib = """@software{monreal2026qmcert,
  author = {Monreal-Hern\\'andez, Andre},
  title = {{QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum-Chemical Calculations}},
  year = {2026},
  version = {1.0.0},
  publisher = {Zenodo},
  url = {https://github.com/sircalch/qmcert}
}"""
    print("\nIf you use QMCert in your publications, please cite:\n")
    print("APA Style:")
    print("Monreal-Hernández, A. (2026). QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum-Chemical Calculations (v1.0.0). Zenodo. https://github.com/sircalch/qmcert\n")
    print("BibTeX:")
    print(bib)
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="qmcert",
        description="QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum Chemistry."
    )
    parser.add_argument("-v", "--version", action="version", version=f"qmcert {__version__}")
    
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")
    
    # Assess command
    assess_parser = subparsers.add_parser("assess", help="Assess quantum chemistry calculation output file")
    assess_parser.add_argument("-i", "--input", required=True, help="Calculation output log file (.out, .log)")
    assess_parser.add_argument("--ts", action="store_true", help="Expect Transition State (exactly 1 imaginary frequency)")
    assess_parser.add_argument("-o", "--output", default="qmcert_output", help="Directory for output report and assets (default: qmcert_output)")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run QMCert on a benchmark DFT calculation dataset")
    demo_parser.add_argument("-o", "--output", default="qmcert_demo_output", help="Output directory (default: qmcert_demo_output)")
    
    # Cite command
    subparsers.add_parser("cite", help="Display BibTeX and APA citation details")
    
    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    
    if args.command == "assess":
        print_banner()
        run_assess(args)
    elif args.command == "demo":
        print_banner()
        run_demo(args.output)
    elif args.command == "cite":
        print_banner()
        print_citation()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

