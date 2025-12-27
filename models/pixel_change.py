import numpy as np

def pixel_difference(
    before_img: np.ndarray,
    after_img: np.ndarray,
    threshold: float = 8.0
):
    """
    Pixel-level change detection using absolute difference.

    INPUT:
        before_img, after_img : np.ndarray
            Expected shape -> (H, W)
            Expected dtype -> uint8 (0–255)

    OUTPUT:
        dict with:
            change_mask   : (H, W) uint8 (0 or 1)
            change_map    : (H, W) uint8 (0–255)
            change_ratio  : float (0–1)
            confidence    : float (0–1)
            pixel_count   : int  (ABSOLUTE ground-truth pixel count)
    """

    if before_img.shape != after_img.shape:
        raise ValueError("Before and after images must have identical shape")

    if before_img.ndim != 2 or after_img.ndim != 2:
        raise ValueError("Pixel change expects single-channel grayscale images")

    # Force float for math safety
    before = before_img.astype(np.float32)
    after = after_img.astype(np.float32)

    # Absolute difference
    diff = np.abs(after - before)

    # Normalize difference map 
    max_val = diff.max()
    if max_val > 0:
        change_map = (diff / max_val * 255).astype(np.uint8)
    else:
        change_map = np.zeros_like(diff, dtype=np.uint8)

    # Binary change mask
    change_mask = (diff >= threshold).astype(np.uint8)
  
    # Change statistics
    total_pixels = change_mask.size
    pixel_count = int(np.count_nonzero(change_mask))

    change_ratio = pixel_count / total_pixels if total_pixels > 0 else 0.0
    confidence = min(1.0, change_ratio * 5.0) #confidence level

    return {
        "change_mask": change_mask,    
        "change_map": change_map,       
        "change_ratio": float(change_ratio),
        "confidence": float(confidence),
        "pixel_count": pixel_count      
    }
