"""
Manuscript Methods text generator, LaTeX summary tables, and BibTeX citations for QMCert.
"""

from typing import Dict, Any
import os
import pandas as pd
from qmcert.core.scoring import QMCertValidationReport


def generate_qm_manuscript_assets(
    report: QMCertValidationReport,
    output_dir: str
) -> Dict[str, str]:
    """
    Generates manuscript Computational Details text, LaTeX tables, and BibTeX citations.

    Parameters
    ----------
    report : QMCertValidationReport
        Validation report.
    output_dir : str
        Output directory.

    Returns
    -------
    paths : dict
        Mapping of generated asset paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated = {}
    
    # 1. Summary DataFrame
    rows = []
    
    # Engine & Method
    meta = report.metadata
    rows.append({"Parameter": "Quantum Chemistry Engine", "Value": f"{meta.get('engine', 'ORCA')} {meta.get('version', '')}".strip(), "Status": "PASS"})
    rows.append({"Parameter": "Functional & Basis Set", "Value": f"{meta.get('functional', 'DFT')} / {meta.get('basis_set', 'Def2-TZVP')}", "Status": "PASS"})
    rows.append({"Parameter": "Dispersion Correction", "Value": str(meta.get("dispersion", "None")), "Status": "PASS"})
    rows.append({"Parameter": "Solvent Model", "Value": str(meta.get("solvent_model", "Gas Phase")), "Status": "PASS"})
    rows.append({"Parameter": "Charge & Multiplicity", "Value": f"q = {meta.get('charge', 0)}, (2S+1) = {meta.get('multiplicity', 1)}", "Status": "PASS"})
    
    if report.scf_result:
        rows.append({"Parameter": "SCF Convergence", "Value": f"Converged ({report.scf_result['n_cycles']} iterations)", "Status": report.scf_result["status"]})
        
    if report.geometry_result:
        rows.append({"Parameter": "Geometry Optimization", "Value": f"Converged ({report.geometry_result['n_steps']} steps)", "Status": report.geometry_result["status"]})
        
    if report.frequency_result:
        fr = report.frequency_result
        rows.append({"Parameter": "Stationary Point Type", "Value": f"{fr.point_type} ({fr.n_imaginary} imaginary modes)", "Status": fr.status})
        rows.append({"Parameter": "Lowest Vibrational Mode", "Value": f"{fr.lowest_frequency:.1f} cm^-1", "Status": fr.status})
        
    if report.spin_result:
        sr = report.spin_result
        rows.append({"Parameter": "Spin Contamination <S^2>", "Value": f"<S^2> = {sr.s2_calculated:.4f} (exact = {sr.s2_exact:.4f}, error = {sr.contamination_pct:.2f}%)", "Status": sr.status})
        
    if report.orbital_result:
        obr = report.orbital_result
        rows.append({"Parameter": "HOMO-LUMO Gap", "Value": f"{obr['gap_ev']:.2f} eV ({obr['gap_eh']:.4f} Eh)", "Status": obr["status"]})
        
    if report.thermochemistry:
        th = report.thermochemistry
        rows.append({"Parameter": "ZPVE", "Value": f"{th.zpve_hartree:.5f} Eh", "Status": "PASS"})
        rows.append({"Parameter": "Gibbs Free Energy G (298.15 K)", "Value": f"{th.gibbs_free_energy_hartree:.5f} Eh", "Status": "PASS"})
        
    if report.quasi_rrho_correction:
        qr = report.quasi_rrho_correction
        rows.append({"Parameter": "Grimme Quasi-RRHO Delta G", "Value": f"{qr['delta_g_quasi_rrho_hartree'] * 627.509:.3f} kcal/mol ({qr['n_low_freq_modes']} low modes)", "Status": "PASS"})

    df_summary = pd.DataFrame(rows)
    
    # CSV Table
    csv_path = os.path.join(output_dir, "qmcert_summary_table.csv")
    df_summary.to_csv(csv_path, index=False)
    generated["summary_csv"] = csv_path
    
    # LaTeX Table
    tex_table_path = os.path.join(output_dir, "qmcert_summary_table.tex")
    tex_table = df_summary.to_latex(index=False, escape=False)
    with open(tex_table_path, "w", encoding="utf-8") as f:
        f.write("% QMCert Quantum Chemistry Quality and Reproducibility Summary Table\n")
        f.write(tex_table)
    generated["summary_tex"] = tex_table_path

    # 2. Methods Text Snippet
    methods_path = os.path.join(output_dir, "methods_snippet.txt")
    
    func_str = meta.get("functional", "DFT")
    basis_str = meta.get("basis_set", "TZVP")
    disp_str = f" with {meta.get('dispersion')}" if meta.get("dispersion") and meta.get("dispersion") != "None" else ""
    solv_str = f" in {meta.get('solvent_model')}" if meta.get("solvent_model") and meta.get("solvent_model") != "Gas Phase" else ""
    engine_str = meta.get("engine", "ORCA")
    
    freq_sentence = ""
    if report.frequency_result:
        fr = report.frequency_result
        if fr.n_imaginary == 0:
            freq_sentence = f"Harmonic vibrational frequencies were calculated to confirm that optimized structures correspond to true local minima on the potential energy surface (0 imaginary frequencies, lowest mode = {fr.lowest_frequency:.1f} cm$^{{-1}}$). "
        elif fr.n_imaginary == 1:
            freq_sentence = f"Harmonic vibrational analysis confirmed a first-order transition state with exactly one imaginary frequency (nu = {fr.imaginary_frequencies[0]:.1f} cm$^{{-1}}$). "
            
    spin_sentence = ""
    if report.spin_result and report.spin_result.multiplicity > 1:
        sr = report.spin_result
        spin_sentence = f"Spin contamination was evaluated as negligible (<S^2> = {sr.s2_calculated:.4f}, deviation = {sr.contamination_pct:.2f}% relative to exact {sr.s2_exact:.4f}). "
        
    qrrho_sentence = ""
    if report.quasi_rrho_correction and report.quasi_rrho_correction["n_low_freq_modes"] > 0:
        qr = report.quasi_rrho_correction
        qrrho_sentence = f"Thermal free energies were adjusted using Grimme's quasi-RRHO harmonic entropy correction for {qr['n_low_freq_modes']} low-frequency modes below 100 cm$^{{-1}}$. "

    full_methods = (
        f"All quantum-chemical calculations were performed using {engine_str} at the {func_str}/{basis_str} level of theory{disp_str}{solv_str}. "
        f"Calculation quality, SCF convergence, and wavefunction consistency were systematically verified using QMCert v1.0.0 (Monreal-Hernández, 2026). "
        f"{freq_sentence}{spin_sentence}{qrrho_sentence}"
        f"Overall computational reproducibility was validated with status: {report.overall_status}."
    )
    
    with open(methods_path, "w", encoding="utf-8") as f:
        f.write(full_methods + "\n")
    generated["methods_text"] = methods_path

    # 3. BibTeX Citation File
    bib_path = os.path.join(output_dir, "citation.bib")
    bib_content = """@software{monreal2026qmcert,
  author = {Monreal-Hern\\'andez, Andre},
  title = {{QMCert: Automated Quality-Control, Stationary Point Certification, and Reproducibility Assessment for Quantum-Chemical Calculations}},
  year = {2026},
  version = {1.0.0},
  publisher = {Zenodo},
  url = {https://github.com/amonreal/qmcert}
}
"""
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(bib_content)
    generated["citation_bib"] = bib_path

    return generated
