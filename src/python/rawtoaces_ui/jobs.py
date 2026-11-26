# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""Conversion requests shared by the UI and the isolated binding worker."""

from dataclasses import dataclass, field
from pathlib import Path
import tempfile
from typing import List


@dataclass(frozen=True)
class ConversionOptions:
    parameters: dict = field(default_factory=dict)

    @property
    def output_dir(self):
        return self.parameters.get("output_dir", "")

    @property
    def overwrite(self):
        return self.parameters.get("overwrite", False)

    @property
    def output_format(self):
        return self.parameters.get("output_format", "exr")

    def to_dict(self):
        return dict(self.parameters)


def output_path(filename: str, output_dir: str, output_format: str = "exr") -> Path:
    source = Path(filename).resolve()
    directory = Path(output_dir).expanduser().resolve() if output_dir else source.parent
    return directory / (source.stem + "_aces." + output_format)


def validate_queue(filenames: List[str], options: ConversionOptions):
    if not filenames:
        raise ValueError("Add at least one RAW image to the queue.")
    if options.output_dir:
        directory = Path(options.output_dir).expanduser()
        if directory.exists() and not directory.is_dir():
            raise ValueError("The output destination must be a directory.")
    destinations = set()
    for filename in filenames:
        if not Path(filename).is_file():
            raise ValueError("Input file not found: " + filename)
        destination = output_path(filename, options.output_dir, options.output_format)
        key = str(destination).casefold()
        if key in destinations:
            raise ValueError("Multiple inputs would write the same output: " + str(destination))
        destinations.add(key)
        if destination.exists() and not options.overwrite:
            raise ValueError("Output already exists: " + str(destination))


def convert(filename: str, options: ConversionOptions):
    import rawtoaces

    destination = output_path(filename, options.output_dir, options.output_format)
    converter = rawtoaces.ImageConverter()
    settings = converter.settings
    enums = {"WB_method": settings.WBMethod, "matrix_method": settings.MatrixMethod,
             "crop_mode": settings.CropMode}
    for name, value in options.parameters.items():
        if name in ("output_format", "output_type", "output_pixels", "display_settings"):
            continue
        if name == "lens_correction_types":
            for correction in value:
                settings.lens_correction_types |= getattr(settings.LensCorrectionType, correction)
        else:
            setattr(settings, name, getattr(enums[name], value) if name in enums else value)
    settings.output_dir = str(destination.parent)
    if settings.create_dirs:
        destination.parent.mkdir(parents=True, exist_ok=True)
    source = str(Path(filename).resolve())
    native = (options.output_format == "exr" and options.parameters.get("output_type", "auto") == "auto"
              and options.parameters.get("output_pixels", "scene-linear") == "scene-linear")
    if native:
        if not converter.process_image(source):
            raise RuntimeError(converter.last_error_message or str(converter.status))
    else:
        from .export import export_image
        # The temporary ACES EXR uses its own lossless/default storage. A
        # writer-specific export compression (e.g. TIFF LZW) is applied later.
        settings.compression = ""
        if not destination.parent.is_dir():
            raise FileNotFoundError("Output directory does not exist: " + str(destination.parent))
        with tempfile.TemporaryDirectory(prefix="rawtoaces-export-") as temporary:
            settings.output_dir = temporary
            if not converter.process_image(source):
                raise RuntimeError(converter.last_error_message or str(converter.status))
            converted = output_path(source, temporary)
            display = (options.parameters.get("display_settings", {})
                       if options.parameters.get("output_pixels") == "display" else None)
            export_image(converted, destination, options.parameters.get("output_type", "auto"),
                         display, options.parameters.get("compression", ""), options.overwrite)
    return destination
