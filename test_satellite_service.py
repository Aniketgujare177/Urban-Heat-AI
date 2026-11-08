
from app.services.satellite_service import analyze_vegetation

result = analyze_vegetation(
    area_name="Gangapur Road",
    latitude=20.0067,
    longitude=73.7498
)

print("\n--- SATELLITE ANALYSIS ---")

for key, value in result.items():
    print(f"{key}: {value}")
