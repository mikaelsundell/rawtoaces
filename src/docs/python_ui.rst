..
  Copyright Contributors to the rawtoaces Project.
  SPDX-License-Identifier: CC-BY-4.0

Python desktop application
==========================

The optional PySide6 application converts a queue of RAW images through the
Python bindings and provides an OpenGL view of converted images.

Build and run
-------------

Enable ``RTA_BUILD_PYTHON_UI`` alongside ``RTA_BUILD_PYTHON_BINDINGS``. The UI is
disabled by default. It requires PySide6 with QtOpenGLWidgets and QtUiTools,
NumPy, OpenColorIO 2.4+, and the OpenImageIO Python module in the interpreter
selected for the bindings. CMake
checks those imports when the UI is enabled; it does not install packages.

.. code-block:: bash

   cmake -S . -B build -DRTA_BUILD_PYTHON_UI=ON \
     -DPython_EXECUTABLE=/path/to/python3
   cmake --build build --target rawtoaces_python_ui --config Release
   cmake --build build --target run_python_ui --config Release

The existing ``RTA_PYTHON_VERSION`` override can select Python 3.9 explicitly:
add ``-DRTA_PYTHON_VERSION=3.9`` and select that interpreter with
``Python_EXECUTABLE``. The application's Python code supports 3.9; the default
binding discovery still requests 3.10 or newer. Install versions of PySide6,
OpenImageIO, and NumPy that support the selected interpreter and platform.

``cmake --install build --config Release`` installs a ``rawtoaces-ui`` launcher
under the configured ``INSTALL_BIN_DIR``. On Windows, use
``rawtoaces-ui.cmd``. The Python application installs next to the extension in
``INSTALL_LIB_DIR``. The launcher uses the configured Python interpreter.

For an existing Python installation where the compiled ``rawtoaces`` extension
is already importable, ``src/python/pyproject.toml`` also packages the pure
Python UI separately. Its GUI entry point is ``rawtoaces-ui``; it does not
build or bundle the C++ extension.

Conversion workflow
-------------------

1. In **Database & diagnostics**, explicitly select the ``data`` directory
   inside your ``rawtoaces-data`` checkout, containing ``camera``,
   ``illuminant``, ``cmf``, and ``training``. An explicitly supplied
   ``RAWTOACES_DATA_PATH`` can prefill the field. The application does not
   search sibling checkouts or guess this location. The chosen path is saved.
2. Drag RAW files or folders onto the queue, or use **Add files** and
   **Add folder**. Duplicate inputs are ignored. An EXR dropped onto the
   application opens in the image view.
3. Review the properties. **Metadata** white balance and **Auto** matrix
   selection use each file's metadata and the available spectral data.
   Camera and lens override fields are empty initially, so a mixed-camera
   batch retains its per-file metadata.
4. Choose an output directory or leave it empty to write beside each input.
   Select an installed OpenImageIO writer and pixel type in **Output**.
   OpenEXR is the default; outputs use ``<source-stem>_aces.<extension>``.
   Choose **Scene-linear ACES** to retain scene values where the format and
   pixel type support them, or **Display-adjusted** to apply the current
   viewer controls. Integer formats quantise and clip values.
   Enable **Create output folders**
   when needed. Overwriting is disabled initially. The application checks for
   existing outputs and filename collisions before starting the batch.
5. Select **Convert to ACES**. The queue reports completion per file and shows
   the conversion log. A successful output opens automatically in the viewer;
   selecting an already converted queue item reopens that output.

Conversion runs in a child Python process using the same interpreter and
bindings. **Stop after current image** finishes the active file and leaves the
rest unprocessed. Closing during conversion follows the same behaviour.

Property categories
-------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Category
     - Parameters
   * - Colour & white balance
     - White-balance method, illuminant, WB region and multipliers, matrix
       method and custom matrix, headroom, scale, camera overrides.
   * - RAW decoding
     - Demosaicing, half-size decoding, brightness, thresholds, black and
       saturation overrides, highlight recovery, denoising, aberration scales,
       bad-pixel file.
   * - Crop & orientation
     - Crop mode and box, orientation override.
   * - Lens correction
     - Distortion, chromatic aberration, vignetting, mandatory correction,
       lens identity, aperture, focal length, and focus-distance overrides.
   * - Output
     - Destination, file format, pixel type, scene-linear or display-adjusted
       pixels, compression, directory creation, and overwrite policy.
   * - Database & diagnostics
     - Explicit spectral-data directory, ExifTool, cache, timing, diagnostic
       attributes, and verbosity.

Defaults come from ``ImageConverter.Settings``. Method-specific editors are
enabled when their white-balance or matrix method is selected. A custom
matrix must describe the complete camera RGB to ACES AP0 transform.

Image inspection
----------------

The image view uses ``QOpenGLWidget``, GLSL 3.30 core shaders, a floating-point
texture, and vertex-buffer drawing. OpenColorIO generates the GPU shader from
the built-in ``studio-config-v2.2.0_aces-v1.3_ocio-v2.4`` configuration. Input
is fixed to ``ACES2065-1`` and the display to ``sRGB - Display``. Only **View**
is selectable, defaulting to **Un-tone-mapped (sRGB)**. The other ACES views and
``Raw`` come from the same configuration.

The application requests an sRGB default surface format before creating its
windows and OpenGL contexts. OCIO produces the sRGB display-encoded pixels;
the surface colour-space tag describes those pixels to the window system.

Exposure in stops, RGB or individual channels, and luminance are inspection
controls. OCIO handles display encoding; there is no separate gamma or manual
tone mapper. Viewing adjustments leave the normal scene-linear ACES output
unchanged. Display-adjusted exports use the matching OCIO CPU processor.

Drag inside the image to pan, scroll to zoom, double-click to fit, or use
**Fit** and **1:1**. Images larger than 2048 pixels on the longest side are
downsampled for this first viewer; the label reports both the original and
preview dimensions. Preview loading runs outside the UI thread.

**Save as** exports the currently displayed file at its full source resolution
through OpenImageIO, even when the interactive preview is downsampled. Choose
**Source pixels** or **Display-adjusted**, a pixel type, and an optional
writer-specific compression name. The file picker lists the installed output
writers. The checkerboard is not baked into the export. Half/float EXR and
float TIFF can retain HDR values; PNG and JPEG use bounded integer samples.
Other queue formats are written from the library's ACES conversion result.

Interface resources
-------------------

``src/python/rawtoaces_ui/resources/main_window.ui`` defines the viewer,
queue, log, properties, and action blocks. Python inserts the functional
panels into those named containers at runtime through QtUiTools. A plain
``application.qss`` provides the gray palette while retaining the native Qt
style. Both resources are staged, packaged, and installed with the application.

Saved sessions
--------------

The application uses per-user Qt settings to save conversion parameters,
the explicit data directory, viewer controls, window layout, category states,
the queue, and output associations. Existing files are restored on startup;
conversion starts only when requested. Changes are saved while using the
application and again on exit.
