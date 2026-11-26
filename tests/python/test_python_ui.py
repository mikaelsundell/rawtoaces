# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

"""UI behaviour and real worker/rendering checks; enabled with the UI build."""

import os
from pathlib import Path
import shutil
import time

import numpy as np
import pytest
import rawtoaces
from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QColorSpace, QDragEnterEvent, QDropEvent, QSurfaceFormat
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from rawtoaces_ui.image_view import ImageView, configure_surface_format
from rawtoaces_ui.jobs import ConversionOptions, output_path, validate_queue
from rawtoaces_ui.main_window import MainWindow
from rawtoaces_ui.preview import PreviewImage, read_preview
from rawtoaces_ui.color_management import ColorPipeline, default_view, views
from rawtoaces_ui.settings import SettingsStore, initial_data_directory
from rawtoaces_ui.workers import ConversionQueue
from rawtoaces_ui.export import display_pixels, export_image, writable_formats


@pytest.fixture(scope="session")
def app():
    configure_surface_format()
    return QApplication.instance() or QApplication([])


def wait_until(app, predicate, timeout=30):
    limit = time.monotonic() + timeout
    while not predicate() and time.monotonic() < limit:
        app.processEvents()
        time.sleep(0.01)
    assert predicate(), "Timed out waiting for the asynchronous UI operation"


def test_data_path_is_only_explicit(monkeypatch):
    monkeypatch.delenv("RAWTOACES_DATA_PATH", raising=False)
    assert initial_data_directory() == ""
    monkeypatch.setenv("RAWTOACES_DATA_PATH", "/explicit/rawtoaces-data/data")
    assert initial_data_directory() == "/explicit/rawtoaces-data/data"


def test_default_surface_is_srgb(app):
    assert QSurfaceFormat.defaultFormat().colorSpace() == QColorSpace(QColorSpace.NamedColorSpace.SRgb)


