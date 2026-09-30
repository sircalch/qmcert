"""
Parser for ORCA 4.x, 5.x, and 6.x output files.
"""

from typing import Dict, Any, List, Optional, Tuple
import os
import re
from qmcert.core.thermo import ThermochemistryData


def parse_orca_output(filepath: str) -> Dict[str, Any]:
    """
    Parses an ORCA quantum chemical output file (.out / .log).

    Parameters
    ----------
    filepath : str
        Path to the ORCA output file.

    Returns
    -------
    data : dict
        Parsed parameters, electronic energies, SCF cycles, geometry optimization,
        vibrational frequencies, spin values, orbitals, and thermochemistry.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    metadata: Dict[str, Any] = {
        "engine": "ORCA",
        "version": "Unknown",
        "functional": "Unknown",
        "basis_set": "Unknown",
        "dispersion": "None",
        "solvent_model": "Gas Phase",
        "charge": 0,
        "multiplicity": 1,
        "n_atoms": 0,
        "scf_type": "RKS/RHF"
    }

    # 1. ORCA Version
    v_match = re.search(r"Program Version\s+([0-9\.]+)", content, re.IGNORECASE)
    if v_match:
        metadata["version"] = v_match.group(1)
        
    # 2. Input line
    input_line_match = re.search(r"\|\s*1>\s*!(.*)", content)
    if not input_line_match:
        input_line_match = re.search(r"!\s*(.*)", content)
    if input_line_match:
        raw_cmd = input_line_match.group(1).strip()
        metadata["raw_command"] = raw_cmd
        tokens = raw_cmd.split()
        for tok in tokens:
            tok_l = tok.lower()
            if tok_l in ["b3lyp", "pbe", "pbe0", "m062x", "m06-2x", "wb97x-d", "wb97x-d3", "wb97x-v", "b97-3c", "r2scan-3c", "pbeh-3c", "bp86", "tpss", "tpssh", "pw6b95", "cam-b3lyp"]:
                metadata["functional"] = tok.upper()
            elif any(b in tok_l for b in ["def2-", "6-31", "cc-pv", "ano-"]):
                metadata["basis_set"] = tok
            elif "d3" in tok_l or "d4" in tok_l or "d3bj" in tok_l:
                metadata["dispersion"] = tok.upper()
            elif "cpcm" in tok_l or "smd" in tok_l:
                metadata["solvent_model"] = tok.upper()

    # 3. Charge and Multiplicity
    cm_match = re.search(r"Total Charge\s+Charge\s*\.\.\.\.\s*(-?\d+)", content)
    if cm_match:
        metadata["charge"] = int(cm_match.group(1))
    mult_match = re.search(r"Multiplicity\s+Mult\s*\.\.\.\.\s*(\d+)", content)
    if mult_match:
        metadata["multiplicity"] = int(mult_match.group(1))

    n_at = re.findall(r"Number of atoms\s*\.+\s*(\d+)", content)
    if n_at:
        metadata["n_atoms"] = int(n_at[-1])

    # 4. SCF Convergence (last SCF run of the job)
    # The outcome of the last SCF in the file decides: an optimisation contains many SCF runs, and an
    # early failure followed by later successes (or the reverse) must not be read from the whole file.
    outcomes = [(m.start(), True) for m in re.finditer(r"SCF CONVERGED AFTER\s+\d+\s+CYCLES", content)]
    outcomes += [(m.start(), False) for m in re.finditer(r"SCF NOT CONVERGED", content, re.IGNORECASE)]
    if outcomes:
        scf_converged = max(outcomes)[1]
    else:
        scf_converged = bool("SUCCESSFULLY CONVERGED" in content)
    scf_cycles = 1
    conv_cycles = re.findall(r"SCF CONVERGED AFTER\s+(\d+)\s+CYCLES", content)
    if conv_cycles:
        scf_cycles = int(conv_cycles[-1])
    else:
        cycle_matches = re.findall(r"SCF iterations\s*\.\.\.\.\s*(\d+)", content)
        if cycle_matches:
            scf_cycles = int(cycle_matches[-1])

    # 5. Geometry Optimization Convergence
    is_opt = bool("GEOMETRY OPTIMIZATION CYCLE" in content or "OPTIMIZATION RUN" in content)
    opt_converged = None
    n_opt_steps = None
    opt_energies = []

    if is_opt:
        # ORCA prints "***   THE OPTIMIZATION HAS CONVERGED   ***" with version-dependent spacing
        opt_converged = bool(re.search(r"THE OPTIMIZATION HAS CONVERGED", content))
        step_matches = re.findall(r"GEOMETRY OPTIMIZATION CYCLE\s+(\d+)", content)
        n_opt_steps = int(step_matches[-1]) if step_matches else 1
        e_matches = re.findall(r"FINAL SINGLE POINT ENERGY\s+([\-\d\.]+)", content)
        if e_matches:
            opt_energies = [float(e) for e in e_matches]

    # Final electronic energy
    final_e = None
    final_e_match = re.findall(r"FINAL SINGLE POINT ENERGY\s+([\-\d\.]+)", content)
    if final_e_match:
        final_e = float(final_e_match[-1])

    # 6. Vibrational Frequencies & IR Intensities (last frequency calculation in the file).
    # Block layout:  VIBRATIONAL FREQUENCIES / ---- / (blank) / Scaling factor ... / (blank) /
    #                "     6:    -830.27 cm**-1  ***imaginary mode***"
    # Exactly-zero entries are the projected translations/rotations and are excluded.
    frequencies: List[float] = []
    intensities: List[float] = []
    freq_modes: List[int] = []
    freq_blocks = re.split(r"VIBRATIONAL FREQUENCIES\s*\n-+\s*\n", content)
    if len(freq_blocks) > 1:
        body = re.split(r"NORMAL MODES|IR SPECTRUM", freq_blocks[-1])[0]
        freq_modes: List[int] = []
        for mode, val in re.findall(r"^\s*(\d+):\s+(-?\d+\.\d+)\s+cm\*\*-1", body, re.M):
            f_val = float(val)
            if abs(f_val) > 1e-6:
                frequencies.append(f_val)
                freq_modes.append(int(mode))

    # IR intensities in km/mol, read by column name from the header of the last IR SPECTRUM block
    ir_blocks = re.split(r"IR SPECTRUM\s*\n-+\s*\n", content)
    if len(ir_blocks) > 1:
        body = ir_blocks[-1].split("* The epsilon")[0]
        header = next((ln for ln in body.splitlines() if "Mode" in ln and "freq" in ln), "")
        cols = header.split()
        int_col = cols.index("Int") if "Int" in cols else (cols.index("T**2") if "T**2" in cols else None)
        if int_col is not None:
            int_by_mode: Dict[int, float] = {}
            for ln in body.splitlines():
                parts = ln.replace("(", " ").replace(")", " ").split()
                if len(parts) > int_col and parts[0].rstrip(":").isdigit():
                    try:
                        int_by_mode[int(parts[0].rstrip(":"))] = float(parts[int_col])
                    except ValueError:
                        pass
            # ORCA omits imaginary modes from the IR table: align by mode number (0.0 when absent)
            if frequencies and int_by_mode:
                intensities = [int_by_mode.get(m, 0.0) for m in freq_modes]

    # 7. Spin expectation value <S^2> of the final SCF
    s2_calc = None
    s2_all = re.findall(r"Expectation value of <S\*\*2>\s*:\s*([\d\.]+)", content)
    if s2_all:
        s2_calc = float(s2_all[-1])

    # 8. Frontier orbitals from the last ORBITAL ENERGIES section
    # (restricted: one table; unrestricted: SPIN UP / SPIN DOWN tables). Columns: NO OCC E(Eh) E(eV)
    homo_ev = None
    lumo_ev = None
    if "ORBITAL ENERGIES" in content:
        orb_section = content.rsplit("ORBITAL ENERGIES", 1)[1]
        orb_section = re.split(r"MULLIKEN|LOEWDIN|\*{5,}", orb_section)[0]
        tables = re.split(r"SPIN (?:UP|DOWN) ORBITALS", orb_section)
        tables = tables[1:] if len(tables) > 1 else [orb_section]
        occ_levels, vir_levels = [], []
        for table in tables:
            for occ_s, ev_s in re.findall(r"^\s*\d+\s+(\d+\.\d+)\s+-?\d+\.\d+\s+(-?\d+\.\d+)\s*$", table, re.M):
                (occ_levels if float(occ_s) > 0.5 else vir_levels).append(float(ev_s))
        if occ_levels:
            homo_ev = max(occ_levels)
        if vir_levels:
            lumo_ev = min(vir_levels)

    # 9. Thermochemistry
    thermo_data = None
    zpve_match = re.search(r"Zero point energy\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    thermal_match = re.findall(r"Total thermal energy\s*(?:\.\.\.)?\s*([\-\d\.]+)\s*Eh", content)
    enthalpy_match = re.search(r"Total Enthalpy\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    gibbs_match = re.search(r"Final Gibbs free energy\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    entropy_match = re.search(r"Final entropy term\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    temp_match = re.search(r"Temperature\s*\.\.\.\s*([\d\.]+)\s*K", content)
    # ORCA 6 applies Grimme's quasi-RRHO entropy by default and prints "Quasi RRHO ... True"; the printed
    # Gibbs free energy then already contains the correction.
    qrrho_flag = re.findall(r"Quasi RRHO\s*\.\.\.\s*(True|False)", content)
    qrrho_by_program = bool(qrrho_flag) and qrrho_flag[-1] == "True"
    
    if zpve_match and gibbs_match:
        temp = float(temp_match.group(1)) if temp_match else 298.15
        zpve = float(zpve_match.group(1))
        h_val = float(enthalpy_match.group(1)) if enthalpy_match else (final_e + zpve if final_e else 0.0)
        g_val = float(gibbs_match.group(1))
        # Entropy in cal/(mol*K)
        # S = (H - G) / T in Hartree/K -> cal/(mol*K)
        hartree_to_cal_mol = 627509.474
        s_val = ((h_val - g_val) / temp) * hartree_to_cal_mol if temp > 0 else 0.0
        
        thermo_data = ThermochemistryData(
            temperature_k=temp,
            pressure_atm=1.0,
            zpve_hartree=zpve,
            thermal_energy_hartree=float(thermal_match[-1]) if thermal_match else h_val,
            enthalpy_hartree=h_val,
            gibbs_free_energy_hartree=g_val,
            entropy_cal_mol_k=s_val,
            quasi_rrho_gibbs_hartree=g_val if qrrho_by_program else None,
            quasi_rrho_entropy_cal_mol_k=s_val if qrrho_by_program else None,
            quasi_rrho_applied_by_program=qrrho_by_program
        )

    return {
        "metadata": metadata,
        "scf_converged": scf_converged,
        "n_scf_cycles": scf_cycles,
        "opt_converged": opt_converged,
        "n_opt_steps": n_opt_steps,
        "final_energy_hartree": final_e,
        "energies_trajectory": opt_energies,
        "frequencies": frequencies if frequencies else None,
        "intensities": intensities if intensities else None,
        "s2_calculated": s2_calc,
        "homo_ev": homo_ev,
        "lumo_ev": lumo_ev,
        "thermochemistry": thermo_data
    }
