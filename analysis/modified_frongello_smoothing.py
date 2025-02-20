import pandas as pd

def apply_smoothing(df, column):
    cumulative_smoothed = 0
    smoothed_values = []
    for _, row in df.iterrows():
        smoothed = row[column] * row['MF_adjustment_factor_1'] + cumulative_smoothed * row['MF_adjustment_factor_2']
        smoothed_values.append(smoothed)
        cumulative_smoothed += smoothed
    df[column] = smoothed_values
    return df

def modified_frongello_smoothing(df, breakdown):
    df = df.copy()
    returns_df = df.groupby("Start Date", as_index=False)[["TotalReturn_portfolio", "TotalReturn_benchmark"]].first()

    # First factor of the Modified Frongello: average of portfolio compounded returns and benchmark compounded returns
    # up to the previous period (this is why shift is used)
    returns_df["MF_adjustment_factor_1"] = (
            0.5 * (1 + returns_df["TotalReturn_portfolio"]).cumprod() +
            0.5 * (1 + returns_df["TotalReturn_benchmark"]).cumprod()
    ).shift(1, fill_value=1)

    # Second factor of the Modified Frongello: average of the portfolio and benchmark returns for the current period
    returns_df["MF_adjustment_factor_2"] = 0.5 * (returns_df["TotalReturn_portfolio"] + returns_df["TotalReturn_benchmark"])

    # All data required is accessible through the merged df
    df = pd.merge(df, returns_df[["Start Date", "MF_adjustment_factor_1", "MF_adjustment_factor_2"]], on="Start Date", how="left")

    # Modified Frongello application
    # Define the columns to exclude from the Modified Frongello
    excluded_cols = ["Start Date", "TotalReturn_portfolio", "TotalReturn_benchmark", "MF_adjustment_factor_1",
                     "MF_adjustment_factor_2", breakdown]

    # Identify all the columns to apply the Modified Frongello to
    cols_to_apply_smoothing = [col for col in df.columns if col not in excluded_cols]

    # Loop over columns and apply the MF smoothing after grouping data by breakdown
    for col in cols_to_apply_smoothing:
        df = df.groupby(breakdown, group_keys=False).apply(lambda x: apply_smoothing(x, col))

    modified_frongello_result_df = df.groupby(breakdown, as_index=False)[cols_to_apply_smoothing].sum()

    # Create the "Total" row
    total_row = {breakdown: "Total"}
    for col in cols_to_apply_smoothing:
        total_row[col] = df[col].sum()
    # Prepend the row to the DataFrame
    modified_frongello_result_df = pd.concat([pd.DataFrame([total_row]), modified_frongello_result_df],
                                             ignore_index=True)
    return modified_frongello_result_df
