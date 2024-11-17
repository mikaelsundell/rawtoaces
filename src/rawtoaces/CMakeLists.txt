# Copyright Contributors to the rawtoaces project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/rawtoaces

cmake_minimum_required(VERSION 3.5)
include_directories( "${CMAKE_CURRENT_SOURCE_DIR}" )

add_executable( 
    rawtoaces
    main.cpp
)

set_property(TARGET rawtoaces PROPERTY CXX_STANDARD 17)

target_include_directories(rawtoaces
    PUBLIC
        ${OpenImageIO_INCLUDE_DIR}
)

target_link_libraries( 
    rawtoaces
    PUBLIC
        rawtoaces_util
)

install(TARGETS rawtoaces DESTINATION bin)
