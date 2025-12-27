import numpy as np
import rasterio
from scipy.ndimage import binary_opening, binary_closing, label
import json

def write_change_geojson(
    change_mask: np.ndarray,
    pixel_changed_pixels: int,
    texture_confirmed_pixels: int,
    reference_tif: str | None = None,
    output_geojson: str | None = None,
    transform=None,
    crs=None,
    min_area_pixels: int = 50
):
  
    # Resolve spatial metadata
    if reference_tif is not None:
        with rasterio.open(reference_tif) as src:
            crs = src.crs
    else:
        if crs is None:
            raise ValueError("CRS must be provided")

    # Morphological filtering (only for geometry)
    mask = change_mask.astype(bool)

    if np.count_nonzero(mask) > 0:
        mask = binary_opening(mask, structure=np.ones((3, 3)))
        mask = binary_closing(mask, structure=np.ones((5, 5)))

        labeled, num = label(mask)
        clean_mask = np.zeros_like(mask, dtype=np.uint8)

        for i in range(1, num + 1):
            component = (labeled == i)
            if np.count_nonzero(component) >= min_area_pixels:
                clean_mask[component] = 1
    else:
        clean_mask = mask.astype(np.uint8)

    # Final GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": None,  # geometry optional at this stage
                "properties": {
                    "change_detected": pixel_changed_pixels > 0,
                    "pixel_changed_pixels": pixel_changed_pixels,
                    "texture_confirmed_pixels": texture_confirmed_pixels
                }
            }
        ],
        "crs": {
            "type": "name",
            "properties": {"name": str(crs)}
        }
    }
  
    if output_geojson is not None:
        with open(output_geojson, "w") as f:
            json.dump(geojson, f)

    return geojson
