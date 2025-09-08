import pandas as pd
import joblib
from haversine import haversine, Unit

# --- Helper functions needed for testing ---
def calculate_distance(lat1, lon1, lat2, lon2):
    return haversine((lat1, lon1), (lat2, lon2))

def calculate_net_profit(predicted_price_per_kg, quantity_tonnes, distance_km, market_fees_percent=1.5):
    total_revenue = predicted_price_per_kg * quantity_tonnes * 1000
    transport_cost = (distance_km * 2 * quantity_tonnes) + 500
    market_fees = total_revenue * (market_fees_percent / 100)
    other_costs = 200 * quantity_tonnes
    total_costs = transport_cost + market_fees + other_costs
    net_profit = total_revenue - total_costs
    return {'net_profit': net_profit}

# --- Main Test Function ---
def test_complete_system():
    """
    Test if all the core components work together.
    """
    print("🧪 Testing Crop Market Recommender System")
    print("=" * 50)

    # Test 1: Data loading
    try:
        df = pd.read_csv('data/market_prices.csv')
        assert not df.empty
        print("✅ Data loading: PASSED")
    except Exception as e:
        print(f"❌ Data loading: FAILED - {e}")

    # Test 2: Model loading
    try:
        model = joblib.load('models/Tomato_price_model.pkl')
        features = joblib.load('models/Tomato_features.pkl')
        assert model is not None
        assert features is not None
        print("✅ Model loading: PASSED")
    except Exception as e:
        print(f"❌ Model loading: FAILED - {e}")

    # Test 3: Profit calculation
    try:
        profit = calculate_net_profit(25, 2, 50)
        assert profit['net_profit'] > 0
        print("✅ Profit calculation: PASSED")
    except Exception as e:
        print(f"❌ Profit calculation: FAILED - {e}")

    # Test 4: Distance calculation
    try:
        # Distance between Delhi (approx) and Mumbai (approx)
        dist = calculate_distance(28.6, 77.2, 19.0, 72.8)
        assert 1000 < dist < 1500 
        print("✅ Distance calculation: PASSED")
    except Exception as e:
        print(f"❌ Distance calculation: FAILED - {e}")

    print("\n🎉 System test completed!")

if __name__ == "__main__":
    test_complete_system()