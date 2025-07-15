cmake_minimum_required(VERSION 3.5)

add_library(${RAWTOACESIDTLIB} ${DO_SHARED}
    rta.cpp
)

set_target_properties(${RAWTOACESIDTLIB} PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES ""
)

target_sources(${RAWTOACESIDTLIB} PRIVATE
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/define.h
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/mathOps.h
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/rta.h
)

target_include_directories(${RAWTOACESIDTLIB}
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/../../include>
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

target_link_libraries(${RAWTOACESIDTLIB}
    PUBLIC
        Eigen3::Eigen
)

target_link_libraries(${RAWTOACESIDTLIB}
    PRIVATE
        Boost::filesystem
        Boost::system
        Imath::Imath
        Imath::ImathConfig
)

if (TARGET LibRaw::LibRaw)
    target_link_libraries(${RAWTOACESIDTLIB} PUBLIC LibRaw::LibRaw)
else()
    if (LibRaw_INCLUDE_DIRS)
        target_include_directories(${RAWTOACESIDTLIB} PUBLIC ${LibRaw_INCLUDE_DIRS})
    endif()
    if (LibRaw_LIBRARY_DIRS)
        target_link_directories(${RAWTOACESIDTLIB} PRIVATE ${LibRaw_LIBRARY_DIRS})
    endif()
    if (LibRaw_LIBRARIES)
        target_link_libraries(${RAWTOACESIDTLIB} PUBLIC ${LibRaw_LIBRARIES} ${LibRaw_LDFLAGS_OTHER})
    endif()
endif()

if (${Ceres_VERSION_MAJOR} GREATER 1)
    target_link_libraries(${RAWTOACESIDTLIB} PUBLIC Ceres::ceres)
else()
    if (CERES_INCLUDE_DIRS)
        target_include_directories(${RAWTOACESIDTLIB}
            PUBLIC $<BUILD_INTERFACE:${CERES_INCLUDE_DIRS}>
        )
    endif()
    target_link_libraries(${RAWTOACESIDTLIB} PUBLIC ${CERES_LIBRARIES})
endif()

set(RAWTOACESIDT_HEADERS
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/define.h
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/mathOps.h
    ${PROJECT_SOURCE_DIR}/include/rawtoaces/rta.h
)

set_target_properties(${RAWTOACESIDTLIB} PROPERTIES
    SOVERSION ${RAWTOACES_MAJOR_VERSION}.${RAWTOACES_MINOR_VERSION}.${RAWTOACES_PATCH_VERSION}
    VERSION ${RAWTOACES_VERSION}
    PUBLIC_HEADER "${RAWTOACESIDT_HEADERS}"
)

install(TARGETS ${RAWTOACESIDTLIB}
    EXPORT ${PROJECT_NAME}Targets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/rawtoaces
)
