import pandas as pd

def apply_smoothing(df, column, adjustment_factor):
    smoothed_values = (df[column] * df[adjustment_factor]).cumsum()
    df[column] = smoothed_values
    return df

def contribution_smoothing(df, classification_criteria):
    df = df.copy()
    returns_df = df.groupby("Start Date", as_index=False)[["TotalReturn_portfolio", "TotalReturn_benchmark"]].first()

    # Compute cumulative product for portfolio returns
    # For each row i, we want the product of (1+TotalReturn_portfolio) for all rows < i.
    returns_df["portfolio_adjustment_factor"] = (1 + returns_df["TotalReturn_portfolio"]).cumprod().shift(1, fill_value=1)

    # Compute cumulative product for benchmark returns
    # For each row i, we want the product of (1+TotalReturn_benchmark) for all rows < i.
    returns_df["benchmark_adjustment_factor"] = (1 + returns_df["TotalReturn_benchmark"]).cumprod().shift(1, fill_value=1)

    df = pd.merge(df, returns_df[["Start Date", "portfolio_adjustment_factor", "benchmark_adjustment_factor"]], on="Start Date", how="left")
    
    cols_to_apply_smoothing = ["Return", "BM Return"]

    # Apply compounded contribution smoothing to the portfolio return and the benchmark return with their adjustment factors
    df = df.groupby(classification_criteria, group_keys=False).apply(lambda x: apply_smoothing(x, "Return", "portfolio_adjustment_factor"))
    df = df.groupby(classification_criteria, group_keys=False).apply(lambda x: apply_smoothing(x, "BM Return", "benchmark_adjustment_factor"))

    # Compute the excess return
    df["Excess return"] = df["Return"] - df["BM Return"]
    cols_to_apply_smoothing = cols_to_apply_smoothing + ["Excess return"]

    # The compounded returns is the last smoothed value for each classification
    contribution_result_df = df.groupby(classification_criteria, as_index=False)[cols_to_apply_smoothing].last()
    
    # Create the "Total" row
    total_row = {classification_criteria: "Total"}
    for col in cols_to_apply_smoothing:
        total_row[col] = contribution_result_df[col].sum()
    # Prepend the row to the DataFrame
    contribution_result_df = pd.concat([pd.DataFrame([total_row]), contribution_result_df], ignore_index=True)

    return contribution_result_df
