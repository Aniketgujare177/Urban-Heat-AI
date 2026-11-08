
import numpy as np
import rasterio
import planetary_computer

from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling
from pystac_client import Client
from datetime import datetime, timedelta, timezone

LATITUDE = 20.0059
LONGITUDE = 73.7621

# Approximately 500 metres around College Road
bbox = [
    LONGITUDE - 0.005,
    LATITUDE - 0.005,
    LONGITUDE + 0.005,
    LATITUDE + 0.005
]

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

print("Selected image:", item.id)


# Read local B04 red band
with rasterio.open(item.assets["B04"].href) as src:
    local_bounds = transform_bounds(
        "EPSG:4326", src.crs, *bbox
    )

    window = from_bounds(
        *local_bounds, transform=src.transform
    ).round_offsets().round_lengths()

    window = window.intersection(
        Window(0, 0, src.width, src.height)
    )

    red = src.read(1, window=window).astype("float32")
    local_transform = src.window_transform(window)
    local_crs = src.crs

# Read local B08 NIR band
with rasterio.open(item.assets["B08"].href) as src:
    nir = src.read(1, window=window).astype("float32")

if red.shape != nir.shape:
    raise RuntimeError("B04 and B08 dimensions do not match.")

# SCL is usually 20m resolution.
# Align it to the 10m red/NIR grid using nearest-neighbour resampling.
with rasterio.open(item.assets["SCL"].href) as scl_src:
    with WarpedVRT(
        scl_src,
        crs=local_crs,
        transform=local_transform,
        width=red.shape[1],
        height=red.shape[0],
        resampling=Resampling.nearest
    ) as scl_vrt:
        scl = scl_vrt.read(1)

# NDVI calculation
denominator = nir + red

ndvi = np.full(red.shape, np.nan, dtype="float32")

valid_reflectance = (
    (denominator != 0) &
    (red > 0) &
    (nir > 0) &
    np.isfinite(denominator)
)

ndvi[valid_reflectance] = (
    (nir[valid_reflectance] - red[valid_reflectance]) /
    denominator[valid_reflectance]
)

# SCL classes:
# 4 = Vegetation
# 5 = Not vegetated
# 6 = Water
# 7 = Unclassified
# Exclude water and all cloud/shadow/snow/invalid classes.
clear_land = np.isin(scl, [4, 5, 7])

valid_pixels = (
    valid_reflectance &
    clear_land &
    np.isfinite(ndvi)
)

if not np.any(valid_pixels):
    raise RuntimeError("No valid clear land pixels found.")

vegetation_pixels = np.sum(ndvi[valid_pixels] > 0.3)
total_pixels = np.sum(valid_pixels)

vegetation_percentage = (
    vegetation_pixels / total_pixels
) * 100

cloud_shadow_pixels = np.sum(~clear_land)
total_area_pixels = scl.size

print("\n--- COLLEGE ROAD MASKED NDVI RESULTS ---")
print("Mean NDVI:", round(float(np.nanmean(ndvi[valid_pixels])), 3))
print("Vegetation coverage:", round(float(vegetation_percentage), 2), "%")
print("Valid clear land pixels:", int(total_pixels))
print("Excluded pixels:", int(cloud_shadow_pixels))
print("Total area pixels:", int(total_area_pixels))
print("Satellite date:", item.datetime)
print("Scene cloud cover:", item.properties.get("eo:cloud_cover"))
print("Cloud and shadow masking: Applied")
