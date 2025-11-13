"""
Model registry for attribution and contribution analysis.
"""

from analysis import (
    brinson_fachler,
    brinson_fachler_instrument,
    brinson_hood_beebower,
    brinson_hood_beebower_instrument,
    effects_analysis,
    effects_analysis_instrument,
    contribution,
    contribution_instrument,
    grap_smoothing,
    modified_frongello_smoothing,
    contribution_smoothing,
    measurement_analytics_master,
    measurement_analytics_instrument
)

# Attribution model registry
# Structure: {model_name: (master_function, instrument_function)}
MODEL_REGISTRY = {
    "Brinson-Fachler": {
        "master": brinson_fachler,
        "instrument": brinson_fachler_instrument
    },
    "Brinson-Hood-Beebower": {
        "master": brinson_hood_beebower,
        "instrument": brinson_hood_beebower_instrument
    },
    "Standard fixed income attribution": {
        "master": effects_analysis,
        "instrument": effects_analysis_instrument
    },
    "with Brinson Fachler on credit (POC)": {
        "master": effects_analysis,
        "instrument": effects_analysis_instrument
    }
}

# Contribution analysis registry
CONTRIBUTION_REGISTRY = {
    "master": contribution,
    "instrument": contribution_instrument
}

# Smoothing algorithm registry
SMOOTHING_REGISTRY = {
    "Frongello": grap_smoothing,
    "Modified Frongello": modified_frongello_smoothing
}

# Contribution smoothing function
CONTRIBUTION_SMOOTHING = contribution_smoothing

# Measurement & Analytics registry
MEASUREMENT_REGISTRY = {
    "master": measurement_analytics_master,
    "instrument": measurement_analytics_instrument
}
