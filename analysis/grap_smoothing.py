import pandas as pd


def grap_smoothing(df, breakdown):
    df = df.copy()
    returns_df = df.groupby("Start Date", as_index=False)[["TotalReturn_portfolio", "TotalReturn_benchmark"]].first()

    # Compute cumulative product for portfolio returns
    # For each row i, we want the product of (1+TotalReturn_portfolio) for all rows < i.
    returns_df["cumulative_portfolio"] = (1 + returns_df["TotalReturn_portfolio"]).cumprod().shift(1, fill_value=1)

    # Compute reverse cumulative product for benchmark returns
    # For each row i, we want the product of (1+TotalReturn_benchmark) for all rows > i.
    returns_df["cumulative_benchmark"] = (1 + returns_df["TotalReturn_benchmark"])[::-1].cumprod()[::-1].shift(-1, fill_value=1)

    # The GRAP factor is the product of the two cumulative values
    returns_df["GRAP factor"] = returns_df["cumulative_portfolio"] * returns_df["cumulative_benchmark"]

    # Keep only the necessary columns and add the GRAP factor to the main dataframe
    returns_df = returns_df[["Start Date", "GRAP factor"]]
    df.drop(["TotalReturn_portfolio", "TotalReturn_benchmark"], axis=1, inplace=True)
    df = pd.merge(df, returns_df, on="Start Date", how="left")

    # GRAP factor application
    # Define the columns to exclude from the GRAP factor multiplication
    excluded_cols = ["Start Date", "GRAP factor", breakdown]
    cols_to_multiply = [col for col in df.columns if col not in excluded_cols]

    # Multiply those columns by the "GRAP Factor" column row-by-row
    df[cols_to_multiply] = df[cols_to_multiply].mul(df["GRAP factor"], axis=0)

    # Sum outputs across all dates
    grap_result_df = df.groupby(breakdown, as_index=False)[cols_to_multiply].sum()

    # Create the "Total" row
    total_row = {breakdown: "Total"}
    for col in cols_to_multiply:
        total_row[col] = df[col].sum()
    # Prepend the row to the DataFrame
    grap_result_df = pd.concat([pd.DataFrame([total_row]), grap_result_df], ignore_index=True)

    return grap_result_df
