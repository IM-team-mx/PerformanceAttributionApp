import streamlit as st
import datetime
import numpy as np
import pandas as pd
from analysis.data_preparation import prepare_data
from analysis.brinson_fachler import brinson_fachler, brinson_fachler_instrument
from analysis.brinson_hood_beebower import brinson_hood_beebower, brinson_hood_beebower_instrument
from analysis.effects_analysis import effects_analysis, effects_analysis_instrument
from analysis.contribution import contribution, contribution_instrument
from analysis.grap_smoothing import grap_smoothing
from analysis.modified_frongello_smoothing import modified_frongello_smoothing
from analysis.contribution_smoothing import contribution_smoothing
from utils.styling import style_dataframe, dataframe_height
from utils.csv_loading import load_csv_files, validate_dataframes

# Streamlit page configuration
st.set_page_config(
    page_title="Performance contribution and attribution",
    page_icon=":bar_chart:",
    layout="wide"
)

# Page title
st.markdown("### :bar_chart: Performance Attribution and Contribution Reconciliation")

# Add some vertical space
st.text("")
st.text("")

# Placeholder for csv files upload
file_upload_row = st.columns(2)

# First row of user settings
settings_row1 = st.columns(5)
data_source_toggle = settings_row1[0].pills("Data source", ["Use TPK data", "Upload csv files"],
                                          default="Use TPK data")

# Load csv files
classifications_df, portfolio_df, benchmark_df = load_csv_files(data_source_toggle, file_upload_row)

# Check if the columns of the loaded files are the expected ones
correct_format = False
if not portfolio_df.empty and not benchmark_df.empty:
    correct_format = validate_dataframes(portfolio_df, benchmark_df)


# App logic when input files are loaded with a correct format
if correct_format:

    # User settings
    asset_class = settings_row1[1].pills("Asset class", ["Equity", "Fixed income"], default="Equity")
    contribution_attribution = settings_row1[2].pills("Analysis", ["Attribution", "Contribution"], default="Attribution")

    # Model selection in case of Attribution analysis
    if contribution_attribution == "Attribution":
        if asset_class == "Equity":
            model = settings_row1[3].pills("Model", ["Brinson-Fachler", "Brinson-Hood-Beebower"], default="Brinson-Fachler")
        else:
            model = settings_row1[3].pills("Model", ["Fixed income attribution"], default="Fixed income attribution", disabled=True)
            effects_full_list = ["Income", "Yield curve", "Credit", "Rolldown", "Trading", "Global other"]
            default_effects = ["Income", "Yield curve", "Credit"]
            effects = st.multiselect("Effects", effects_full_list, default_effects)
        smoothing_algorithm = settings_row1[4].pills("Smoothing algorithm", ["Frongello", "Modified Frongello"], default="Frongello")

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
    performance_period = settings_row2[2].pills("Performance period", ["YTD", "MTD", "WTD", "1D", "Custom"], default="YTD")
    performance_period_date_dict = {
        "YTD": datetime.date(2019, 12, 31),
        "MTD": datetime.date(2020, 9, 30),
        "WTD": datetime.date(2020, 10, 2),
        "1D": datetime.date(2020, 10, 5)
    }

    if performance_period == "Custom":
        start_date = settings_row2[2].date_input("Select start date", datetime.date(2019, 12, 31))
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
        # Radio button in the left pane, allowing to select a classification criteria
        if asset_class == "Fixed income":
            classification_criteria = analysis_master_row[0].radio(
                "Allocation criteria",
                ["S&P rating", "Fitch rating", "Moody's rating", "GICS sector", "GICS industry group", "GICS industry", "GICS sub-industry", "Region", "Country"],
            )
        else:
            classification_criteria = analysis_master_row[0].radio(
                "Allocation criteria",
                ["GICS sector", "GICS industry group", "GICS industry", "GICS sub-industry", "Region", "Country"],
            )

        # Prepare the data
        data_df = prepare_data(selected_portfolios, selected_benchmark, portfolio_df, benchmark_df, classifications_df, start_date, end_date)

        # Apply the requested analysis
        if contribution_attribution == "Contribution":
            master_df = contribution(data_df, classification_criteria)
            master_df = contribution_smoothing(master_df, classification_criteria)
        else:
            # Apply the model (without any smoothing)
            if model == "Brinson-Fachler":
                master_df = brinson_fachler(data_df, classification_criteria)
            elif model == "Brinson-Hood-Beebower":
                master_df = brinson_hood_beebower(data_df, classification_criteria)
            elif model == "Fixed income attribution":
                master_df = effects_analysis(data_df, classification_criteria, effects)

            # Apply the smoothing
            if smoothing_algorithm == "Frongello":
                master_df = grap_smoothing(master_df, classification_criteria)
            elif smoothing_algorithm == "Modified Frongello":
                master_df = modified_frongello_smoothing(master_df, classification_criteria)


        analysis_master_row[1].markdown("**Performance analysis:**")
        analysis_master_row[1].dataframe(
            style_dataframe(master_df, decimal_places),
            hide_index=True,
            width=1000,
            height=dataframe_height(master_df)
        )

        # Drill-down analysis for specific classification
        # Allow user to drill down by classification
        classification_values = [val for val in master_df[classification_criteria].to_list() if
                                 val not in ["Total"]]
        classification_value = analysis_details_row[0].radio(f"Select a {classification_criteria}:",
                                                             classification_values)

        # Apply the requested analysis at instrument level
        if contribution_attribution == "Contribution":
            instruments_df = contribution_instrument(data_df, classification_criteria, classification_value)
            details_instruments_df = contribution_smoothing(instruments_df, "Product description")
        else:
            # Apply the model (without any smoothing)
            if model == "Brinson-Fachler":
                instruments_df = brinson_fachler_instrument(data_df, classification_criteria, classification_value)
            elif model == "Brinson-Hood-Beebower":
                instruments_df = brinson_hood_beebower_instrument(data_df, classification_criteria, classification_value)
            elif model == "Fixed income attribution":
                instruments_df = effects_analysis_instrument(data_df, classification_criteria, classification_value, effects)

            # Apply the smoothing
            if smoothing_algorithm == "Frongello":
                details_instruments_df = grap_smoothing(instruments_df,"Product description")
            elif smoothing_algorithm == "Modified Frongello":
                details_instruments_df = modified_frongello_smoothing(instruments_df, "Product description")

        analysis_details_row[1].markdown("**Instruments details**:")
        analysis_details_row[1].dataframe(
            style_dataframe(details_instruments_df, decimal_places),
            hide_index=True,
            width=1000,
            height=dataframe_height(details_instruments_df)
        )