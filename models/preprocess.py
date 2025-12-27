import os
import numpy as np
import rasterio
import cv2
import base64

# Convert raster to PNG
def raster_to_png_base64(raster):
    """
    Safe preview generator for satellite rasters or images
    """

    # GeoTIFF: (bands, H, W)
    if raster.ndim == 3:
        bands, h, w = raster.shape

        if bands >= 3:
            img = raster[:3].transpose(1, 2, 0)
        else:
            img = raster[0]

    elif raster.ndim == 2:
        img = raster
    elif raster.ndim == 3 and raster.shape[2] in [3, 4]:
        img = raster[:, :, :3]
    else:
        raise ValueError("Unsupported raster format for preview")

    img = img.astype(np.float32)
    img -= img.min()
    if img.max() > 0:
        img /= img.max()

    img = (img * 255).astype(np.uint8)

    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    _, buffer = cv2.imencode(".png", img)
    return base64.b64encode(buffer).decode("utf-8")

def load_standard_image(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    return img

# Main Preprocess function

def preprocess_images(before_path, after_path):
    """
    Universal preprocessing entrypoint

    Returns:
        before_img (np.ndarray)  -> (H, W)
        after_img  (np.ndarray)  -> (H, W)
        meta (dict)
    """

    ext1 = os.path.splitext(before_path)[1].lower()
    ext2 = os.path.splitext(after_path)[1].lower()

    is_geotiff = ext1 in [".tif", ".tiff"] and ext2 in [".tif", ".tiff"]

    meta = {
        "is_geotiff": is_geotiff,
        "transform": None,
        "crs": None,
        "before_preview": None,
        "after_preview": None,
    }

    # CASE 1: GeoTIFF Image
    if is_geotiff:
        with rasterio.open(before_path) as src1, rasterio.open(after_path) as src2:
            before_raw = src1.read()
            after_raw = src2.read()

            meta["transform"] = src1.transform
            meta["crs"] = src1.crs

            # PREVIEWS (RGB)
            meta["before_preview"] = raster_to_png_base64(before_raw)
            meta["after_preview"] = raster_to_png_base64(after_raw)

            # ANALYSIS (grayscale)
            before_img = before_raw[0].astype(np.float32)
            after_img = after_raw[0].astype(np.float32)

    # CASE 2: Normal Image
    else:
        before_img = load_standard_image(before_path).astype(np.float32)
        after_img = load_standard_image(after_path).astype(np.float32)

        meta["before_preview"] = raster_to_png_base64(before_img)
        meta["after_preview"] = raster_to_png_base64(after_img)

    # Alignment + Normalization
    h = min(before_img.shape[0], after_img.shape[0])
    w = min(before_img.shape[1], after_img.shape[1])

    before_img = cv2.resize(before_img, (w, h))
    after_img = cv2.resize(after_img, (w, h))

    before_img = cv2.normalize(before_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    after_img = cv2.normalize(after_img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    return before_img, after_img, meta
