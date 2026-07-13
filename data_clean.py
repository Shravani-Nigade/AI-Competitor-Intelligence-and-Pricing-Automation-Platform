import csv
import re
import pandas as pd
from datetime import datetime

# Input and output files
input_file = "clean_products_ambraee_com_20250928_170221.csv"
output_file_cleaned = "clean_products_cleaned.csv"
output_file_final = "clean_products_final.csv"

def extract_price(text):
    """Extract numeric value from price text"""
    if pd.isna(text) or str(text).strip().upper() == "NA":
        return ""
    match = re.search(r"\d[\d,]*\.?\d*", str(text).replace(",", ""))
    return match.group(0) if match else ""

# ---------------- Step 1: Load and Basic Cleaning ----------------
df = pd.read_csv(input_file)

# ✅ Clean price columns
for col in ["Product Price", "Regular Price", "Discounted Price"]:
    if col in df.columns:
        df[col] = df[col].apply(extract_price)

# ✅ Drop columns with all NA/empty values
df = df.dropna(axis=1, how="all")  # all NaN
df = df.loc[:, ~df.apply(lambda col: all(str(x).strip().upper() == "NA" or str(x).strip() == "" for x in col))]

# ✅ Remove duplicate product names (keep first)
if "Product Name" in df.columns:
    df = df.drop_duplicates(subset=["Product Name"], keep="first")

# Save basic cleaned file
df.to_csv(output_file_cleaned, index=False, encoding="utf-8-sig")
print(f"✅ Basic cleaned dataset saved to {output_file_cleaned}")

# ---------------- Step 2: Enriched Dataset ----------------
# Convert price columns to numeric
if "Regular Price" in df.columns:
    df["Regular Price"] = pd.to_numeric(df["Regular Price"], errors="coerce")
if "Discounted Price" in df.columns:
    df["Discounted Price"] = pd.to_numeric(df["Discounted Price"], errors="coerce")

# Add new columns
if "Regular Price" in df.columns and "Discounted Price" in df.columns:
    df["Actual Price"] = df["Regular Price"]
    df["Discounted Price Clean"] = df["Discounted Price"]
    df["Price Difference"] = df["Regular Price"] - df["Discounted Price"]
    df["Discount %"] = (df["Price Difference"] / df["Regular Price"]) * 100
    df["Discount %"] = df["Discount %"].round(2)

# Published Date (today)
df["Published Date"] = datetime.today().strftime("%Y-%m-%d")

# Save final enriched dataset
df.to_csv(output_file_final, index=False, encoding="utf-8-sig")
print(f"✅ Final enriched dataset saved to {output_file_final}")
