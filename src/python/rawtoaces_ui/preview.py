# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""Floating-point image loading for the scene-linear image view."""

from dataclasses import dataclass

import numpy as np


@dataclass
class PreviewImage:
    pixels: np.ndarray
    width: int
    height: int
    pixel_aspect: float = 1.0
    display_encoded: bool = False


def read_preview(filename, maximum=2048):
    import OpenImageIO as oiio

    image = oiio.ImageBuf(str(filename))
    if not image.init_spec(str(filename), 0, 0):
        raise RuntimeError(image.geterror())
    spec = image.spec()
    width, height = spec.width, spec.height
    names = list(spec.channelnames)
    alpha = spec.alpha_channel
    aspect = spec.get_float_attribute("PixelAspectRatio", 1.0)
    display_encoded = "rawtoaces UI display-adjusted export" in spec.get_string_attribute("ImageDescription", "")
    if width < 1 or height < 1 or spec.deep:
        raise ValueError("The viewer requires a non-deep, two-dimensional image.")
    ratio = min(1.0, maximum / max(width, height))
    if ratio < 1.0:
        roi = oiio.ROI(0, max(1, round(width * ratio)), 0, max(1, round(height * ratio)),
                       0, 1, 0, spec.nchannels)
        image = oiio.ImageBufAlgo.resize(image, roi=roi)
    pixels = image.get_pixels(oiio.FLOAT)
    if pixels is None or image.has_error:
        raise RuntimeError(image.geterror() or "Cannot read image pixels.")
    rgba = np.ones((*pixels.shape[:2], 4), dtype=np.float32)
    for channel, name in enumerate(("R", "G", "B")):
        source = names.index(name) if name in names else min(channel, pixels.shape[-1] - 1)
        rgba[..., channel] = pixels[..., source]
    if 0 <= alpha < pixels.shape[-1]:
        rgba[..., 3] = pixels[..., alpha]
    np.nan_to_num(rgba, copy=False, nan=0.0, posinf=65504.0, neginf=-65504.0)
    return PreviewImage(np.ascontiguousarray(rgba), width, height, aspect, display_encoded)
