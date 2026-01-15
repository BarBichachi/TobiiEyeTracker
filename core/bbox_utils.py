# bbox_utils.py
# Bounding-box helpers used by the tracking pipeline.
# Provides center/offset computations for (x, y, w, h) boxes relative to the image center.

import torch
import numpy as np


# Converts (x, y, w, h) box to (dx, dy, w, h) relative to image center (right=+, up=+)
def bbox_to_center_offset(bbox, img_width, img_height):
    x, y, w, h = _as_single_box_xywh(bbox)

    x_center = x + w / 2.0
    y_center = y + h / 2.0

    dx, dy = center_offset(x_center, y_center, img_width, img_height)
    return dx, dy, w, h


# Calculates the offset of a point from the image center (right=+, up=+)
def center_offset(x_center, y_center, img_width, img_height):
    x_origin = img_width / 2.0
    y_origin = img_height / 2.0
    return float(x_center - x_origin), float(y_origin - y_center)


# Normalizes bbox input to a single (x, y, w, h) float tuple
def _as_single_box_xywh(bbox):
    if torch is not None and isinstance(bbox, torch.Tensor):
        arr = bbox.detach().cpu().numpy()
    else:
        arr = np.asarray(bbox)

    arr = np.squeeze(arr)
    if arr.shape != (4,):
        raise ValueError(f"Expected bbox shape (4,) or (1,4), got {arr.shape}")

    x, y, w, h = arr.tolist()
    return float(x), float(y), float(w), float(h)
