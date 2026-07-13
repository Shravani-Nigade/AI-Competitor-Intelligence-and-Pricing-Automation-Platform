import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# ---------------------------------
# PAGE CONFIG
# ---------------------------------
st.set_page_config(
    page_title="Seasonal Product Price Prediction",
    layout="wide"
)

# ---------------------------------
# LOAD DATA
# ---------------------------------
df = pd.read_csv("lavanya_products_seasonal_predictions.csv")
df.columns = df.columns.str.strip()

# Convert date
df["Scrape Date"] = pd.to_datetime(df["Scrape Date"], errors="coerce")
df["Year"] = df["Scrape Date"].dt.year
df["Month"] = df["Scrape Date"].dt.month_name()

# ---------------------------------
# HELPER FUNCTION
# ---------------------------------
def make_clickable(url):
    return f'<a href="{url}" target="_blank">🛒 Buy Now</a>'

# ---------------------------------
# TITLE
# ---------------------------------
st.title("📊 Seasonal Product Price Trend & Purchase Dashboard")

# ---------------------------------
# SIDEBAR FILTERS
# ---------------------------------
st.sidebar.header("🔍 Filters")

festival = st.sidebar.selectbox(
    "Select Festival",
    ["Normal", "Diwali", "Dussehra", "Christmas"]
)

festival_price_map = {
    "Normal": "Predicted_Normal_Price",
    "Diwali": "Predicted_Diwali_Price",
    "Dussehra": "Predicted_Dussehra_Price",
    "Christmas": "Predicted_Christmas_Price"
}
price_col = festival_price_map[festival]

# Year filter
years = sorted(df["Year"].dropna().unique())
selected_year = st.sidebar.selectbox("Select Year", years)

# Month filter
months = ["All"] + sorted(df["Month"].dropna().unique())
selected_month = st.sidebar.selectbox("Select Month", months)

# Availability
available_only = st.sidebar.checkbox("Show Available Products Only")

# Rating filter
min_rating = st.sidebar.slider("Minimum Star Rating", 0.0, 5.0, 3.0)

# Price range
min_price = int(df[price_col].min())
max_price = int(df[price_col].max())

price_range = st.sidebar.slider(
    f"{festival} Price Range (₹)",
    min_price,
    max_price,
    (min_price, max_price)
)

# ---------------------------------
# APPLY FILTERS
# ---------------------------------
filtered_df = df[df["Year"] == selected_year]

if selected_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == selected_month]

if available_only:
    filtered_df = filtered_df[filtered_df["Availability"] == "Yes"]

filtered_df = filtered_df[
    (filtered_df["Star Rating"] >= min_rating) &
    (filtered_df[price_col] >= price_range[0]) &
    (filtered_df[price_col] <= price_range[1])
]

# ---------------------------------
# ADD BUY LINK
# ---------------------------------
filtered_df["Buy Link"] = filtered_df["Product URL"].apply(make_clickable)

# ---------------------------------
# DISPLAY PRODUCTS
# ---------------------------------
st.subheader(f"📄 Filtered Products ({festival} Season)")

st.write(
    filtered_df[
        ["Product Name", price_col, "Star Rating", "Availability", "Month", "Buy Link"]
    ].to_html(escape=False),
    unsafe_allow_html=True
)

# ---------------------------------
# PRICE DISTRIBUTION
# ---------------------------------
st.subheader("📈 Price Distribution")

fig, ax = plt.subplots()
ax.hist(filtered_df[price_col], bins=10)
ax.set_xlabel("Predicted Price (₹)")
ax.set_ylabel("Product Count")
ax.set_title(f"{festival} Price Distribution")
st.pyplot(fig)

# ---------------------------------
# MONTH-WISE TREND
# ---------------------------------
st.subheader("📉 Month-wise Average Price Trend")

trend_df = filtered_df.groupby("Month")[price_col].mean()
st.line_chart(trend_df)

# ---------------------------------
# FESTIVAL COMPARISON
# ---------------------------------
st.subheader("🎉 Festival Price Comparison")

comparison_cols = [
    "Predicted_Normal_Price",
    "Predicted_Diwali_Price",
    "Predicted_Dussehra_Price",
    "Predicted_Christmas_Price"
]

comparison_data = filtered_df[comparison_cols].mean()

fig2, ax2 = plt.subplots()
comparison_data.plot(kind="bar", ax=ax2)
ax2.set_ylabel("Average Price (₹)")
ax2.set_title("Average Price Across Festivals")
st.pyplot(fig2)

# ---------------------------------
# BEST TIME TO BUY
# ---------------------------------
st.subheader("🛒 Best Time to Buy")

best_festival = comparison_data.idxmin().replace("Predicted_", "").replace("_Price", "")
best_price = comparison_data.min()

st.success(
    f"✅ Best time to buy is **{best_festival}** "
    f"with average price ₹{round(best_price, 2)}"
)

# ---------------------------------
# QUICK INSIGHTS
# ---------------------------------
st.subheader("🔎 Quick Insights")

st.write(f"• Average {festival} Price: ₹{round(filtered_df[price_col].mean(), 2)}")
st.write(f"• Maximum {festival} Price: ₹{round(filtered_df[price_col].max(), 2)}")
st.write(f"• Minimum {festival} Price: ₹{round(filtered_df[price_col].min(), 2)}")

# ---------------------------------
# BUY PRODUCT SECTION
# ---------------------------------
st.subheader("🛍️ Buy a Product")

if not filtered_df.empty:
    selected_product = st.selectbox(
        "Select Product",
        filtered_df["Product Name"].unique()
    )

    product_url = filtered_df[
        filtered_df["Product Name"] == selected_product
    ]["Product URL"].values[0]

    st.markdown(
        f"### 👉 [Click here to buy **{selected_product}**]({product_url})",
        unsafe_allow_html=True
    )
else:
    st.warning("No products available for selected filters.")
