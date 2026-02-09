# app_state.py
from dataclasses import dataclass

@dataclass
class AppState:
    # current angles (UI will display)
    pan: int = 90
    tilt: int = 90

    # step size for keyboard nudging
    step: int = 5

    # safe ranges (soft limits) - change after calibration
    pan_min: int = 20
    pan_max: int = 160
    tilt_min: int = 20
    tilt_max: int = 160
