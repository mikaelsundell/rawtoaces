cmake_minimum_required(VERSION 3.12)

# Include coverage support if enabled
if(ENABLE_COVERAGE)
    include(${CMAKE_CURRENT_SOURCE_DIR}/../../cmake/CodeCoverage.cmake)
endif()

if(Qt6_FOUND)
    message(STATUS "Building rawtoaces_gui (Qt6 detected)")

    add_executable(rawtoaces_gui
        main.cpp
    )

    target_link_libraries(rawtoaces_gui
        PRIVATE
            Qt6::Core
            Qt6::Gui
            Qt6::GuiPrivate
            Qt6::Widgets
    )

    # Coverage setup when enabled
    if(ENABLE_COVERAGE AND COVERAGE_SUPPORTED)
        setup_coverage_flags(rawtoaces_gui)
    endif()

    install(TARGETS rawtoaces_gui DESTINATION ${INSTALL_BIN_DIR})

else()
    message(WARNING
        "Qt6 not found. Skipping rawtoaces_gui (GUI application will not be built)."
    )

endif()
