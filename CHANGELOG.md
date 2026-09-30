# Changelog

## 1.2.0 (2026-09-30)

Benchmark on 59 ORCA 6.1.1 calculations (B3LYP-D3BJ/def2-SVP: minima, radicals and triplets,
symmetric saddle points, unconverged jobs, UHF single points) against cclib, GoodVibes and the
values printed by ORCA (`validation/`). Energies, frequencies, intensities, orbital energies,
<S^2> and thermochemistry agree to rounding error; every designed test gets the expected verdict.

### Fixed
- **Quasi-RRHO correction invited double counting.** ORCA 6 applies Grimme's quasi-RRHO entropy by
  default, so its printed Gibbs free energy already contains the correction. 1.1.0 reported that
  energy together with a separate correction and its methods paragraph said free energies "were
  adjusted" with it (up to 0.73 kcal/mol in the benchmark). QMCert now reads ORCA's
  `Quasi RRHO ... True/False` setting (`ThermochemistryData.quasi_rrho_applied_by_program`) and
  reports `gibbs_harmonic_hartree` and `gibbs_quasi_rrho_hartree` explicitly.
- Number of atoms was never read (always 0).
- SCF convergence is decided by the last SCF outcome in the file, not by any occurrence.
- Methods paragraph: spin contamination was called "negligible" whatever its value; structures with
  two or more imaginary frequencies were not mentioned; one imaginary frequency was described as a
  "confirmed" transition state even when a minimum was intended. The text now states each result.
- Overall labels "FULLY CERTIFIED" / "REJECTED" replaced by "ALL PASSED" / "AT LEAST ONE FAILED";
  report provenance carried a fixed version string.
- README claimed Q-Chem and NWChem support (no such parsers) and checks of four convergence
  thresholds (the optimiser's banner is read).

## 1.1.0 (2026-09-26)

### Fixed (validated on real ORCA 6.1.1 outputs, `validation/orca_runs/`)
- **Vibrational frequencies were never read from real ORCA outputs.** The frequency block was cut at the first
  blank line, which ORCA prints right after the header, so stationary points could not be classified at all.
  Frequencies are now read from the last `VIBRATIONAL FREQUENCIES` block. Projected translations and rotations
  (exactly 0.00 cm⁻¹) are excluded.
- **HOMO/LUMO energies** were matched from any line with four numbers anywhere in the file. They are now read
  from the last `ORBITAL ENERGIES` section, including the SPIN UP and SPIN DOWN tables of unrestricted runs.
- **Optimisation convergence** was reported as not converged for converged ORCA 6 optimisations, because the
  banner spacing changed between versions.
- **⟨S²⟩** was taken from the first SCF of an optimisation instead of the final one.
- **Thermal energy** was set equal to the enthalpy; it is now read from `Total thermal energy`, and H − U = kT.
- **IR intensities** were read from the ε column instead of Int (km/mol). They are now aligned with the
  frequencies by mode number, because ORCA omits imaginary modes from the IR table.
- The number of SCF cycles is taken from `SCF CONVERGED AFTER n CYCLES`.
- The demo output is labelled as synthetic data.

### Added
- Regression tests on real ORCA outputs: H₂O minimum, planar NH₃ saddle point, CH₃ radical, triplet O₂.

## 1.0.0 (2026-08-31)

Initial release.
