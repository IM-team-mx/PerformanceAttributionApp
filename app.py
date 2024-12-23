from email.policy import default

import streamlit as st
import datetime
import pandas as pd
from analysis.data_preparation import prepare_data
from analysis.brinson_fachler import brinson_fachler
from analysis.brinson_fachler_instrument import brinson_fachler_instrument
from analysis.brinson_hood_beebower import brinson_hood_beebower
from analysis.total_returns import total_returns
from analysis.grap_smoothing import grap_smoothing
from utils.styling import highlight_total_row

# Streamlit page configuration
st.set_page_config(
    page_title='Performance attribution',
    page_icon=':bar_chart:',
    layout='wide'
)

# Page title
st.markdown('### :bar_chart: Performance attribution')

# Use TPK data or custom data
data_source_toggle = st.segmented_control("",["TPK data", "Custom data"], default="TPK data")

# Load csv data
classifications_file = "./data/equities_classifications.csv"
if data_source_toggle == "TPK data":
    portfolios_file = "./data/portfolios.csv"
    benchmarks_file = "./data/benchmarks.csv"
else:
    file_upload_row = st.container(border=True).columns(2)
    portfolios_file = file_upload_row[0].file_uploader("portfolios.csv file", help="File produced by the Performance service")
    benchmarks_file = file_upload_row[1].file_uploader("benchmarks.csv file", help="File produced by the Performance service")

# App logic when input files are loaded
if portfolios_file is not None and benchmarks_file is not None:

    # User settings
    settings_row = st.columns(5)
    model = settings_row[0].selectbox('Model', ['Brinson-Fachler', 'Brinson-Hood-Beebower'])
    reference_date = settings_row[1].date_input('Start date', datetime.date(2019, 12, 31))
    decimal_places = settings_row[2].selectbox('Decimal places', (2, 4, 8, 12))

    # Load the data files, replacing NaNs with zeros
    portfolio_df = pd.read_csv(portfolios_file).fillna(0)
    benchmark_df = pd.read_csv(benchmarks_file).fillna(0)
    classifications_df = pd.read_csv(classifications_file).fillna(0)

    # Retrieve the list of portfolios and benchmarks from the dataframes
    portfolios = portfolio_df["Portfolio"].unique()
    benchmarks = benchmark_df["Benchmark"].unique()

    # Allow the user to select the list of portfolios and benchmarks to perform the analysis on
    selected_portfolios = settings_row[3].multiselect("Portfolios", portfolios, default=portfolios[0])
    selected_benchmark = settings_row[4].selectbox("Benchmark", benchmarks)

    # Create 2 rows and 2 columns, left column is for allocation criteria/instrument, right for analysis results
    analysis_master_row = st.columns([0.25, 0.75])
    analysis_detail_row = st.columns([0.25, 0.75])

    # Radio button in the left pane, allowing to select a classification criteria
    classification_criteria = analysis_master_row[0].radio(
        'Allocation criteria',
        ['GICS sector', 'GICS industry group', 'GICS industry', 'GICS sub-industry', 'Region', 'Country'],
    )

    # Prepare the data
    prepared_data = prepare_data(portfolios, benchmarks, portfolio_df, benchmark_df, classifications_df, classification_criteria)

    brinson_fachler_result = brinson_fachler(prepared_data, classification_criteria)
    brinson_hood_beebower_result = brinson_hood_beebower(prepared_data, classification_criteria)

    # Calculate total returns and apply GRAP smoothing
    total_returns_df = total_returns(brinson_fachler_result, reference_date)

    if model == 'Brinson-Fachler':
        grap_result = grap_smoothing(brinson_fachler_result, total_returns_df, model, classification_criteria)
    else:
        grap_result = grap_smoothing(brinson_hood_beebower_result, total_returns_df, model, classification_criteria)

    # Format the DataFrame for display
    df_style = '{:,.' + str(decimal_places) + '%}'
    styled_grap_result_df = grap_result.style.apply(highlight_total_row, axis=1)

    if model == 'Brinson-Fachler':
        styled_grap_result_df = styled_grap_result_df.format({
            'Allocation': df_style.format,
            'Selection': df_style.format,
            'Excess return': df_style.format
        })
    else:
        styled_grap_result_df = styled_grap_result_df.format({
            'Allocation': df_style.format,
            'Selection': df_style.format,
            'Interaction': df_style.format,
            'Excess return': df_style.format
        })

    # Display main analysis results
    analysis_master_row[1].markdown(f'**{model} Attribution**:')
    analysis_master_row[1].dataframe(styled_grap_result_df, hide_index=True, width=800,
                                     height=(len(grap_result.index) + 1) * 35 + 3)

    if model == 'Brinson-Fachler':
        # Allow user to drill down by classification
        classification_values = [val for val in grap_result[classification_criteria].to_list() if
                                 val not in ['Cash', 'Total']]
        classification_value = analysis_detail_row[0].radio(f'Select a {classification_criteria}:',
                                                            classification_values)

        # Drill-down analysis for specific classification
        brinson_fachler_instrument_result = brinson_fachler_instrument(prepared_data, classification_criteria,
                                                                       classification_value)

        grap_instrument_result = grap_smoothing(brinson_fachler_instrument_result, total_returns_df, model, '')

        # Display detailed instrument-level results
        styled_grap_instrument_result_df = grap_instrument_result.style.apply(highlight_total_row, axis=1)
        styled_grap_instrument_result_df = styled_grap_instrument_result_df.format({'Selection': df_style.format})
        analysis_detail_row[1].markdown('**Instrument Selection Details**:', help='Detailed selection analysis by '
                                                                                  'instrument')
        analysis_detail_row[1].dataframe(styled_grap_instrument_result_df, hide_index=True, width=700,
                                         height=(len(grap_instrument_result.index) + 1) * 35 + 3)