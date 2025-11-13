"""
Performance Attribution and Contribution Reconciliation Application

A Streamlit web application for analyzing portfolio performance against benchmarks
using various attribution models and contribution analysis methods.
"""
import streamlit as st
import datetime
import numpy as np
import pandas as pd
from config.settings import PAGE_CONFIG, CLASSIFICATION_CRITERIA
from utils import load_csv_files, validate_dataframes, style_dataframe, dataframe_height
from ui.components import render_settings
from ui.analysis_runner import run_analysis

# Configure Streamlit page
st.set_page_config(**PAGE_CONFIG)

# Page title
st.markdown("### :bar_chart: Performance Attribution and Contribution Reconciliation")
st.text("")
st.text("")

# File upload section
file_upload_row = st.columns(2)
settings_row1 = st.columns(5)

data_source_toggle = settings_row1[0].pills(
    "Data source",
    ["Use TPK data", "Upload csv files"],
    default="Use TPK data",
    key="data_source_toggle"
)

# Load CSV files
classifications_df, portfolio_df, benchmark_df = load_csv_files(
    data_source_toggle,
    file_upload_row
)

# Validate dataframes
correct_format = False
if not portfolio_df.empty and not benchmark_df.empty:
    correct_format = validate_dataframes(portfolio_df, benchmark_df)

