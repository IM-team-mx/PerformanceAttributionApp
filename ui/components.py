"""
Reusable UI components for Streamlit application.
"""
import streamlit as st
import numpy as np
import pandas as pd
from config.settings import (
    PERFORMANCE_PERIODS,
    DEFAULT_PORTFOLIOS,
    CLASSIFICATION_CRITERIA,
    FIXED_INCOME_EFFECTS,
    CUSTOM_DATE_DEFAULTS
)
from utils import style_dataframe, dataframe_height


def render_settings(portfolio_df, benchmark_df, data_source_toggle):
    """
    Render the settings panel for the application.

    Returns a dictionary with all user selections.
    """
    settings_row1 = st.columns(5)
    settings = {}

    # Asset class and analysis type
    settings['asset_class'] = settings_row1[1].pills(
        "Asset class",
        ["Equity", "Fixed income"],
        default="Equity"
    )
    settings['analysis_type'] = settings_row1[2].pills(
        "Analysis",
        ["Attribution", "Contribution"],
        default="Attribution"
    )

    # Model selection for Attribution
    if settings['analysis_type'] == "Attribution":
        if settings['asset_class'] == "Equity":
            settings['model'] = settings_row1[3].pills(
                "Model",
                ["Brinson-Fachler", "Brinson-Hood-Beebower"],
                default="Brinson-Fachler"
            )
        else:
            settings['model'] = settings_row1[3].pills(
                "Model",
                ["Standard fixed income attribution", "with Brinson Fachler on credit (POC)"],
                default="Standard fixed income attribution",
                disabled=True
            )
            settings['effects'] = st.multiselect(
                "Effects",
                FIXED_INCOME_EFFECTS["full_list"],
                FIXED_INCOME_EFFECTS["default"]
            )

        settings['smoothing'] = settings_row1[4].pills(
            "Smoothing algorithm",
            ["Frongello", "Modified Frongello"],
            default="Frongello"
        )
    else:
        settings['model'] = None
        settings['smoothing'] = None

    # Second row: portfolios, benchmark, period, decimals
    settings_row2 = st.columns(5)

    # Get portfolios and benchmarks
    portfolios = np.sort(portfolio_df["Portfolio"].unique())
    benchmarks = np.sort(benchmark_df["Benchmark"].unique())

    # Set defaults
    if data_source_toggle == "Use TPK data":
        default_config = DEFAULT_PORTFOLIOS[settings['asset_class']]
        default_portfolio = default_config["portfolio"]
        default_benchmark_idx = default_config["benchmark_index"]
    else:
        default_portfolio = portfolios[0]
        default_benchmark_idx = 0

    settings['portfolios'] = settings_row2[0].multiselect(
        "Portfolios",
        portfolios,
        default_portfolio
    )
    settings['benchmark'] = settings_row2[1].selectbox(
        "Benchmark",
        benchmarks,
        index=default_benchmark_idx
    )

    # Performance period
    settings['period'] = settings_row2[2].pills(
        "Performance period",
        ["1Y", "YTD", "6M", "1M", "MTD", "WTD", "1D", "Custom"],
        default="YTD"
    )

    if settings['period'] == "Custom":
        settings['start_date'] = settings_row2[2].date_input(
            "Select start date",
            CUSTOM_DATE_DEFAULTS["start_date"]
        )
        settings['end_date'] = settings_row2[2].date_input(
            "Select end date",
            CUSTOM_DATE_DEFAULTS["end_date"]
        )
    else:
        settings['start_date'] = PERFORMANCE_PERIODS[settings['period']]
        settings['end_date'] = pd.to_datetime(portfolio_df["End Date"]).max()

    settings['decimals'] = settings_row2[3].segmented_control(
        "Decimal places",
        [2, 4, 8, 12],
        default=2
    )

    return settings


def render_classification_selector(asset_class, column):
    """
    Render classification criteria selector based on asset class.
    """
    criteria_list = CLASSIFICATION_CRITERIA[asset_class]
    return column.radio("Allocation criteria", criteria_list)


def render_analysis_results(master_df, details_df, classification_criteria, decimal_places):
    """
    Render the analysis results in two panels (master and details).
    """
    # Create layout columns
    analysis_master_row = st.columns([0.25, 0.75])
    analysis_details_row = st.columns([0.25, 0.75])

    # Render classification selector
    classification_value = render_classification_selector_with_results(
        master_df,
        classification_criteria,
        analysis_master_row[0],
        analysis_details_row[0]
    )

    # Render master analysis
    analysis_master_row[1].markdown("**Performance analysis:**")
    analysis_master_row[1].dataframe(
        style_dataframe(master_df, decimal_places),
        hide_index=True,
        width=1000,
        height=dataframe_height(master_df)
    )

    # Render details analysis
    analysis_details_row[1].markdown("**Instruments details:**")
    analysis_details_row[1].dataframe(
        style_dataframe(details_df, decimal_places),
        hide_index=True,
        width=1000,
        height=dataframe_height(details_df)
    )

    return classification_value


def render_classification_selector_with_results(master_df, classification_criteria,
                                                 master_column, details_column):
    """
    Render classification criteria radio buttons and return selected value.
    """
    classification_values = [
        val for val in master_df[classification_criteria].to_list()
        if val not in ["Total"]
    ]

    classification_value = details_column.radio(
        f"Select a {classification_criteria}:",
        classification_values
    )

    return classification_value
