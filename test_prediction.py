
from app.services.prediction_service import predict_heat_risk

result = predict_heat_risk(
    temperature=40,
    humidity=60,
    vegetation=15,
    wind_speed=5,
    built_up_density=85
)

print("\nURBAN HEAT AI PREDICTION")
print("------------------------")
print("Risk:", result["risk"])
print("Confidence:", result["confidence"], "%")
print("Probabilities:", result["probabilities"])
print("Model:", result["model_type"])
print("Data:", result["data_type"])
