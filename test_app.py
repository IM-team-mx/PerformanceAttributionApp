import datetime
import pandas as pd
from analysis.data_preparation import prepare_data
from analysis.brinson_fachler import brinson_fachler, brinson_fachler_instrument
from analysis.brinson_hood_beebower import brinson_hood_beebower, brinson_hood_beebower_instrument
from analysis.effects_analysis import effects_analysis, effects_analysis_instrument
from analysis.grap_smoothing import grap_smoothing
from analysis.modified_frongello_smoothing import modified_frongello_smoothing

# File paths
classifications_file = "./data/classifications.csv"
portfolios_file = "./data/portfolios.csv"
benchmarks_file = "./data/benchmarks.csv"

# Test parameters
model = "Brinson-Fachler"
# model = "Brinson-Hood-Beebower"
# model = "Effects analysis"
# smoothing = "GRAP"
smoothing = "Modified frongello"
start_date = datetime.date(2019, 12, 31)
end_date = datetime.date(2020, 10, 6)
portfolios = ["EUR EQ LARGE CP"]
# portfolios = ["LIQ EUR CORP"]
benchmark = "EURO STOXX 50"
# benchmark = "IBOXX E LIQ COR"
classification_criteria = "GICS sector"
classification_value = "Financials"
# classification_criteria = "S&P rating"
# classification_value = "A"

# Load and transform data
portfolio_df = pd.read_csv(portfolios_file)
benchmark_df = pd.read_csv(benchmarks_file)
classifications_df = pd.read_csv(classifications_file)

data_df = prepare_data(portfolios, benchmark, portfolio_df,benchmark_df, classifications_df, start_date, end_date)

if model == "Brinson-Fachler":
    attribution_df = brinson_fachler(data_df, classification_criteria)
    instruments_df = brinson_fachler_instrument(data_df, classification_criteria, classification_value)
elif model == "Brinson-Hood-Beebower":
    attribution_df = brinson_hood_beebower(data_df, classification_criteria)
    instruments_df = brinson_hood_beebower_instrument(data_df, classification_criteria, classification_value)
else:
    attribution_df = effects_analysis(data_df, classification_criteria)
    instruments_df = effects_analysis_instrument(data_df, classification_criteria, classification_value)


if smoothing == "GRAP":
    smoothed_attribution_df = grap_smoothing(attribution_df, classification_criteria)
    smoothed_instrument_df = grap_smoothing(instruments_df, "Product description")
else:
    smoothed_attribution_df = modified_frongello_smoothing(attribution_df, classification_criteria)
    smoothed_instrument_df = modified_frongello_smoothing(instruments_df, "Product description")


print(smoothed_attribution_df)


