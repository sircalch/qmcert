"""
Quickstart API tutorial for QMCert.
"""

import os
from qmcert import assess_qm_quality
from qmcert.parsers import parse_qm_output
from qmcert.reporters import (
    generate_qm_figures,
    generate_qm_manuscript_assets,
    generate_qm_html_report
)
from examples.generate_sample_outputs import generate_sample_orca_output


def main():
    print("Running QMCert Python API quickstart example...")
    output_dir = "quickstart_qmcert_output"
    os.makedirs(output_dir, exist_ok=True)
    
    sample_file = "sample_orca_calc.out"
    generate_sample_orca_output(sample_file)
    
    # 1. Parse calculation
    parsed = parse_qm_output(sample_file)
    meta = parsed["metadata"]
    
    # 2. Assess calculation
    report = assess_qm_quality(
        metadata=meta,
        scf_converged=parsed["scf_converged"],
        n_scf_cycles=parsed["n_scf_cycles"],
        opt_converged=parsed["opt_converged"],
        n_opt_steps=parsed["n_opt_steps"],
        frequencies=parsed["frequencies"],
        intensities=parsed["intensities"],
        expected_point_type="MINIMUM",
        thermochemistry=parsed["thermochemistry"]
    )
    
    print(f"\nOverall Certification: {report.overall_status}")
    print(f"Validation Score: {report.validation_score}")
    print(f"Method: {meta['functional']}/{meta['basis_set']} ({meta['engine']})")
    if report.frequency_result:
        print(f"Stationary Point: {report.frequency_result.point_type} ({report.frequency_result.n_imaginary} imag modes)")
        
    # 3. Export all publication assets
    generate_qm_figures(report, output_dir)
    assets = generate_qm_manuscript_assets(report, output_dir)
    
    with open(assets["methods_text"], "r", encoding="utf-8") as f:
        methods_txt = f.read()
    with open(assets["citation_bib"], "r", encoding="utf-8") as f:
        bib_txt = f.read()
        
    html_p = os.path.join(output_dir, "report.html")
    generate_qm_html_report(report, html_p, methods_text=methods_txt, citation_bib=bib_txt)
    
    print(f"\nCompleted! Check out: {os.path.abspath(html_p)}")


if __name__ == "__main__":
    main()
