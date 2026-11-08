
import os
import pickle
import numpy as np


# Locate the trained model
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "heat_risk_model.pkl"
)


def load_model():

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "Heat risk model not found. Train the model first."
        )

    with open(MODEL_PATH, "rb") as file:
        model_information = pickle.load(file)

    return model_information["model"]


def predict_heat_risk(
    temperature,
    humidity,
    vegetation,
    wind_speed,
    built_up_density
):

    model = load_model()

    input_data = np.array([[
        temperature,
        humidity,
        vegetation,
        wind_speed,
        built_up_density
    ]])

    prediction = model.predict(input_data)[0]

    probabilities = model.predict_proba(input_data)[0]

    confidence = float(max(probabilities) * 100)

    class_probabilities = {
        risk: round(float(probability) * 100, 2)
        for risk, probability in zip(
            model.classes_,
            probabilities
        )
    }

    return {
        "risk": prediction,
        "confidence": round(confidence, 2),
        "probabilities": class_probabilities,
        "model_type": "Random Forest",
        "data_type": "Synthetic training data"
    }
