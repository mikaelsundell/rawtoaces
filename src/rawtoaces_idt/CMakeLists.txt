# Copyright Contributors to the rawtoaces project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/rawtoaces

add_library( rawtoaces_idt ${DO_SHARED}
    rawtoaces_idt.cpp
    # Make the headers visible in IDEs. This should not affect the builds.
    ../../include/rawtoaces/define.h
    ../../include/rawtoaces/mathOps.h
    ../../include/rawtoaces/rawtoaces_idt.h
)

include_directories( "${CMAKE_CURRENT_SOURCE_DIR}" )

target_link_libraries(
    rawtoaces_idt
    PUBLIC
        libraw
        Boost::boost
        Boost::system
        Boost::filesystem
        Imath::Imath
        Imath::ImathConfig
)

if (${Ceres_VERSION_MAJOR} GREATER 1)
    target_link_libraries(rawtoaces_idt PUBLIC Ceres::ceres)
else ()
    target_include_directories(rawtoaces_idt PUBLIC ${CERES_INCLUDE_DIRS})
    target_link_libraries(rawtoaces_idt PUBLIC ${CERES_LIBRARIES})
endif ()

set_target_properties(rawtoaces_idt PROPERTIES
    SOVERSION ${Rawtoaces_MAJOR_VERSION}.${Rawtoaces_MINOR_VERSION}.${Rawtoaces_PATCH_VERSION}
    VERSION ${Rawtoaces_VERSION}
)

set_target_properties(rawtoaces_idt PROPERTIES
    INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
)

install(FILES
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/define.h
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/mathOps.h
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/rta.h
 	DESTINATION include/rawtoaces
)

install(TARGETS rawtoaces_idt DESTINATION lib)
