
import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


# --------------------------------------------------
# URBAN HEAT AI - RANDOM FOREST PROTOTYPE
# Training data in this version is synthetic.
# It is NOT verified real-world environmental data.
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "heat_risk_model.pkl")

FEATURE_NAMES = [
    "temperature",
    "humidity",
    "vegetation",
    "wind_speed",
    "built_up_density"
]


def generate_training_data(samples=5000):

    np.random.seed(42)

    temperature = np.random.uniform(20, 45, samples)
    humidity = np.random.uniform(20, 100, samples)
    vegetation = np.random.uniform(5, 80, samples)
    wind_speed = np.random.uniform(0, 25, samples)
    built_up_density = np.random.uniform(10, 100, samples)

    # Synthetic demonstration risk score.
    # These weights are illustrative, not scientifically calibrated.

    risk_score = (
        (temperature - 20) * 2.5
        + (humidity - 20) * 0.12
        + (80 - vegetation) * 0.35
        + (25 - wind_speed) * 0.5
        + built_up_density * 0.25
    )

    labels = np.where(
        risk_score >= 115,
        "High",
        np.where(risk_score >= 75, "Medium", "Low")
    )

    X = np.column_stack([
        temperature,
        humidity,
        vegetation,
        wind_speed,
        built_up_density
    ])

    return X, labels


def train_model():

    print("\nUrban Heat AI - Model Training")
    print("--------------------------------")

    X, y = generate_training_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    print("\nTraining completed!")
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples: {len(X_test)}")
    print(f"Test accuracy on synthetic data: {accuracy:.2%}")

    print("\nClassification Report:")
    print(classification_report(y_test, predictions))

    model_information = {
        "model": model,
        "features": FEATURE_NAMES,
        "training_data": "synthetic demonstration data",
        "model_type": "Random Forest Classifier"
    }

    with open(MODEL_PATH, "wb") as file:
        pickle.dump(model_information, file)

    print(f"\nModel saved successfully:")
    print(MODEL_PATH)


if __name__ == "__main__":
    train_model()
