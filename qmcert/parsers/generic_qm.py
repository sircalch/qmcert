"""
Universal quantum chemical log parser with automated engine detection.
"""

from typing import Dict, Any
import os
from qmcert.parsers.orca import parse_orca_output
from qmcert.parsers.gaussian import parse_gaussian_output


def parse_qm_output(filepath: str) -> Dict[str, Any]:
    """
    Automatically detects quantum chemistry engine and parses output.

    Parameters
    ----------
    filepath : str
        Path to output/log file.

    Returns
    -------
    data : dict
        Parsed parameters and calculation results.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        # Read first 100 lines for header detection
        head = "".join([f.readline() for _ in range(100)])
        
    head_lower = head.lower()
    
    if "orca" in head_lower or "neese" in head_lower or "* o   r   c   a *" in head:
        return parse_orca_output(filepath)
    elif "gaussian" in head_lower or "entering gaussian system" in head_lower:
        return parse_gaussian_output(filepath)
    else:
        # Fallback to ORCA parser then Gaussian parser
        try:
            return parse_orca_output(filepath)
        except Exception:
            return parse_gaussian_output(filepath)