# Main application logic
if correct_format:
    # User settings
    asset_class = settings_row1[1].pills("Asset class", ["Equity", "Fixed income"], default="Equity", key="asset_class")
    contribution_attribution = settings_row1[2].pills("Analysis", ["Attribution", "Contribution", "Measurement & Analytics"], default="Attribution", key="contribution_attribution")

    # Model selection in case of Attribution analysis
    if contribution_attribution == "Attribution":
        if asset_class == "Equity":
            model = settings_row1[3].pills("Model", ["Brinson-Fachler", "Brinson-Hood-Beebower"], default="Brinson-Fachler", key="model_equity")
        else:
            model = settings_row1[3].pills("Model", ["Standard fixed income attribution", "with Brinson Fachler on credit (POC)"], default="Standard fixed income attribution", key="model_fixed_income")
            # Define effects list based on fixed income model
            effects_full_list = ["Income", "Yield curve", "Credit", "Rolldown", "Trading", "Global other"]
            if model == "Standard fixed income attribution":
                effects = st.multiselect("Effects", effects_full_list, ["Rolldown", "Income", "Yield curve", "Credit"])
            else:
                effects_brinson = effects_full_list.copy()
                credit_index = effects_brinson.index("Credit")
                effects_brinson[credit_index:credit_index+1] = ["Credit allocation", "Credit selection"]
                effects = st.multiselect("Effects", effects_brinson, ["Rolldown", "Income", "Yield curve", "Credit allocation", "Credit selection"])
                effects_brinson_instrument = list(dict.fromkeys(["Credit" if effect in ["Credit allocation", "Credit selection"] else effect for effect in effects]))
        smoothing_algorithm = settings_row1[4].pills("Smoothing algorithm", ["Frongello", "Modified Frongello"], default="Frongello", key="smoothing_algorithm")

    # Second row of user settings: portfolios, benchmarks, performance period and decimals
    settings_row2 = st.columns(5)

    # Portfolios and benchmark to be loaded
    # Retrieve the list of portfolios and benchmarks from the dataframes
    portfolios = portfolio_df["Portfolio"].unique()
    portfolios = np.sort(portfolios)
    benchmarks = benchmark_df["Benchmark"].unique()
    benchmarks = np.sort(benchmarks)

    # Define the default portfolios and benchmark
    if data_source_toggle == "Use TPK data":
        if asset_class == "Equity":
            default_portfolio = "EUR EQ LARGE CP"
            default_benchmark_index = 0
        else:
            default_portfolio = "LIQ EUR CORP"
            default_benchmark_index = 1
    else:
        default_portfolio = portfolios[0]
        default_benchmark_index = 0


    # Allow the user to select the list of portfolios and benchmarks to perform the analysis on
    selected_portfolios = settings_row2[0].multiselect("Portfolios", portfolios, default_portfolio)
    selected_benchmark = settings_row2[1].selectbox("Benchmark", benchmarks,index=default_benchmark_index)

    # Reference date selection using predefined performance periods
    # Note these are hardcoded dates based on the tpk data
    performance_period = settings_row2[2].pills("Performance period", ["1Y", "YTD","6M","1M", "MTD", "WTD", "1D", "Custom"], default="YTD", key="performance_period")
    performance_period_date_dict = {
        "1Y": datetime.date(2019, 11, 1),
        "YTD": datetime.date(2020, 1, 1),
        "6M": datetime.date(2020, 5, 1),
        "1M": datetime.date(2020, 10, 1),
        "MTD": datetime.date(2020, 10, 1),
        "WTD": datetime.date(2020, 10, 5),
        "1D": datetime.date(2020, 10, 6)
    }

    if performance_period == "Custom":
        start_date = settings_row2[2].date_input("Select start date", datetime.date(2020, 1, 1))
        end_date = settings_row2[2].date_input("Select end date", datetime.date(2020, 10, 6))
    else:
        start_date = performance_period_date_dict[performance_period]
        end_date = pd.to_datetime(portfolio_df["End Date"]).max()

    decimal_places = settings_row2[3].segmented_control("Decimal places", [2, 4, 8, 12], default=2)

    # Add some vertical space
    st.text("")
    st.text("")

    # Create 2 rows and 2 columns, left column is for allocation criteria/instrument, right for analysis results
    analysis_master_row = st.columns([0.25, 0.75])
    analysis_details_row = st.columns([0.25, 0.75])

    if len(selected_portfolios) > 0:
        if contribution_attribution == "Measurement & Analytics":
            frequency = analysis_master_row[0].pills("Frequency", ["daily", "weekly", "monthly"], default="daily", key="measurement_frequency")
            classification_criteria = None
        else:
            frequency = "daily"
            # Render classification criteria selector on the left column (only for attribution/contribution)
            classification_criteria = analysis_master_row[0].radio(
                "Allocation criteria",
                CLASSIFICATION_CRITERIA[asset_class],
                key="classification_criteria"
            )

        # Create settings dict for analysis
        settings = {
            'asset_class': asset_class,
            'analysis_type': contribution_attribution,
            'portfolios': selected_portfolios,
            'benchmark': selected_benchmark,
            'start_date': start_date,
            'end_date': end_date,
            'decimals': decimal_places,
            'frequency': frequency
        }

        if contribution_attribution == "Attribution":
            settings['model'] = model
            settings['smoothing'] = smoothing_algorithm
            if asset_class == "Fixed income":
                settings['effects'] = effects

        # Run the analysis
        master_df, get_instruments = run_analysis(
            settings,
            portfolio_df,
            benchmark_df,
            classifications_df,
            classification_criteria
        )

        # Display results depending on analysis type
        if contribution_attribution == "Measurement & Analytics":
            analysis_master_row[1].markdown("**Return vs Benchmark chart**")
            chart_df = master_df.set_index("Date")
            analysis_master_row[1].line_chart(chart_df)
            # Display instrument-level measurement analytics (volatility table, etc.)
            analysis_details_row[1].markdown("**Measurement analytics:**")
            details_df = get_instruments(None)
            analysis_details_row[1].dataframe(
                style_dataframe(details_df, settings['decimals']),
                hide_index=True,
                width=1000,
                height=dataframe_height(details_df)
            )
        else:
            # Display master-level results for Attribution/Contribution
            analysis_master_row[1].markdown("**Performance analysis:**")
            analysis_master_row[1].dataframe(
                style_dataframe(master_df, settings['decimals']),
                hide_index=True,
                width=1000,
                height=dataframe_height(master_df)
            )

            # Get classification values for drill-down
            classification_values = [
                val for val in master_df[classification_criteria].to_list()
                if val not in ["Total"]
            ]

            # Render classification value selector
            classification_value = analysis_details_row[0].radio(
                f"Select a {classification_criteria}:",
                classification_values,
                key="classification_value"
            )

            # Get instrument-level details
            details_df = get_instruments(classification_value)

            # Display instrument-level results
            analysis_details_row[1].markdown("**Instruments details:**")
            analysis_details_row[1].dataframe(
                style_dataframe(details_df, settings['decimals']),
                hide_index=True,
                width=1000,
                height=dataframe_height(details_df)
            )