def test_queue_prevents_output_collisions_and_overwrite(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    first.mkdir()
    second.mkdir()
    inputs = [first / "image.dng", second / "image.nef"]
    for path in inputs:
        path.touch()
    options = ConversionOptions({"output_dir": str(tmp_path / "output")})
    with pytest.raises(ValueError, match="same output"):
        validate_queue([str(path) for path in inputs], options)
    destination = output_path(str(inputs[0]), "")
    destination.write_text("existing image")
    with pytest.raises(ValueError, match="already exists"):
        validate_queue([str(inputs[0])], ConversionOptions())
    assert destination.read_text() == "existing image"


def test_drop_adds_files_deduplicates_and_persists_parameters(app, tmp_path, monkeypatch):
    monkeypatch.delenv("RAWTOACES_DATA_PATH", raising=False)
    filename = tmp_path / "sample.dng"
    filename.touch()
    state = tmp_path / "settings.ini"
    window = MainWindow(rawtoaces, state)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(filename))])
    drag = QDragEnterEvent(QPoint(10, 10), Qt.DropAction.CopyAction, mime,
                           Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    window.files.dragEnterEvent(drag)
    assert drag.isAccepted()
    drop = QDropEvent(QPointF(10, 10), Qt.DropAction.CopyAction, mime,
                      Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    window.files.dropEvent(drop)
    window.files.dropEvent(drop)
    assert window.filenames == [str(filename)]
    assert window.properties.options().parameters["database_directories"] == []
    window.properties.fields["headroom"].setValue(4.0)
    window.properties.fields["matrix_method"].setCurrentText("Custom")
    window.properties._setters["custom_matrix"]([[1.1, 0.2, 0.3], [0.1, 1.2, 0.1], [0, 0, 1]])
    window.properties._setters["database_directories"]([str(tmp_path / "chosen-data")])
    window.properties.lens_checks["Distortion"].setChecked(True)
    window.image_panel.exposure.setValue(1.5)
    window.image_panel.view_selector.setCurrentIndex(window.image_panel.view_selector.findData("ACES 1.0 - SDR Video"))
    expected = window.properties.options().to_dict()
    window.close()
    restored = MainWindow(rawtoaces, state)
    assert restored.filenames == [str(filename)]
    assert restored.properties.options().to_dict() == expected
    assert restored.image_panel.exposure.value() == 1.5
    assert restored.image_panel.view_selector.currentData() == "ACES 1.0 - SDR Video"
    assert not restored.queue.busy
    restored.close()


def test_settings_recovers_from_invalid_json(tmp_path):
    store = SettingsStore(tmp_path / "settings.ini")
    store.settings.setValue("session", "{broken json")
    assert store.load() == {}


def test_default_ocio_view_preserves_neutral_white():
    assert default_view() == "Un-tone-mapped"
    assert "ACES 1.0 - SDR Video" in views()
    white = np.ones((1, 1, 4), dtype=np.float32)
    ColorPipeline().apply(white)
    np.testing.assert_allclose(white, 1.0, atol=1e-4)


def test_preview_preserves_hdr_data_and_channel_order(tmp_path):
    import OpenImageIO as oiio
    path = tmp_path / "hdr.exr"
    pixels = np.array([[[4.0, 0.25, -0.5, 0.5], [0.1, 0.2, 0.3, 1.0]]], dtype=np.float32)
    spec = oiio.ImageSpec(2, 1, 4, oiio.FLOAT)
    writer = oiio.ImageOutput.create(str(path))
    assert writer.open(str(path), spec)
    assert writer.write_image(pixels)
    writer.close()
    loaded = read_preview(path)
    np.testing.assert_allclose(loaded.pixels, pixels)
    assert loaded.width == 2 and loaded.height == 1


def test_full_resolution_export_and_display_pixels(tmp_path):
    import OpenImageIO as oiio
    assert any(name == "png" for name, _ in writable_formats())
    source = tmp_path / "source.exr"
    values = np.full((8, 3072, 4), 1.0, np.float32)
    values[..., :3] = [0.25, 0.5, 2.0]
    image = oiio.ImageBuf(oiio.ImageSpec(3072, 8, 4, oiio.FLOAT))
    image.specmod().attribute("oiio:ColorSpace", "lin_ap0_scene")
    image.specmod().attribute("acesImageContainerFlag", 1)
    image.specmod().attribute("compression", "none")
    assert image.set_pixels(image.roi, values)
    assert image.write(str(source), oiio.HALF)
    linear = tmp_path / "linear.tif"
    export_image(source, linear, "float")
    assert read_preview(source, maximum=64).pixels.shape[1] == 64
    np.testing.assert_allclose(read_preview(linear, maximum=4096).pixels, values)
    display = tmp_path / "display.png"
    export_image(source, display, "uint16", {"exposure": 1.0, "view": "Raw"})
    expected = np.clip(values * [2, 2, 2, 1], 0, 1)
    result = read_preview(display, maximum=4096)
    assert (result.width, result.height) == (3072, 8)
    np.testing.assert_allclose(result.pixels, expected, atol=2 / 65535)
    before = display.read_bytes()
    with pytest.raises(FileExistsError):
        export_image(source, display)
    assert display.read_bytes() == before
    float_exr = tmp_path / "float.exr"
    export_image(source, float_exr, "float")
    float_image = oiio.ImageBuf(str(float_exr))
    assert float_image.init_spec(str(float_exr), 0, 0)
    assert float_image.spec().get_int_attribute("acesImageContainerFlag") == 0


def test_queue_can_write_another_format(app, tmp_path):
    source = Path(__file__).resolve().parents[1] / "materials" / "blackmagic_cinema_camera_cinemadng.dng"
    copied = tmp_path / "input.dng"
    shutil.copy2(source, copied)
    queue = ConversionQueue()
    options = ConversionOptions({"output_dir": str(tmp_path), "output_format": "png",
                                 "output_type": "uint16", "output_pixels": "display",
                                 "display_settings": {"view": default_view()},
                                 "WB_method": "Metadata", "matrix_method": "Metadata",
                                 "half_size": True})
    finished, completed, log = [], [], []
    queue.completed.connect(lambda _, success: completed.append(success))
    queue.output.connect(log.append)
    queue.finished.connect(finished.append)
    queue.start([str(copied)], options)
    wait_until(app, lambda: bool(finished), timeout=90)
    assert completed == [True], "".join(log)
    assert output_path(str(copied), str(tmp_path), "png").is_file()
    assert not output_path(str(copied), str(tmp_path)).exists()


def test_worker_converts_with_bindings_and_cancels_between_files(app, tmp_path):
    source = Path(__file__).resolve().parents[1] / "materials" / "blackmagic_cinema_camera_cinemadng.dng"
    copied = tmp_path / "source.dng"
    shutil.copy2(source, copied)
    queue = ConversionQueue()
    options = ConversionOptions({"output_dir": str(tmp_path / "output"), "create_dirs": True,
                                 "WB_method": "Metadata", "matrix_method": "Metadata",
                                 "half_size": True})
    completed, finished, log = [], [], []
    queue.completed.connect(lambda index, success: completed.append((index, success)))
    queue.output.connect(log.append)
    queue.finished.connect(finished.append)
    queue.started.connect(lambda *_: queue.cancel())
    second = tmp_path / "second.dng"
    shutil.copy2(source, second)
    queue.start([str(copied), str(second)], options)
    wait_until(app, lambda: bool(finished), timeout=90)
    assert completed == [(0, True)], "".join(log)
    assert finished == [True]
    assert output_path(str(copied), options.output_dir).is_file()
    assert not output_path(str(second), options.output_dir).exists()


def test_failed_worker_reports_failure_and_finishes(app, tmp_path):
    bad = tmp_path / "broken.dng"
    bad.write_text("not a RAW file")
    queue = ConversionQueue()
    completed, finished, log = [], [], []
    queue.completed.connect(lambda index, success: completed.append(success))
    queue.finished.connect(finished.append)
    queue.output.connect(log.append)
    queue.start([str(bad)], ConversionOptions())
    wait_until(app, lambda: bool(finished))
    assert completed == [False]
    assert "Conversion failed" in "".join(log)


@pytest.mark.skipif(os.environ.get("RTA_TEST_OPENGL") != "1", reason="Requires a native OpenGL window")
def test_glsl_rendering_exposure_channels_views_and_orientation(app):
    view = ImageView()
    view.resize(320, 240)
    pixels = np.empty((8, 8, 4), dtype=np.float32)
    pixels[:] = [0.25, 0.5, 0.75, 1.0]
    view.set_image(PreviewImage(pixels, 8, 8))
    view.color_view = "Raw"
    view.show()
    try:
        assert QTest.qWaitForWindowExposed(view, 10000)
        wait_until(app, lambda: bool(view.gl_error) or (view.isValid() and view._texture is not None))
        assert not view.gl_error
        def center():
            image = view.grabFramebuffer()
            colour = image.pixelColor(image.width() // 2, image.height() // 2)
            return np.array([colour.red(), colour.green(), colour.blue()])
        np.testing.assert_allclose(center(), [64, 128, 191], atol=2)
        view.exposure = 1.0
        view.update()
        np.testing.assert_allclose(center(), [128, 255, 255], atol=2)
        view.exposure = 0.0
        view.channel = 1
        view.update()
        np.testing.assert_allclose(center(), [64, 64, 64], atol=2)
        view.channel = 0
        for color_view in views():
            view.color_view = color_view
            view.update()
            expected = display_pixels(pixels, {"view": color_view})[0, 0, :3]
            np.testing.assert_allclose(center(), np.clip(expected, 0, 1) * 255, atol=3)
        view.color_view = "Raw"
        pixels[:4] = [1.0, 0.0, 0.0, 1.0]
        pixels[4:] = [0.0, 0.0, 1.0, 1.0]
        view.channel = 0
        view.set_image(PreviewImage(pixels, 8, 8))
        frame = view.grabFramebuffer()
        assert frame.pixelColor(frame.width() // 2, frame.height() // 3).red() > 240
        assert frame.pixelColor(frame.width() // 2, 2 * frame.height() // 3).blue() > 240
    finally:
        view.cleanup()
        view.close()
