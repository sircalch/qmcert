# Changelog

## 1.1.0 (unreleased)

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
