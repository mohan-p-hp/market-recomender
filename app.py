from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd

app = FastAPI(title="Crop Market Recommender")

# This defines the data structure we expect in a request
class RecommendationRequest(BaseModel):
    farmer_lat: float
    farmer_lon: float
    commodity: str
    quantity_tonnes: float

@app.get("/")
def home():
    return {"message": "Welcome to the Crop Market Recommender API"}

@app.post("/recommend")
def get_recommendations(request: RecommendationRequest):
    """
    API endpoint to get market recommendations.

    NOTE: For this guide, we are returning a sample response.
    In a real application, you would import and call the 
    recommend_markets function from Phase 6 here.
    """
    sample_response = [
        {
            "market_name": "Delhi Mandi",
            "distance_km": 45.2,
            "predicted_price_kg": 25.5,
            "net_profit": 48500,
            "transport_cost": 1000
        },
        {
            "market_name": "Gurgaon Mandi",
            "distance_km": 35.8,
            "predicted_price_kg": 24.0,
            "net_profit": 46200,
            "transport_cost": 800
        }
    ]

    return {"recommendations": sample_response}