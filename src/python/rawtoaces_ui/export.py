# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""Full-resolution exports through the installed OpenImageIO writers."""

import os
from pathlib import Path
import tempfile

import numpy as np

from .color_management import ColorPipeline


def writable_formats():
    import OpenImageIO as oiio
    formats = []
    for entry in oiio.get_string_attribute("extension_list").split(";"):
        if ":" not in entry:
            continue
        name, extensions = entry.split(":", 1)
        if name in ("null", "term"):
            continue
        writer = oiio.ImageOutput.create(name)
        if writer is not None:
            formats.append((name, extensions.split(",")))
    oiio.geterror()  # Clear discovery errors from input-only formats.
    return sorted(formats, key=lambda item: (item[0] != "openexr", item[0]))


def display_pixels(pixels, state):
    """Match the viewer's image math, keeping alpha instead of its checkerboard."""
    rgb = np.asarray(pixels[..., :3], dtype=np.float32).copy()
    alpha = pixels[..., 3:4] if pixels.shape[-1] > 3 else np.ones((*rgb.shape[:2], 1), np.float32)
    channel = state.get("channel", 0)
    if 1 <= channel <= 3:
        rgb[:] = rgb[..., channel - 1:channel]
    elif channel == 4:
        rgb[:] = alpha
    elif channel == 5:
        rgb[:] = np.sum(rgb * [0.34396645, 0.72816610, -0.07213255], axis=-1, keepdims=True)
    if channel:
        alpha = np.ones_like(alpha)
    result = np.ascontiguousarray(np.concatenate([rgb, alpha], axis=-1), dtype=np.float32)
    if channel != 4:
        ColorPipeline(state.get("view")).apply(result, state.get("exposure", 0.0))
    return result


def export_image(source, destination, pixel_type="auto", display=None,
                 compression="", overwrite=False):
    import OpenImageIO as oiio
    destination = Path(destination).expanduser().resolve()
    if destination.exists() and not overwrite:
        raise FileExistsError("Output already exists: " + str(destination))
    image = oiio.ImageBuf(str(source))
    if not image.read(0, 0, True, oiio.FLOAT):
        raise RuntimeError(image.geterror())
    if display is not None:
        from .preview import read_preview
        # maximum disables downsampling: exports always use source resolution.
        rgba = read_preview(source, maximum=max(image.spec().width, image.spec().height)).pixels
        values = display_pixels(rgba, display)
        converted = oiio.ImageBuf(oiio.ImageSpec(values.shape[1], values.shape[0], 4, oiio.FLOAT))
        if not converted.set_pixels(converted.roi, values):
            raise RuntimeError(converted.geterror())
        image = converted
        image.specmod().attribute("ImageDescription", "rawtoaces UI display-adjusted export")
        if display.get("view") != "Raw":
            image.specmod().attribute("oiio:ColorSpace", "sRGB")
    # RGB-only writers such as JPEG cannot store the viewer's alpha channel.
    if destination.suffix.lower() in (".jpg", ".jpeg", ".jpe", ".bmp", ".ppm", ".hdr", ".rgbe"):
        image = oiio.ImageBufAlgo.channels(image, (0, 1, 2))
    if compression:
        image.specmod().attribute("compression", compression)
    types = {"auto": oiio.UNKNOWN, "uint8": oiio.UINT8, "uint16": oiio.UINT16,
             "half": oiio.HALF, "float": oiio.FLOAT}
    if pixel_type == "auto":
        suffix = destination.suffix.lower()
        if suffix in (".exr", ".sxr", ".mxr"):
            pixel_type = "half"
        elif suffix in (".png", ".jp2", ".j2k", ".dpx"):
            pixel_type = "uint16"
        elif suffix in (".jpg", ".jpeg", ".jpe", ".bmp", ".webp", ".gif", ".tga"):
            pixel_type = "uint8"
    spec = image.specmod()
    if destination.suffix.lower() in (".exr", ".sxr", ".mxr"):
        is_aces = spec.get_string_attribute("oiio:ColorSpace") in ("lin_ap0_scene", "ACES2065-1", "ACES")
        uncompressed = spec.get_string_attribute("compression", "none") in ("", "none")
        spec.attribute("acesImageContainerFlag", int(is_aces and pixel_type == "half" and uncompressed))
    else:
        spec.erase_attribute("acesImageContainerFlag")
    fd, temporary = tempfile.mkstemp(prefix=".rawtoaces-", suffix=destination.suffix,
                                     dir=str(destination.parent))
    os.close(fd)
    try:
        if not image.write(temporary, types[pixel_type]):
            raise RuntimeError(image.geterror() or oiio.geterror())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return destination
