# app.py

import pandas as pd
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
from haversine import haversine, Unit
from fastapi.middleware.cors import CORSMiddleware

# --- NEW: Import a standard Python caching tool ---
from functools import lru_cache

# --- Main Application Setup ---
app = FastAPI(title="Crop Market Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Data Loading and Feature Engineering ---
# MODIFIED: Use @lru_cache instead of @st.cache_data
@lru_cache(maxsize=None)
def load_data():
    """This function will now be cached using a standard Python utility."""
    df = pd.read_csv('data/market_prices.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

def create_features(df):
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

def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine((lat1, lon1), (lat2, lon2), unit=Unit.KILOMETERS)

def calculate_net_profit(predicted_price_per_kg, quantity_tonnes, distance_km):
    total_revenue = predicted_price_per_kg * quantity_tonnes * 1000
    transport_cost = (distance_km * 2 * quantity_tonnes) + 500
    market_fees = total_revenue * (1.5 / 100)
    other_costs = 200 * quantity_tonnes
    total_costs = transport_cost + market_fees + other_costs
    net_profit = total_revenue - total_costs
    return {'net_profit': net_profit}

class RecommendationRequest(BaseModel):
    farmer_lat: float
    farmer_lon: float
    commodity: str
    quantity_tonnes: float
    selected_date: str

@app.get("/")
def home():
    return {"message": "Welcome to the Crop Market Recommender API"}

@app.post("/recommend")
def get_recommendations(request: RecommendationRequest):
    all_recommendations = []
    model = joblib.load(f'models/{request.commodity}_price_model.pkl')
    feature_columns = joblib.load(f'models/{request.commodity}_features.pkl')
    start_date = datetime.strptime(request.selected_date, '%Y-%m-%d').date()
    sample_markets = [
        {'name': 'Delhi_Mandi', 'lat': 28.6, 'lon': 77.2},
        {'name': 'Mumbai_Mandi', 'lat': 19.0, 'lon': 72.8},
        {'name': 'Pune_Mandi', 'lat': 18.5, 'lon': 73.8},
    ]

    for i in range(3):
        prediction_date = start_date + timedelta(days=i)
        for market in sample_markets:
            distance = calculate_distance(request.farmer_lat, request.farmer_lon, market['lat'], market['lon'])
            latest_market_data = df_features[(df_features['market_name'] == market['name']) & (df_features['commodity'] == request.commodity)].tail(1)
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
            profit_info = calculate_net_profit(predicted_price_per_kg, request.quantity_tonnes, distance)
            
            all_recommendations.append({
                'date': prediction_date.strftime('%Y-%m-%d'),
                'market_name': market['name'],
                'distance_km': round(distance, 1),
                'predicted_price_kg': round(predicted_price_per_kg, 2),
                'net_profit': round(profit_info['net_profit'])
            })

    return {"recommendations": all_recommendations}