import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import joblib
from haversine import haversine, Unit

st.set_page_config(layout="wide")
st.title("🌾 Smart Crop Market Recommender")
st.write("Find the best markets to sell your crops for maximum profit!")

# --- COPY THE LOGIC FROM PHASE 6 HERE ---
# Load data once to improve performance
@st.cache_data
def load_data():
    df = pd.read_csv('data/market_prices.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

def create_features(df):
    # This is the feature creation logic from Phase 3
    df = df.sort_values(['market_name', 'commodity', 'date'])
    df['price_yesterday'] = df.groupby(['market_name', 'commodity'])['modal_price'].shift(1)
    df['price_last_week'] = df.groupby(['market_name', 'commodity'])['modal_price'].shift(7)
    df['price_avg_7days'] = df.groupby(['market_name', 'commodity'])['modal_price'].shift(1).rolling(7).mean()
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['arrivals_yesterday'] = df.groupby(['market_name', 'commodity'])['arrivals_qty'].shift(1)
    df = df.dropna()
    return df

df_raw = load_data()
df_features = create_features(df_raw)

# These are the profit/distance functions from Phase 5
def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine((lat1, lon1), (lat2, lon2), unit=Unit.KILOMETERS)

def calculate_net_profit(predicted_price_per_kg, quantity_tonnes, distance_km, market_fees_percent=1.5):
    total_revenue = predicted_price_per_kg * quantity_tonnes * 1000
    transport_cost = (distance_km * 2 * quantity_tonnes) + 500
    market_fees = total_revenue * (market_fees_percent / 100)
    other_costs = 200 * quantity_tonnes
    total_costs = transport_cost + market_fees + other_costs
    net_profit = total_revenue - total_costs
    return {'net_profit': net_profit, 'total_costs': total_costs, 'revenue': total_revenue}

# This is the main recommendation function from Phase 6
def recommend_markets(farmer_lat, farmer_lon, commodity, quantity_tonnes, available_markets):
    recommendations = []
    model = joblib.load(f'models/{commodity}_price_model.pkl')
    feature_columns = joblib.load(f'models/{commodity}_features.pkl')
    prediction_date = datetime.now().date() + timedelta(days=1)

    for market in available_markets:
        distance = calculate_distance(farmer_lat, farmer_lon, market['lat'], market['lon'])
        latest_market_data = df_features[(df_features['market_name'] == market['name']) & (df_features['commodity'] == commodity)].tail(1)
        if latest_market_data.empty: continue
        
        features_for_prediction = pd.DataFrame(columns=feature_columns)
        features_for_prediction.loc[0, 'price_yesterday'] = latest_market_data['modal_price'].values[0]
        features_for_prediction.loc[0, 'price_last_week'] = latest_market_data['price_last_week'].values[0]
        features_for_prediction.loc[0, 'price_avg_7days'] = latest_market_data['price_avg_7days'].values[0]
        features_for_prediction.loc[0, 'day_of_week'] = prediction_date.weekday()
        features_for_prediction.loc[0, 'month'] = prediction_date.month
        features_for_prediction.loc[0, 'is_weekend'] = 1 if prediction_date.weekday() in [5, 6] else 0
        features_for_prediction.loc[0, 'arrivals_yesterday'] = latest_market_data['arrivals_qty'].values[0]
        features_for_prediction.loc[0, 'market_lat'] = market['lat']
        features_for_prediction.loc[0, 'market_lon'] = market['lon']

        predicted_price_per_quintal = model.predict(features_for_prediction)[0]
        predicted_price_per_kg = predicted_price_per_quintal / 100
        profit_info = calculate_net_profit(predicted_price_per_kg, quantity_tonnes, distance)
        
        recommendations.append({
            'Market': market['name'],
            'Distance (km)': round(distance, 1),
            'Predicted Price (₹/kg)': round(predicted_price_per_kg, 2),
            'Net Profit (₹)': round(profit_info['net_profit'])
        })
    
    recommendations.sort(key=lambda x: x['Net Profit (₹)'], reverse=True)
    return recommendations[:3]

# --- User Inputs ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Your Farm Location")
    farmer_lat = st.number_input("Latitude", value=28.6, format="%.4f")
    farmer_lon = st.number_input("Longitude", value=77.2, format="%.4f")
with col2:
    st.subheader("Your Crop Details")
    commodity = st.selectbox("Select Crop Type", ["Tomato"]) # Only Tomato model is trained
    quantity = st.number_input("Quantity (in tonnes)", value=2.0, min_value=0.1, step=0.5)

# This is the database of markets our system knows
sample_markets = [
    {'name': 'Delhi_Mandi', 'lat': 28.6, 'lon': 77.2},
    {'name': 'Mumbai_Mandi', 'lat': 19.0, 'lon': 72.8},
    {'name': 'Pune_Mandi', 'lat': 18.5, 'lon': 73.8},
]

# --- Button to Trigger Recommendation ---
if st.button("Find Best Markets 🚀", use_container_width=True):
    st.write("---")
    st.subheader("🏆 Top Recommendations")
    
    # THIS IS THE FIX: Call the function with the user's inputs
    recommendations = recommend_markets(farmer_lat, farmer_lon, commodity, quantity, sample_markets)
    
    if not recommendations:
        st.warning("Could not generate recommendations. Please try different inputs.")
    else:
        df = pd.DataFrame(recommendations)
        best_market = df.iloc[0]
        st.success(f"💡 **Best Choice**: Sell at **{best_market['Market']}** to earn an estimated **₹{best_market['Net Profit (₹)']}** total profit!")
        st.dataframe(df, use_container_width=True, hide_index=True)