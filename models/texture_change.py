import numpy as np
import rasterio
from skimage.feature import graycomatrix, graycoprops
from skimage.morphology import remove_small_objects, opening
from scipy.ndimage import label


def compute_glcm_window(window):
    glcm = graycomatrix(
        window,
        distances=[1],
        angles=[0],
        levels=256,
        symmetric=True,
        normed=True
    )
    return graycoprops(glcm, 'contrast')[0, 0]

def texture_change(
    tiff1_path,
    tiff2_path,
    pixel_change_mask,
    window_size=7,
    min_area=30
):
  
    # Read GeoTIFF
    with rasterio.open(tiff1_path) as src1:
        img1 = src1.read(1)

    with rasterio.open(tiff2_path) as src2:
        img2 = src2.read(1)

    # Normalize to 8-bit
    img1 = ((img1 - img1.min()) / (img1.max() - img1.min()) * 255).astype(np.uint8)
    img2 = ((img2 - img2.min()) / (img2.max() - img2.min()) * 255).astype(np.uint8)

    pad = window_size // 2
    texture_mask = np.zeros(pixel_change_mask.shape, dtype=bool)

    labeled_mask, num = label(pixel_change_mask.astype(bool))

    for lbl in range(1, num + 1):
        component = (labeled_mask == lbl)

        if np.count_nonzero(component) < min_area:
            continue

        rows, cols = np.where(component)
        rmin, rmax = rows.min(), rows.max()
        cmin, cmax = cols.min(), cols.max()

        for i in range(max(rmin, pad), min(rmax, img1.shape[0] - pad)):
            for j in range(max(cmin, pad), min(cmax, img1.shape[1] - pad)):
                if not component[i, j]:
                    continue

                w1 = img1[i-pad:i+pad+1, j-pad:j+pad+1]
                w2 = img2[i-pad:i+pad+1, j-pad:j+pad+1]

                t1 = compute_glcm_window(w1)
                t2 = compute_glcm_window(w2)

                if abs(t2 - t1) > 0.5:
                    texture_mask[i, j] = True

    texture_mask = opening(texture_mask)
    texture_mask = remove_small_objects(texture_mask, min_size=min_area)

    return texture_mask.astype(np.uint8)
