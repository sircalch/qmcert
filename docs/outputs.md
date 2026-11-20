# Outputs

`qmcert assess` and `qmcert demo` write these files to the output directory:

| File | Content |
|---|---|
| `report.html` | Self-contained report with every check, its status and diagnostics |
| `qmcert_optimization_trajectory.svg`, `.pdf`, `.png` | Energy along the geometry optimisation (when the job contains one) |
| `qmcert_simulated_ir_spectrum.svg`, `.pdf`, `.png` | Simulated IR spectrum from the harmonic frequencies (when they are available) |
| `qmcert_summary_table.csv`, `.tex` | Summary table, ready for a spreadsheet or a LaTeX manuscript |
| `methods_snippet.txt` | Draft methods paragraph that states each result, including the number of imaginary frequencies, the spin contamination and the quasi-RRHO treatment |
| `citation.bib` | BibTeX entry for QMCert |

The methods paragraph is a starting point: edit it so that it describes your study accurately.
