
import re
import numpy as np
import rasterio
import planetary_computer
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
from datetime import datetime, timedelta, timezone

from pystac_client import Client
from rasterio.windows import from_bounds, Window
from rasterio.warp import transform_bounds
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling


CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIR = PROJECT_ROOT / "app" / "static" / "images"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def analyze_vegetation(area_name, latitude, longitude):

    # Approximately 500 metres around the selected location
    bbox = [
        longitude - 0.005,
        latitude - 0.005,
        longitude + 0.005,
        latitude + 0.005
    ]

    catalog = Client.open(CATALOG_URL)

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
        raise RuntimeError(
            f"No suitable satellite image found for {area_name}."
        )

    items.sort(
        key=lambda item: item.properties.get(
            "eo:cloud_cover", 100
        )
    )

    item = planetary_computer.sign_inplace(items[0])

    # Read red band
    with rasterio.open(item.assets["B04"].href) as src:

        bounds = transform_bounds(
            "EPSG:4326",
            src.crs,
            *bbox
        )

        window = from_bounds(
            *bounds,
            transform=src.transform
        ).round_offsets().round_lengths()

        window = window.intersection(
            Window(0, 0, src.width, src.height)
        )

        red = src.read(
            1, window=window
        ).astype("float32")

        local_transform = src.window_transform(window)
        local_crs = src.crs

    # Read near-infrared band
    with rasterio.open(item.assets["B08"].href) as src:
        nir = src.read(
            1, window=window
        ).astype("float32")

    if red.shape != nir.shape:
        raise RuntimeError("Satellite band dimensions do not match.")

    # Align Scene Classification Layer to the red band grid
    with rasterio.open(item.assets["SCL"].href) as src:

        with WarpedVRT(
            src,
            crs=local_crs,
            transform=local_transform,
            width=red.shape[1],
            height=red.shape[0],
            resampling=Resampling.nearest
        ) as vrt:

            scl = vrt.read(1)

    denominator = nir + red

    valid_reflectance = (
        (denominator != 0) &
        (red > 0) &
        (nir > 0) &
        np.isfinite(denominator)
    )

    ndvi = np.full(
        red.shape, np.nan, dtype="float32"
    )

    ndvi[valid_reflectance] = (
        (nir[valid_reflectance] - red[valid_reflectance]) /
        denominator[valid_reflectance]
    )

    # Keep clear land pixels:
    # SCL 4 = Vegetation
    # SCL 5 = Not vegetated
    clear_land = np.isin(scl, [4, 5])

    valid = (
        valid_reflectance &
        clear_land &
        np.isfinite(ndvi)
    )

    if not np.any(valid):
        raise RuntimeError("No valid clear land pixels found.")

    vegetation_pixels = np.sum(
        valid & (ndvi > 0.3)
    )

    total_pixels = np.sum(valid)

    vegetation_percentage = (
        vegetation_pixels / total_pixels
    ) * 100

    mean_ndvi = float(np.mean(ndvi[valid]))

    # Create a safe filename for this neighbourhood
    slug = re.sub(
        r"[^a-z0-9]+",
        "_",
        area_name.lower()
    ).strip("_")

    image_filename = f"ndvi_{slug}.png"
    image_path = IMAGE_DIR / image_filename

    # Generate map image
    fig, ax = plt.subplots(figsize=(9, 7))

    image = ax.imshow(
        np.ma.masked_invalid(ndvi),
        cmap="RdYlGn",
        vmin=-1,
        vmax=1
    )

    fig.colorbar(image, ax=ax, label="NDVI")

    ax.set_title(f"{area_name} - Vegetation Map")
    ax.axis("off")

    fig.savefig(
        image_path,
        dpi=180,
        bbox_inches="tight"
    )

    plt.close(fig)

    return {
        "area_name": area_name,
        "mean_ndvi": round(mean_ndvi, 3),
        "vegetation_percentage": round(
            float(vegetation_percentage), 2
        ),
        "valid_pixels": int(total_pixels),
        "satellite_date": item.datetime.isoformat(),
        "cloud_cover": item.properties.get(
            "eo:cloud_cover"
        ),
        "image": f"images/{image_filename}",
        "source": "Sentinel-2 L2A"
    }
