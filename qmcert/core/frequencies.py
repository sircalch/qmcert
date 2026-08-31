"""
Vibrational frequencies, imaginary mode detection, and stationary point certification.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class FrequencyAnalysisResult:
    n_frequencies: int
    n_imaginary: int
    imaginary_frequencies: List[float]
    lowest_frequency: float
    point_type: str  # 'LOCAL_MINIMUM', 'TRANSITION_STATE', 'HIGHER_ORDER_SADDLE_POINT'
    expected_type: str  # 'MINIMUM' or 'TRANSITION_STATE'
    status: str  # 'PASS', 'WARNING', 'FAIL'
    diagnostic_message: str
    frequencies: List[float]
    intensities: Optional[List[float]]


def classify_stationary_point(
    frequencies: List[float],
    intensities: Optional[List[float]] = None,
    expected_type: str = "MINIMUM",
    imaginary_cutoff: float = -10.0
) -> FrequencyAnalysisResult:
    """
    Certifies stationary point nature based on harmonic vibrational frequencies.

    Parameters
    ----------
    frequencies : list of float
        Harmonic vibrational frequencies in cm^-1.
    intensities : list of float, optional
        IR absorption intensities (km/mol).
    expected_type : str, default 'MINIMUM'
        Expected stationary point: 'MINIMUM' (ground state/intermediate) or 'TRANSITION_STATE' (TS).
    imaginary_cutoff : float, default -10.0
        Threshold below which a frequency is considered a true imaginary mode (cm^-1).

    Returns
    -------
    result : FrequencyAnalysisResult
        Detailed classification result with pass/fail validation.
    """
    freqs = np.asarray(frequencies, dtype=float)
    n_total = len(freqs)
    
    if n_total == 0:
        return FrequencyAnalysisResult(
            n_frequencies=0,
            n_imaginary=0,
            imaginary_frequencies=[],
            lowest_frequency=0.0,
            point_type="UNKNOWN",
            expected_type=expected_type.upper(),
            status="WARNING",
            diagnostic_message="No vibrational frequencies provided in output.",
            frequencies=[],
            intensities=intensities
        )
        
    # Identify imaginary frequencies (negative values in cm^-1)
    imag_freqs = freqs[freqs < imaginary_cutoff].tolist()
    n_imag = len(imag_freqs)
    lowest_freq = float(np.min(freqs))
    
    exp_upper = expected_type.strip().upper()
    if exp_upper in ["TS", "TRANSITION_STATE", "TRANSITION STATE", "SADDLE"]:
        target = "TRANSITION_STATE"
    else:
        target = "MINIMUM"
        
    # Classify physical point type
    if n_imag == 0:
        point_type = "LOCAL_MINIMUM"
    elif n_imag == 1:
        point_type = "TRANSITION_STATE"
    else:
        point_type = "HIGHER_ORDER_SADDLE_POINT"
        
    # Certification Logic
    if target == "MINIMUM":
        if n_imag == 0:
            status = "PASS"
            diag = f"Stationary point certified as true local minimum (0 imaginary frequencies, lowest mode = {lowest_freq:.1f} cm^-1)."
        elif n_imag == 1:
            status = "FAIL"
            diag = f"1 imaginary frequency detected (nu = {imag_freqs[0]:.1f} cm^-1). Structure is a Transition State, not a confirmed local minimum."
        else:
            status = "FAIL"
            diag = f"{n_imag} imaginary frequencies detected (lowest: {imag_freqs[0]:.1f} cm^-1). Geometry is a higher-order saddle point."
    elif target == "TRANSITION_STATE":
        if n_imag == 1:
            status = "PASS"
            diag = f"Transition state confirmed (exactly 1 imaginary frequency: nu = {imag_freqs[0]:.1f} cm^-1)."
        elif n_imag == 0:
            status = "FAIL"
            diag = "No imaginary frequency detected (0 imaginary modes). Structure converged to a local minimum instead of a transition state."
        else:
            status = "FAIL"
            diag = f"{n_imag} imaginary frequencies detected. Geometry is a higher-order saddle point rather than a first-order transition state."

    return FrequencyAnalysisResult(
        n_frequencies=n_total,
        n_imaginary=n_imag,
        imaginary_frequencies=imag_freqs,
        lowest_frequency=lowest_freq,
        point_type=point_type,
        expected_type=target,
        status=status,
        diagnostic_message=diag,
        frequencies=freqs.tolist(),
        intensities=intensities
    )


def simulate_ir_spectrum(
    frequencies: List[float],
    intensities: Optional[List[float]] = None,
    fwhm: float = 15.0,
    wavenumber_range: Tuple[float, float] = (400.0, 4000.0),
    n_points: int = 2000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulates an experimental-style Infrared (IR) absorption spectrum by applying
    Lorentzian line-broadening to harmonic vibrational transitions:
        I(nu) = sum_k A_k * gamma / (pi * ((nu - nu_k)^2 + gamma^2))

    Parameters
    ----------
    frequencies : list of float
        Harmonic frequencies in cm^-1.
    intensities : list of float, optional
        Harmonic IR intensities in km/mol. If None, equal weights assumed.
    fwhm : float, default 15.0
        Full Width at Half Maximum (gamma = FWHM / 2) in cm^-1.
    wavenumber_range : tuple of (float, float), default (400, 4000)
        Integration domain in cm^-1.
    n_points : int, default 2000
        Number of spectral grid points.

    Returns
    -------
    wavenumbers : np.ndarray
        1D grid of wavenumbers (cm^-1).
    absorbance : np.ndarray
        Simulated absorption intensity spectrum.
    """
    freqs = np.asarray(frequencies, dtype=float)
    # Ignore imaginary modes for positive spectrum
    real_mask = freqs > 0
    valid_freqs = freqs[real_mask]
    
    if intensities is not None and len(intensities) == len(freqs):
        valid_intens = np.asarray(intensities, dtype=float)[real_mask]
    else:
        valid_intens = np.ones(len(valid_freqs), dtype=float)
        
    wn_grid = np.linspace(wavenumber_range[0], wavenumber_range[1], n_points)
    absorbance = np.zeros(n_points, dtype=float)
    
    gamma = fwhm / 2.0
    
    for nu_k, a_k in zip(valid_freqs, valid_intens):
        # Lorentzian peak
        absorbance += a_k * (gamma / np.pi) / ((wn_grid - nu_k) ** 2 + gamma ** 2)
        
    # Normalize peak max to 100%
    if np.max(absorbance) > 0:
        absorbance = (absorbance / np.max(absorbance)) * 100.0
        
    return wn_grid, absorbance
