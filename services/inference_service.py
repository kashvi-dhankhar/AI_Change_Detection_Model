import os
import numpy as np
import cv2

from models.pixel_change import pixel_difference
from models.geojson_writer import write_change_geojson

def run_pixel_change_inference(
    before_img: np.ndarray,
    after_img: np.ndarray,
    reference_tif: str,
    output_dir: str,
    threshold: float = 25.0,
    export_geojson: bool = True
):
    """
    Runs pixel-level change detection inference and saves outputs.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Pixel Change Detection
    result = pixel_difference(
        before_img=before_img,
        after_img=after_img,
        threshold=threshold
    )

    change_mask = result["change_mask"]
    change_map = result["change_map"]
    change_ratio = result["change_ratio"]
    pixel_count = result["pixel_count"]  

    mask_path = os.path.join(output_dir, "change_mask.png")
    diff_path = os.path.join(output_dir, "change_map.png")

    cv2.imwrite(mask_path, (change_mask * 255).astype(np.uint8))
    cv2.imwrite(diff_path, change_map)

    # GeoJSON Export
    geojson_path = None
    if export_geojson:
        geojson_path = os.path.join(output_dir, "change_polygons.geojson")
        write_change_geojson(
            change_mask=change_mask,
            reference_tif=reference_tif,
            output_geojson=geojson_path
        )

    # Final summary
    return {
        "pixel_count": pixel_count,       
        "change_ratio": change_ratio,
        "mask_path": mask_path,
        "diff_path": diff_path,
        "geojson_path": geojson_path
    }
