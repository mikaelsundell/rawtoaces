# Copyright Contributors to the rawtoaces project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/rawtoaces

add_library(rawtoaces_util ${DO_SHARED}
    rawtoaces_util.cpp
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/rawtoaces_util.h
)

set_property(TARGET rawtoaces_util PROPERTY CXX_STANDARD 17)

include_directories( "${CMAKE_CURRENT_SOURCE_DIR}" )

target_include_directories(rawtoaces_util PRIVATE ${OIIO_INCLUDE_DIRS} )
target_link_directories(rawtoaces_util PUBLIC  ${OIIO_LIBRARY_DIRS} )
target_link_libraries(rawtoaces_util
    PUBLIC
        ${OIIO_LIBRARIES}
        ${OIIO_LDFLAGS_OTHER}
)
 
target_link_libraries(rawtoaces_util
    PUBLIC
        rawtoaces_idt
        OpenImageIO::OpenImageIO
)
    
set_target_properties(rawtoaces_util
    PROPERTIES
    SOVERSION ${Rawtoaces_MAJOR_VERSION}.${Rawtoaces_MINOR_VERSION}.${Rawtoaces_PATCH_VERSION}
    VERSION ${Rawtoaces_VERSION} 
)
    
install(
    FILES ${PROJECT_SOURCE_DIR}/include/rawtoaces/rawtoaces_util.h	 	
    DESTINATION include/rawtoaces
)

install(TARGETS rawtoaces_util DESTINATION lib)
