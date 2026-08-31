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

    # 4. SCF Convergence
    scf_converged = bool("SUCCESSFULLY CONVERGED" in content or "SCF CONVERGED AFTER" in content or "SCF converged" in content)
    scf_cycles = 1
    cycle_matches = re.findall(r"SCF iterations\s*\.\.\.\.\s*(\d+)", content)
    if cycle_matches:
        scf_cycles = int(cycle_matches[-1])
    else:
        cycle_matches2 = re.findall(r"Iteration\s+(\d+)\s+:", content)
        if cycle_matches2:
            scf_cycles = int(cycle_matches2[-1])

    # 5. Geometry Optimization Convergence
    is_opt = bool("GEOMETRY OPTIMIZATION CYCLE" in content or "OPTIMIZATION RUN" in content)
    opt_converged = None
    n_opt_steps = None
    opt_energies = []
    
    if is_opt:
        opt_converged = bool(
            "*** THE OPTIMIZATION HAS CONVERGED ***" in content or
            "HURRAY - THE OPTIMIZATION HAS CONVERGED" in content
        )
        step_matches = re.findall(r"GEOMETRY OPTIMIZATION CYCLE\s+(\d+)", content)
        n_opt_steps = int(step_matches[-1]) if step_matches else 1
        
        # Extract energy trajectory
        e_matches = re.findall(r"FINAL SINGLE POINT ENERGY\s+([\-\d\.]+)", content)
        if e_matches:
            opt_energies = [float(e) for e in e_matches]

    # Final electronic energy
    final_e = None
    final_e_match = re.findall(r"FINAL SINGLE POINT ENERGY\s+([\-\d\.]+)", content)
    if final_e_match:
        final_e = float(final_e_match[-1])

    # 6. Vibrational Frequencies & IR Intensities
    frequencies: List[float] = []
    intensities: List[float] = []
    
    # Check for VIBRATIONAL FREQUENCIES block
    freq_block_match = re.search(r"VIBRATIONAL FREQUENCIES\s*[-]+\s*(.*?)(?:\n\s*\n|NORMAL MODES)", content, re.DOTALL)
    if freq_block_match:
        lines = freq_block_match.group(1).strip().splitlines()
        for l in lines:
            parts = l.strip().split()
            if len(parts) >= 2 and parts[0].replace(":", "").isdigit():
                try:
                    val = float(parts[1])
                    frequencies.append(val)
                except ValueError:
                    pass

    # Check for IR SPECTRUM block (intensities)
    ir_block_match = re.search(r"IR SPECTRUM\s*[-]+\s*(.*?)(?:\n\s*\n|The epsilon)", content, re.DOTALL)
    if ir_block_match:
        lines = ir_block_match.group(1).strip().splitlines()
        for l in lines:
            parts = l.strip().split()
            if len(parts) >= 3 and parts[0].replace(":", "").isdigit():
                try:
                    freq_val = float(parts[1])
                    t2_int = float(parts[2])
                    intensities.append(t2_int)
                except ValueError:
                    pass

    # 7. Spin expectation values <S^2>
    s2_calc = None
    s2_match = re.search(r"Expectation value of <S\*\*2>\s*:\s*([\d\.]+)", content)
    if s2_match:
        s2_calc = float(s2_match.group(1))

    # 8. Frontier Orbitals (HOMO / LUMO)
    homo_ev = None
    lumo_ev = None
    # ORCA orbital block: "NO   OCC          E(Eh)            E(eV)"
    orb_matches = re.findall(r"\s*(\d+)\s+([\d\.]+)\s+([\-\d\.]+)\s+([\-\d\.]+)", content)
    if orb_matches:
        last_occ_ev = None
        first_unocc_ev = None
        for idx_s, occ_s, eh_s, ev_s in orb_matches:
            try:
                occ = float(occ_s)
                ev = float(ev_s)
                if occ > 0.0:
                    last_occ_ev = ev
                elif occ == 0.0 and first_unocc_ev is None:
                    first_unocc_ev = ev
            except ValueError:
                pass
        homo_ev = last_occ_ev
        lumo_ev = first_unocc_ev

    # 9. Thermochemistry
    thermo_data = None
    zpve_match = re.search(r"Zero point energy\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    enthalpy_match = re.search(r"Total Enthalpy\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    gibbs_match = re.search(r"Final Gibbs free energy\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    entropy_match = re.search(r"Final entropy term\s*\.\.\.\s*([\-\d\.]+)\s*Eh", content)
    temp_match = re.search(r"Temperature\s*\.\.\.\s*([\d\.]+)\s*K", content)
    
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
        "energies_trajectory": opt_energies,
        "frequencies": frequencies if frequencies else None,
        "intensities": intensities if intensities else None,
        "s2_calculated": s2_calc,
        "homo_ev": homo_ev,
        "lumo_ev": lumo_ev,
        "thermochemistry": thermo_data
    }
