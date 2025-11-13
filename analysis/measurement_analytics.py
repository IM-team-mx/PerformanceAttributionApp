import pandas as pd
import numpy as np

def measurement_analytics_master(merged_df: pd.DataFrame, classification_criteria=None, frequency: str = "daily") -> pd.DataFrame:
    daily_returns = calculate_measurement_analytics(merged_df, frequency=frequency)
    # Compute cumulative returns (product of growth factors: (1+r1)*(1+r2)*...)
    # This gives cumulative growth from the start of the period
    daily_returns["Fund_Factor"] = (1 + daily_returns["TotalReturn_portfolio"]).cumprod()
    daily_returns["BM_Factor"] = (1 + daily_returns["TotalReturn_benchmark"]).cumprod()
    
    # Convert to cumulative percent return (with first point = 0%, second point = return from day 1, etc.)
    # Cumulative return = (Factor - 1) * 100, so baseline (Factor=1) = 0%
    daily_returns["Return"] = (daily_returns["Fund_Factor"] - 1) * 100
    daily_returns["BM return"] = (daily_returns["BM_Factor"] - 1) * 100
    daily_returns["Excess return"] = daily_returns["Return"] - daily_returns["BM return"]
    
    # Convert dates to date objects
    daily_returns["Date"] = pd.to_datetime(daily_returns["Start Date"]).dt.date
    result = daily_returns[["Date", "Return", "BM return", "Excess return"]].copy()

    first_date = result.loc[0, "Date"]
    # first_date is already a datetime.date object, convert to datetime for timedelta arithmetic
    baseline_date = pd.to_datetime(first_date) - pd.Timedelta(days=1)
    baseline_row = pd.DataFrame([{
        "Date": baseline_date.date(),
        "Return": 0.0,
        "BM return": 0.0,
        "Excess return": 0.0
    }])
    result = pd.concat([baseline_row, result], ignore_index=True)

    return result

def measurement_analytics_instrument(merged_df: pd.DataFrame, classification_criteria=None, classification_value=None, frequency: str = "daily"):
    daily_returns = calculate_measurement_analytics(merged_df, frequency=frequency)
    # keep csv export for debugging
    daily_returns.to_csv("debug_measurement_instrument.csv", index=False)

    # Map frequency to periods per year for annualization
    periods_per_year = {"daily": 252, "weekly": 52, "monthly": 12}
    n = periods_per_year.get(frequency, 252)

    ptf_returns = daily_returns.get("TotalReturn_portfolio", pd.Series(dtype=float))
    bm_returns = daily_returns.get("TotalReturn_benchmark", pd.Series(dtype=float))

    # Volatility - using population std dev for these and not annualizing - we should consider this further
    vol = ptf_returns.std(ddof=0)
    bmk_vol = bm_returns.std(ddof=0)

    # Tracking error - std population deviation of excess returns
    tracking_error = (ptf_returns - bm_returns).std(ddof=0)

    # Max drawdown

    # Beta
    cov = np.cov(ptf_returns, bm_returns, ddof=0)[0, 1]
    var_bmk = np.var(bm_returns, ddof=0)
    beta = cov / var_bmk

    # Correlation
    var_ptf = np.var(ptf_returns, ddof=0)
    correlation = cov / (np.sqrt(var_ptf) * np.sqrt(var_bmk))

    # Information ratio

    # Jensen alpha

    # Sharpe ratio

    # Sortino ratio

    # Treynor ratio

    return pd.DataFrame([
        {"Metric": "Volatility", "Value": vol},
        {"Metric": "Benchmark volatility", "Value": bmk_vol,},
        {"Metric": "Tracking error", "Value": tracking_error,},
        # {"Metric": "Max drawdown", "Value": max_drawdown,},
        {"Metric": "Beta", "Value": beta,},
        {"Metric": "Correlation", "Value": correlation,}
        # {"Metric": "Information ratio", "Value": information_ratio,},
        # {"Metric": "Jensen alpha", "Value": jensen_alpha,},
        # {"Metric": "Sharpe ratio", "Value": sharpe_ratio,},
        # {"Metric": "Sortino ratio", "Value": sortino_ratio,},
        # {"Metric": "Treynor ratio", "Value": treynor_ratio,},
    ])


def calculate_measurement_analytics(merged_df: pd.DataFrame, frequency: str = "daily") -> pd.DataFrame:
    """
    Simply compounds daily returns to the requested frequency and calculates cumulative returns.
    Leverages pre-computed TotalReturn_* from prepare_data to avoid duplicating aggregation logic.
    """

    # Extract unique daily returns (TotalReturn_* are already aggregated at portfolio level per day in prepare_data)
    df = merged_df[["Start Date", "TotalReturn_portfolio", "TotalReturn_benchmark"]].drop_duplicates(subset=["Start Date"]).sort_values("Start Date").reset_index(drop=True)
    df["Start Date"] = pd.to_datetime(df["Start Date"])
    
    # Compound daily returns to requested frequency
    if frequency == "daily":
        # Use daily returns as-is
        daily_returns = df.copy()
    elif frequency in ("weekly", "monthly"):
        # Set index for resampling
        df.index = df["Start Date"]
        
        # Compound returns: (1 + r1) * (1 + r2) * ... - 1
        resample_rule = "W" if frequency == "weekly" else "M"
        daily_returns = df.groupby(pd.Grouper(freq=resample_rule)).agg({
            "TotalReturn_portfolio": lambda x: (1 + x).prod() - 1,
            "TotalReturn_benchmark": lambda x: (1 + x).prod() - 1
        }).reset_index()
        daily_returns = daily_returns[daily_returns["TotalReturn_portfolio"].notna() | daily_returns["TotalReturn_benchmark"].notna()].reset_index(drop=True)
    else:
        daily_returns = df.copy()
    
    return daily_returns