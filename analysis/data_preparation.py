import pandas as pd

def prepare_data(ptf_list, bm, ptf_df, bm_df, classifications_df, start_date, end_date):
    # Filter ptf_df on portfolios in ptf_list, and on the date range, and remove unneeded columns
    ptf_df = ptf_df[ptf_df["Portfolio"].isin(ptf_list)]
    ptf_df = ptf_df[(pd.to_datetime(ptf_df["Start Date"]) >= pd.to_datetime(start_date)) & 
                    (pd.to_datetime(ptf_df["End Date"]) <= pd.to_datetime(end_date))]
    ptf_df = ptf_df.drop(["Portfolio", "End Date"], axis=1)
    ptf_df = ptf_df.groupby(["Start Date", "Instrument", "ProductTaxonomy"]).sum().reset_index()

    # Filter bm_df on bm benchmark, and on the date range, and remove unneeded columns
    bm_df = bm_df[bm_df["Benchmark"] == bm]
    bm_df = bm_df[(pd.to_datetime(bm_df["Start Date"]) >= pd.to_datetime(start_date)) & 
                  (pd.to_datetime(bm_df["End Date"]) <= pd.to_datetime(end_date))]
    bm_df = bm_df.drop(["Benchmark", "End Date"], axis=1)

    merged_df = pd.merge(ptf_df, bm_df, how="outer", on=["Instrument", "ProductTaxonomy", "Start Date"], suffixes=("_portfolio", "_benchmark")).fillna(0)

    # Compute total MVs and total returns per date
    total_mv_returns_columns = ["Start Date", "DeltaMv_portfolio", "DeltaMv_benchmark", "PreviousMv_portfolio", "PreviousMv_benchmark"]
    total_mv_returns_df = merged_df[total_mv_returns_columns]

    merged_df["TotalPreviousMv_portfolio"] = total_mv_returns_df.groupby("Start Date")["PreviousMv_portfolio"].transform("sum")
    merged_df["TotalPreviousMv_benchmark"] = total_mv_returns_df.groupby("Start Date")["PreviousMv_benchmark"].transform("sum")
    merged_df["TotalDeltaMv_portfolio"] = total_mv_returns_df.groupby("Start Date")["DeltaMv_portfolio"].transform("sum")
    merged_df["TotalDeltaMv_benchmark"] = total_mv_returns_df.groupby("Start Date")["DeltaMv_benchmark"].transform("sum")
    merged_df["TotalReturn_portfolio"] = merged_df["TotalDeltaMv_portfolio"] / merged_df["TotalPreviousMv_portfolio"]
    merged_df["TotalReturn_benchmark"] = merged_df["TotalDeltaMv_benchmark"] / merged_df["TotalPreviousMv_benchmark"]

    # Map taxonomies to product types
    taxonomy_to_product_type = {
        "Equities": "Equity",
        "Fund S/R asset": "Equity",
        "Exchange Traded Funds": "Equity",
        "Bonds": "Bond",
        "Callable Bonds": "Bond",
        "Convertible Bonds": "Bond",
        "Fund fee": "Fees",
        "Fund share fee": "Fees",
        "Cash": "Cash"
    }

    # Apply taxonomy, product type mapping and set Derivative to values that aren't matched in the dictionary (all versions of derivatives will be caught)
    merged_df["Product type"] = merged_df["ProductTaxonomy"].map(lambda x: taxonomy_to_product_type.get(x, "Derivative"))

    # Put Cash, Fees and Derivatives as classification for all instruments that are not securities
    columns_to_update = [col for col in classifications_df.columns if col not in ["Product", "Product description", "Product type", "Issuer"]]
    classifications_df.loc[classifications_df["Product type"] == "Cash", columns_to_update] = "Cash"

    merged_df = pd.merge(merged_df, classifications_df, left_on=["Instrument", "Product type"], right_on=["Product", "Product type"], how="left")

    # Update the instrument for Derivatives as the Product description
    merged_df.loc[merged_df["Product type"] == "Derivative", columns_to_update] = "Derivative"
    merged_df.loc[merged_df["Product type"] == "Derivative", "Product description"] = merged_df["Instrument"]

    # Update the instrument for Fees as the Product description
    merged_df.loc[merged_df["Product type"] == "Fees", columns_to_update] = "Fees"
    merged_df.loc[merged_df["Product type"] == "Fees", "Product description"] = merged_df["Instrument"]

    return merged_df

