"""
Parser for Gaussian 09 and Gaussian 16 output log files.
"""

from typing import Dict, Any, List, Optional
import os
import re
from qmcert.core.thermo import ThermochemistryData


def parse_gaussian_output(filepath: str) -> Dict[str, Any]:
    """
    Parses a Gaussian calculation output (.log / .out).

    Parameters
    ----------
    filepath : str
        Path to the Gaussian log file.

    Returns
    -------
    data : dict
        Parsed Gaussian parameters and results.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    metadata: Dict[str, Any] = {
        "engine": "Gaussian",
        "version": "Gaussian 09/16",
        "functional": "Unknown",
        "basis_set": "Unknown",
        "dispersion": "None",
        "solvent_model": "Gas Phase",
        "charge": 0,
        "multiplicity": 1
    }

    # Gaussian route line: e.g. "# opt freq b3lyp/6-31g(d) scrf=(smd,solvent=water)"
    route_match = re.search(r"#\s*(.*)", content)
    if route_match:
        route = route_match.group(1).lower()
        metadata["route_line"] = route
        for tok in route.split():
            if "/" in tok:
                parts = tok.split("/")
                metadata["functional"] = parts[0].upper()
                metadata["basis_set"] = parts[1]
            elif "empiricaldispersion=" in tok:
                metadata["dispersion"] = tok.split("=")[-1].upper()
            elif "scrf=" in tok:
                metadata["solvent_model"] = tok.upper()

    # Fallback for functional from SCF line: e.g. "SCF Done:  E(RB3LYP)" or "E(UB3LYP)" or "E(RM062X)"
    scf_method_match = re.search(r"SCF Done:\s+E\(([A-Z0-9\-]+)\)", content)
    if scf_method_match and metadata["functional"] == "Unknown":
        raw_m = scf_method_match.group(1)
        # Strip R or U prefix
        if raw_m.startswith("R") or raw_m.startswith("U"):
            metadata["functional"] = raw_m[1:]
        else:
            metadata["functional"] = raw_m

    # Charge and Multiplicity: "Charge =  0 Multiplicity = 1"
    cm_match = re.search(r"Charge\s*=\s*(-?\d+)\s+Multiplicity\s*=\s*(\d+)", content)
    if cm_match:
        metadata["charge"] = int(cm_match.group(1))
        metadata["multiplicity"] = int(cm_match.group(2))

    # SCF convergence
    scf_converged = bool("SCF Done:" in content)
    scf_cycles = 1
    cycle_matches = re.findall(r"(\d+)\s+cycles", content)
    if cycle_matches:
        scf_cycles = int(cycle_matches[-1])

    # Final energy: "SCF Done:  E(RB3LYP) =  -382.456789     A.U."
    e_matches = re.findall(r"SCF Done:\s+E\([A-Z0-9\-]+\)\s*=\s*([\-\d\.]+)", content)
    final_e = float(e_matches[-1]) if e_matches else None

    # Geometry optimization convergence: "Stationary point found."
    is_opt = bool("Optimization completed." in content or "Stationary point found." in content or "Item               Value     Threshold  Converged?" in content)
    opt_converged = None
    n_opt_steps = None
    if is_opt:
        opt_converged = bool("Stationary point found." in content or "Optimization completed." in content)
        step_matches = re.findall(r"Step number\s+(\d+)", content)
        n_opt_steps = int(step_matches[-1]) if step_matches else 1

    # Vibrational frequencies: "Frequencies --   123.45   234.56   345.67"
    # "IR Inten    --    12.34    45.67    89.01"
    freq_matches = re.findall(r"Frequencies\s*--\s*(.*)", content)
    intens_matches = re.findall(r"IR Inten\s*--\s*(.*)", content)
    
    frequencies = []
    intensities = []
    for fm in freq_matches:
        for val_s in fm.split():
            try:
                frequencies.append(float(val_s))
            except ValueError:
                pass
                
    for im in intens_matches:
        for val_s in im.split():
            try:
                intensities.append(float(val_s))
            except ValueError:
                pass

    # Spin contamination <S^2>
    s2_calc = None
    s2_match = re.findall(r"<S\*\*2>\s*=\s*([\d\.]+)", content)
    if s2_match:
        s2_calc = float(s2_match[-1])

    # Thermochemistry
    zpve_match = re.search(r"Zero-point correction=\s*([\-\d\.]+)", content)
    h_match = re.search(r"Sum of electronic and thermal Enthalpies=\s*([\-\d\.]+)", content)
    g_match = re.search(r"Sum of electronic and thermal Free Energies=\s*([\-\d\.]+)", content)
    
    thermo_data = None
    if zpve_match and g_match:
        zpve = float(zpve_match.group(1))
        h_val = float(h_match.group(1)) if h_match else (final_e + zpve if final_e else 0.0)
        g_val = float(g_match.group(1))
        s_val = ((h_val - g_val) / 298.15) * 627509.474
        
        thermo_data = ThermochemistryData(
            temperature_k=298.15,
            pressure_atm=1.0,
            zpve_hartree=zpve,
            thermal_energy_hartree=h_val,
            enthalpy_hartree=h_val,
            gibbs_free_energy_hartree=g_val,
            entropy_cal_mol_k=s_val,
            quasi_rrho_gibbs_hartree=None,
            quasi_rrho_entropy_cal_mol_k=None
        )

    return {
        "metadata": metadata,
        "scf_converged": scf_converged,
        "n_scf_cycles": scf_cycles,
        "opt_converged": opt_converged,
        "n_opt_steps": n_opt_steps,
        "final_energy_hartree": final_e,
        "energies_trajectory": [float(e) for e in e_matches] if len(e_matches) > 1 else None,
        "frequencies": frequencies if frequencies else None,
        "intensities": intensities if intensities else None,
        "s2_calculated": s2_calc,
        "homo_ev": None,
        "lumo_ev": None,
        "thermochemistry": thermo_data
    }
