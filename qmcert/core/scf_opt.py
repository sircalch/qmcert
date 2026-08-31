"""
SCF and Geometry Optimization Convergence Criteria Evaluation.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import numpy as np


@dataclass
class ConvergenceCriteria:
    energy_change: Optional[float]
    max_gradient: Optional[float]
    rms_gradient: Optional[float]
    max_step: Optional[float]
    rms_step: Optional[float]
    energy_converged: bool
    max_gradient_converged: bool
    rms_gradient_converged: bool
    max_step_converged: bool
    rms_step_converged: bool


def evaluate_scf_convergence(
    scf_converged: bool,
    n_scf_cycles: int,
    energy_diff: Optional[float] = None,
    max_cycles: int = 128
) -> Dict[str, Any]:
    """
    Evaluates self-consistent field (SCF) convergence status.

    Parameters
    ----------
    scf_converged : bool
        Whether SCF converged.
    n_scf_cycles : int
        Number of iterations required.
    energy_diff : float, optional
        Final delta E between last two iterations in Eh.
    max_cycles : int
        Maximum cycle limit.

    Returns
    -------
    result : dict
        SCF evaluation status, cycle counts, and recommendations.
    """
    if scf_converged:
        if n_scf_cycles > int(0.8 * max_cycles):
            status = "WARNING"
            msg = f"SCF converged after high number of cycles ({n_scf_cycles}/{max_cycles}). Consider using DIIS, SOSCF or smaller trust radius."
        else:
            status = "PASS"
            msg = f"SCF successfully converged in {n_scf_cycles} iterations."
    else:
        status = "FAIL"
        msg = f"SCF failed to converge within {n_scf_cycles} iterations. Wavefunction is invalid."

    return {
        "status": status,
        "converged": scf_converged,
        "n_cycles": n_scf_cycles,
        "energy_diff": energy_diff,
        "diagnostic_message": msg
    }


def evaluate_geometry_optimization(
    opt_converged: bool,
    n_opt_steps: int,
    energies_trajectory: Optional[List[float]] = None,
    criteria: Optional[ConvergenceCriteria] = None
) -> Dict[str, Any]:
    """
    Evaluates geometry optimization convergence and trajectory stability.

    Parameters
    ----------
    opt_converged : bool
        Whether geometry optimization reached complete convergence.
    n_opt_steps : int
        Number of optimization steps taken.
    energies_trajectory : list of float, optional
        Electronic energies at each optimization step (Eh).
    criteria : ConvergenceCriteria, optional
        Detailed values for the 4 standard convergence thresholds.

    Returns
    -------
    result : dict
        Status, energy variation, trajectory smoothness, and recommendations.
    """
    if opt_converged:
        status = "PASS"
        msg = f"Geometry optimization fully converged in {n_opt_steps} steps."
    else:
        status = "FAIL"
        msg = f"Geometry optimization did not converge ({n_opt_steps} steps taken). Structure is not a stationary point."

    total_e_change = 0.0
    if energies_trajectory and len(energies_trajectory) > 1:
        total_e_change = energies_trajectory[-1] - energies_trajectory[0]

    return {
        "status": status,
        "converged": opt_converged,
        "n_steps": n_opt_steps,
        "total_energy_change_hartree": total_e_change,
        "criteria": criteria,
        "diagnostic_message": msg
    }
