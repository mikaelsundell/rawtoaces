cmake_minimum_required(VERSION 3.5)
include_directories( "${CMAKE_CURRENT_SOURCE_DIR}" )

add_library ( ${RAWTOACESLIB} ${DO_SHARED}
    acesrender.cpp
    ../../include/rawtoaces/acesrender.h
)

target_include_directories(${RAWTOACESLIB}
    PUBLIC
        $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(${RAWTOACESLIB}
    PUBLIC
        ${RAWTOACESIDTLIB}
        Eigen3::Eigen
)

target_link_libraries(${RAWTOACESLIB}
    PRIVATE
        Boost::filesystem
        Boost::system
        Imath::Imath
        Imath::ImathConfig
)

if (AcesContainer_FOUND)
    target_include_directories(${RAWTOACESLIB} PUBLIC ${AcesContainer_INCLUDE_DIRS})
    target_link_directories(${RAWTOACESLIB} PUBLIC ${AcesContainer_LIBRARY_DIRS})
    target_link_libraries(${RAWTOACESLIB} PUBLIC ${AcesContainer_LIBRARIES})
endif()

if (TARGET LibRaw::LibRaw)
    target_link_libraries(${RAWTOACESLIB} PUBLIC LibRaw::LibRaw)
else()
    if (LibRaw_INCLUDE_DIRS)
        target_include_directories(${RAWTOACESLIB} PUBLIC ${LibRaw_INCLUDE_DIRS})
    endif()
    if (LibRaw_LIBRARIES)
        target_link_libraries(${RAWTOACESLIB} PUBLIC ${LibRaw_LIBRARIES})
    endif()
endif()

set_target_properties(${RAWTOACESLIB} PROPERTIES
    SOVERSION ${RAWTOACES_MAJOR_VERSION}.${RAWTOACES_MINOR_VERSION}.${RAWTOACES_PATCH_VERSION}
    VERSION ${RAWTOACES_VERSION}
    PUBLIC_HEADER "${PROJECT_SOURCE_DIR}/include/rawtoaces/acesrender.h"
)

install(TARGETS ${RAWTOACESLIB}
    EXPORT ${PROJECT_NAME}Targets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/rawtoaces
)