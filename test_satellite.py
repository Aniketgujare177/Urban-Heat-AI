
from pystac_client import Client
import planetary_computer
from datetime import datetime, timedelta, timezone

# College Road, Nashik
LATITUDE = 20.0059
LONGITUDE = 73.7621

# Search area: approximately 500 metres around the location
bbox = [
    LONGITUDE - 0.005,
    LATITUDE - 0.005,
    LONGITUDE + 0.005,
    LATITUDE + 0.005
]

print("Connecting to Microsoft Planetary Computer...")

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=90)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime=f"{start_date.date()}/{end_date.date()}",
    query={"eo:cloud_cover": {"lt": 20}},
    max_items=20
)

items = list(search.items())

print(f"\nSatellite images found: {len(items)}")

if not items:
    print("No suitable images found. Try a wider date range.")
else:
    items.sort(
        key=lambda item: item.properties.get("eo:cloud_cover", 100)
    )

    for item in items[:5]:
        cloud = item.properties.get("eo:cloud_cover", "Unknown")

        print("\nImage ID:", item.id)
        print("Date:", item.datetime)
        print("Cloud cover:", cloud, "%")
        print("Red band available:", "B04" in item.assets)
        print("NIR band available:", "B08" in item.assets)

    # Sign the best image's asset URLs
    best_image = planetary_computer.sign_inplace(items[0])

    print("\nBest image selected:", best_image.id)
    print("Satellite connection successful!")
