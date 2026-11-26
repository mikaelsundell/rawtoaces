# SPDX-License-Identifier: Apache-2.0
# Copyright Contributors to the rawtoaces project.

# Check the runtime selected for the extension, rather than a separate Qt SDK.
execute_process(
    COMMAND "${Python_EXECUTABLE}" -c
        "from PySide6 import QtCore, QtWidgets, QtOpenGL, QtOpenGLWidgets, QtUiTools; import OpenImageIO, PyOpenColorIO, numpy; PyOpenColorIO.Config.CreateFromBuiltinConfig('studio-config-v2.2.0_aces-v1.3_ocio-v2.4'); print(QtCore.qVersion())"
    RESULT_VARIABLE _pyside_result OUTPUT_VARIABLE _pyside_version
    ERROR_VARIABLE _pyside_error OUTPUT_STRIP_TRAILING_WHITESPACE
)
if ( NOT _pyside_result EQUAL 0 )
    message(FATAL_ERROR
        "The Python UI requires PySide6 (including QtOpenGLWidgets), OpenImageIO "
        "OpenColorIO 2.4+ and numpy in ${Python_EXECUTABLE}. Install compatible packages into "
        "that environment, then reconfigure.\n"
        "${_pyside_error}")
endif()
message(STATUS "Python UI: PySide6 / Qt ${_pyside_version} (${Python_EXECUTABLE})")

# Each configuration gets its matching extension, including on Visual Studio.
set(_ui_stage "${PROJECT_BINARY_DIR}/python/$<CONFIG>")
add_custom_target(rawtoaces_python_ui ALL
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${_ui_stage}"
    COMMAND "${CMAKE_COMMAND}" -E copy_directory
        "${CMAKE_CURRENT_SOURCE_DIR}/rawtoaces_ui" "${_ui_stage}/rawtoaces_ui"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        "$<TARGET_FILE:rawtoaces_bindings>" "${_ui_stage}"
    DEPENDS rawtoaces_bindings
    COMMENT "Staging the rawtoaces Python application"
    VERBATIM
)

set(RTA_UI_MODULE_DIR "${_ui_stage}")
configure_file(launcher.py.in "${CMAKE_CURRENT_BINARY_DIR}/build-launcher.py.in" @ONLY)
file(GENERATE OUTPUT "${_ui_stage}/rawtoaces-ui.py"
    INPUT "${CMAKE_CURRENT_BINARY_DIR}/build-launcher.py.in")
add_custom_target(run_python_ui
    COMMAND "${Python_EXECUTABLE}" "${_ui_stage}/rawtoaces-ui.py"
    DEPENDS rawtoaces_python_ui
    USES_TERMINAL VERBATIM
)

file(RELATIVE_PATH RTA_UI_MODULE_DIR "${INSTALL_BIN_DIR}" "${INSTALL_LIB_DIR}")
configure_file(launcher.py.in "${CMAKE_CURRENT_BINARY_DIR}/rawtoaces-ui" @ONLY)
if(WIN32)
    install(PROGRAMS "${CMAKE_CURRENT_BINARY_DIR}/rawtoaces-ui"
        DESTINATION "${INSTALL_BIN_DIR}" RENAME rawtoaces-ui.py)
    configure_file(launcher.cmd.in "${CMAKE_CURRENT_BINARY_DIR}/rawtoaces-ui.cmd" @ONLY)
    install(PROGRAMS "${CMAKE_CURRENT_BINARY_DIR}/rawtoaces-ui.cmd"
        DESTINATION "${INSTALL_BIN_DIR}")
else()
    install(PROGRAMS "${CMAKE_CURRENT_BINARY_DIR}/rawtoaces-ui"
        DESTINATION "${INSTALL_BIN_DIR}")
endif()
install(DIRECTORY rawtoaces_ui DESTINATION "${INSTALL_LIB_DIR}"
    FILES_MATCHING PATTERN "*.py" PATTERN "*.ui" PATTERN "*.qss"
    PATTERN "__pycache__" EXCLUDE)

if(RTA_BUILD_TESTS)
    if(WIN32)
        set(_ui_test_pythonpath "${_ui_stage};$ENV{PYTHONPATH}")
    else()
        set(_ui_test_pythonpath "${_ui_stage}:$ENV{PYTHONPATH}")
    endif()
    add_test(NAME Test_Python_UI
        COMMAND "${CMAKE_COMMAND}" -E env
            "PYTHONPATH=${_ui_test_pythonpath}" "QT_QPA_PLATFORM=offscreen"
            "${Python_EXECUTABLE}" -m pytest
            "${PROJECT_SOURCE_DIR}/tests/python/test_python_ui.py" -v)
endif()
