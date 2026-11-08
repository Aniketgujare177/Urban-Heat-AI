
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import planetary_computer

from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds, calculate_default_transform, reproject
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from pystac_client import Client
from datetime import datetime, timedelta, timezone

LATITUDE = 20.0059
LONGITUDE = 73.7621

bbox = [
    LONGITUDE - 0.005,
    LATITUDE - 0.005,
    LONGITUDE + 0.005,
    LATITUDE + 0.005
]

print("Connecting to satellite data...")

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

end = datetime.now(timezone.utc)
start = end - timedelta(days=90)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime=f"{start.date()}/{end.date()}",
    query={"eo:cloud_cover": {"lt": 20}},
    max_items=20
)

items = list(search.items())

if not items:
    raise RuntimeError("No satellite images found.")

items.sort(
    key=lambda item: item.properties.get("eo:cloud_cover", 100)
)

item = planetary_computer.sign_inplace(items[0])

print("Selected:", item.id)


def get_window(src):
    bounds = transform_bounds("EPSG:4326", src.crs, *bbox)
    window = from_bounds(*bounds, transform=src.transform)
    return window.round_offsets().round_lengths().intersection(
        Window(0, 0, src.width, src.height)
    )


with rasterio.open(item.assets["B04"].href) as src:
    window = get_window(src)
    red = src.read(1, window=window).astype("float32")
    transform = src.window_transform(window)
    crs = src.crs

with rasterio.open(item.assets["B08"].href) as src:
    nir = src.read(1, window=window).astype("float32")

with rasterio.open(item.assets["SCL"].href) as src:
    with WarpedVRT(
        src,
        crs=crs,
        transform=transform,
        width=red.shape[1],
        height=red.shape[0],
        resampling=Resampling.nearest
    ) as vrt:
        scl = vrt.read(1)

denominator = nir + red

ndvi = np.full(red.shape, np.nan, dtype="float32")

valid = (
    (denominator != 0) &
    (red > 0) &
    (nir > 0) &
    np.isfinite(denominator) &
    np.isin(scl, [4, 5, 7])
)

ndvi[valid] = (
    (nir[valid] - red[valid]) / denominator[valid]
)

vegetation = np.sum(valid & (ndvi > 0.3))
total = np.sum(valid)

if total == 0:
    raise RuntimeError("No valid pixels available.")

percentage = vegetation / total * 100

# Save NDVI GeoTIFF
profile = {
    "driver": "GTiff",
    "height": ndvi.shape[0],
    "width": ndvi.shape[1],
    "count": 1,
    "dtype": "float32",
    "crs": crs,
    "transform": transform,
    "nodata": -9999
}

with rasterio.open(
    "college_road_ndvi.tif",
    "w",
    **profile
) as dst:
    dst.write(
        np.where(np.isfinite(ndvi), ndvi, -9999),
        1
    )

# Create visualization
plt.figure(figsize=(10, 8))

plt.imshow(
    np.ma.masked_invalid(ndvi),
    cmap="RdYlGn",
    vmin=-1,
    vmax=1
)

plt.colorbar(label="NDVI")
plt.title("College Road, Nashik - Vegetation Map")
plt.axis("off")

plt.figtext(
    0.5, 0.02,
    f"Estimated vegetation coverage: {percentage:.2f}% | "
    f"Satellite date: {item.datetime.date()}",
    ha="center"
)

plt.savefig(
    "college_road_ndvi.png",
    dpi=200,
    bbox_inches="tight"
)

plt.show()

print("\nNDVI visualization saved!")
print("Vegetation coverage:", round(float(percentage), 2), "%")
print("Files: college_road_ndvi.png and college_road_ndvi.tif")
