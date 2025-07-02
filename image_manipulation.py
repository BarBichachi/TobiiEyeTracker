import torch
import numpy as np

# Converts bounding boxes to center format and computes offset from image center
def bbox_to_center_offset(bbox, img_width, img_height):
    """
    Converts a bounding box from top-left format (x1, y1, w, h)
    to center format (cx, cy, w, h),
    and calculates its offset from the image center.

    Args:
        bbox (torch.Tensor | np.ndarray): Shape (1, 4), format [x1, y1, w, h]
        img_width (int): Width of the image
        img_height (int): Height of the image

    Returns:
        dx (float): Horizontal distance from image center (right=+ / left=-)
        dy (float): Vertical distance from image center (up=+ / down=-)
        width (float): Box width
        height (float): Box height
    """
    y = bbox.clone() if isinstance(bbox, torch.Tensor) else np.copy(bbox)
    y[..., 0] = bbox[..., 0] + bbox[..., 2] / 2  # center x
    y[..., 1] = bbox[..., 1] + bbox[..., 3] / 2  # center y

    x_center = y[0][0].item()
    x_origin = img_height / 2
    dx = x_center - x_origin

    y_center = y[0][1].item()
    y_origin = img_width / 2
    dy = y_origin - y_center

    return dx, dy, y[0][2].item(), y[0][3].item()

def center_offset(x_center, y_center, img_width, img_height):
    """
    Calculates the offset of a center point from the image center.

    Args:
        x_center (float): x coordinate of center
        y_center (float): y coordinate of center
        img_width (int): width of the image
        img_height (int): height of the image

    Returns:
        dx, dy (float, float): offset from image center (x: right=+, y: up=+)
    """
    x_origin = img_width / 2
    y_origin = img_height / 2

    return x_center - x_origin, y_origin - y_center