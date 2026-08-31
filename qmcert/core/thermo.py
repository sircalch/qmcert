"""
Thermochemical properties and Grimme quasi-RRHO vibrational entropy corrections.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class ThermochemistryData:
    temperature_k: float
    pressure_atm: float
    zpve_hartree: float
    thermal_energy_hartree: float
    enthalpy_hartree: float
    gibbs_free_energy_hartree: float
    entropy_cal_mol_k: float
    quasi_rrho_gibbs_hartree: Optional[float]
    quasi_rrho_entropy_cal_mol_k: Optional[float]


def calculate_quasi_rrho_corrections(
    frequencies: List[float],
    temperature: float = 298.15,
    cutoff_wavenumber: float = 100.0,
    rotor_b_avg: float = 1e-44  # kg*m^2 effective moment of inertia
) -> Dict[str, Any]:
    """
    Computes Grimme's quasi-RRHO (Rigid Rotor Harmonic Oscillator) entropy corrections
    for low-frequency vibrational modes to prevent entropy divergence.

    Reference: Grimme, S. Chem. Eur. J. 2012, 18, 9955-9964.

    Parameters
    ----------
    frequencies : list of float
        Harmonic vibrational frequencies in cm^-1.
    temperature : float, default 298.15
        Temperature in Kelvin.
    cutoff_wavenumber : float, default 100.0
        Damping cutoff omega_0 in cm^-1 (Grimme standard = 100 cm^-1).
    rotor_b_avg : float
        Effective moment of inertia for free rotor model.

    Returns
    -------
    result : dict
        Standard harmonic entropy, quasi-RRHO entropy, delta G correction (Hartree).
    """
    # Physical constants (SI units)
    h = 6.62607015e-34       # J*s
    c = 2.99792458e10        # cm/s
    k_b = 1.380649e-23       # J/K
    r_gas = 8.314462618      # J/(mol*K)
    cal_to_j = 4.184
    hartree_to_j_mol = 2625499.638  # J/mol
    
    freqs = np.asarray(frequencies, dtype=float)
    pos_freqs = freqs[freqs > 0]
    
    if len(pos_freqs) == 0:
        return {
            "s_harmonic_cal_mol_k": 0.0,
            "s_quasi_rrho_cal_mol_k": 0.0,
            "delta_g_quasi_rrho_hartree": 0.0,
            "n_low_freq_modes": 0
        }
        
    s_harm_total = 0.0
    s_qrrho_total = 0.0
    n_low_freq = 0
    
    for omega in pos_freqs:
        nu = omega * c  # frequency in Hz
        x = (h * nu) / (k_b * temperature)
        
        # Standard harmonic vibrational entropy
        # S_vib = R * [ x / (exp(x) - 1) - ln(1 - exp(-x)) ]
        if x > 50.0:
            s_vib = 0.0
        else:
            s_vib = r_gas * (x / (np.exp(x) - 1.0) - np.log(1.0 - np.exp(-x)))
            
        # Free rotor entropy approximation: S_rot = R * (0.5 + ln( sqrt(8 * pi^3 * k_b * T * B_eff) / h ))
        # Using Grimme formula for free rotor
        mu = (h / (8.0 * np.pi**2 * nu)) if nu > 0 else rotor_b_avg
        mu_eff = (mu * rotor_b_avg) / (mu + rotor_b_avg)
        s_rot = r_gas * (0.5 + np.log(np.sqrt(8.0 * np.pi**3 * k_b * temperature * mu_eff) / h))
        
        # Damping weight function: w(omega) = 1 / (1 + (omega_0 / omega)^4)
        weight = 1.0 / (1.0 + (cutoff_wavenumber / omega) ** 4)
        
        s_qrrho = weight * s_vib + (1.0 - weight) * s_rot
        
        s_harm_total += s_vib
        s_qrrho_total += s_qrrho
        if omega < cutoff_wavenumber:
            n_low_freq += 1
            
    # Convert J/(mol*K) -> cal/(mol*K)
    s_harm_cal = s_harm_total / cal_to_j
    s_qrrho_cal = s_qrrho_total / cal_to_j
    
    # Delta G correction: -T * (S_qrrho - S_harm) in Hartree
    delta_s_j_mol = (s_qrrho_total - s_harm_total)
    delta_g_hartree = (-temperature * delta_s_j_mol) / hartree_to_j_mol
    
    return {
        "s_harmonic_cal_mol_k": float(s_harm_cal),
        "s_quasi_rrho_cal_mol_k": float(s_qrrho_cal),
        "delta_g_quasi_rrho_hartree": float(delta_g_hartree),
        "n_low_freq_modes": int(n_low_freq)
    }
