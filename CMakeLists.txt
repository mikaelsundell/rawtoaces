# Copyright Contributors to the rawtoaces project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/rawtoaces

cmake_minimum_required (VERSION 3.10)
project (RawToAces)

set (RawToAces_MAJOR_VERSION 1)
set (RawToAces_MINOR_VERSION 0)
set (RawToAces_PATCH_VERSION 1)
set (RawToAces_VERSION ${RAWTOACES_MAJOR_VERSION}.${RAWTOACES_MINOR_VERSION}.${RAWTOACES_PATCH_VERSION})

set (RawToAcesIdt_LIB "RawToAces_idt")
set (RawToAcesUtil_LIB "RawToAces_util")
set (RawToAcesUtil2_LIB "RawToAces_util2")

set (RawToAces_BIN "rawtoaces")
set (RawToAces2_BIN "rawtoaces2")

set (CMAKE_MACOSX_RPATH 1)

if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC")
    add_compile_options (/W)
    add_compile_definitions (NOMINMAX)
    add_compile_options ($<$<COMPILE_LANGUAGE:CXX>:/utf-8>)
endif ()

if (NOT CONFIGURED_ONCE)
    set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${warnings}")
    set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${warnings}")
endif ()

# make install directories overridable
set (INSTALL_LIB_DIR lib CACHE PATH "Install directory for libraries")
set (INSTALL_BIN_DIR bin CACHE PATH "Install directory for executable binaries")
set (INSTALL_INCLUDE_DIR include CACHE PATH "Install directory for public header files")
if (WIN32 AND NOT CYGWIN )
    set (DEF_INSTALL_CMAKE_DIR CMake)
else ()
    set (DEF_INSTALL_CMAKE_DIR lib/CMake/${PROJECT_NAME})
endif ()
set (INSTALL_CMAKE_DIR ${DEF_INSTALL_CMAKE_DIR} CACHE PATH "Install directory for project CMake files")

# use, i.e. don't skip the full RPATH for the build tree
set (CMAKE_SKIP_BUILD_RPATH FALSE)

# when building, don't use the install RPATH already
# (but later on when installing)
set (CMAKE_BUILD_WITH_INSTALL_RPATH FALSE) 

# SET(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
# add the automatically determined parts of the RPATH
# which point to directories outside the build tree to the install RPATH
set (CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# the RPATH to be used when installing, but only if it's not a system directory
list (FIND CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES "${CMAKE_INSTALL_PREFIX}/lib" isSystemDir)
if ("${isSystemDir}" STREQUAL "-1")
    set (CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
endif ("${isSystemDir}" STREQUAL "-1")

# convert install paths to absolute
foreach (p LIB BIN INCLUDE CMAKE)
    set (var INSTALL_${p}_DIR)
    if (NOT IS_ABSOLUTE "${${var}}")
        set (${var} "${CMAKE_INSTALL_PREFIX}/${${var}}")
     endif ()
endforeach ()

option (ENABLE_SHARED "Enable Shared Libraries" ON)

if ( ENABLE_SHARED )
  set ( DO_SHARED SHARED )
else ()
  set ( DO_SHARED STATIC )
endif ()

include ( configure.cmake )

# generated config files end up in binary dir so to find them, need
# to add to include path
include_directories ("${PROJECT_SOURCE_DIR}/include")

add_definitions ( -DPACKAGE="RawToAces" -DVERSION="${RawToAces_VERSION}" )
add_subdirectory ("src/${RawToAcesIdt_LIB}")
add_subdirectory ("src/${RawToAcesUtil_LIB}")
add_subdirectory ("src/${RawToAcesUtil2_LIB}")
add_subdirectory ("src/rawtoaces")
add_subdirectory ("src/rawtoaces2")
 
# create a RawToAcesBuildTreeSettings.cmake file for the use from the build tree
file (RELATIVE_PATH CONF_REL_INCLUDE_DIR "${INSTALL_CMAKE_DIR}" "${INSTALL_INCLUDE_DIR}")
configure_file (config/RawToAcesBuildTreeSettings.cmake.in "${PROJECT_BINARY_DIR}/RawToAcesBuildTreeSettings.cmake" @ONLY)
configure_file (config/RawToAcesConfig.cmake.in "${PROJECT_BINARY_DIR}/RawToAcesConfig.cmake" @ONLY)
configure_file (config/RawToAcesConfigVersion.cmake.in "${PROJECT_BINARY_DIR}/RawToAcesConfigVersion.cmake" @ONLY)

if (PKG_CONFIG_FOUND)
  configure_file (config/RawToAces.pc.in "${PROJECT_BINARY_DIR}/RawToAces.pc" @ONLY)
  install (FILES "${PROJECT_BINARY_DIR}/RawToAces.pc" DESTINATION lib/pkgconfig COMPONENT dev)
endif()

install( FILES
  "${PROJECT_BINARY_DIR}/RawToAcesConfig.cmake"
  "${PROJECT_BINARY_DIR}/RawToAcesConfigVersion.cmake"
  DESTINATION "${INSTALL_CMAKE_DIR}" COMPONENT dev)

if (WIN32 AND NOT CYGWIN)
    install (FILES "${PROJECT_BINARY_DIR}/RawToAcesLibraryDepends.cmake" DESTINATION "${INSTALL_CMAKE_DIR}" COMPONENT dev)
endif ()

if (APPLE OR UNIX)
	include (GNUInstallDirs)

	install(
        TARGETS ${RawToAcesIdt_LIB} ${RawToAcesUtil_LIB} ${RawToAcesUtil2_LIB} ${RawToAces_BIN} ${RawToAces2_BIN}
        EXPORT RawToAcesConfig
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    )
    export(
        TARGETS ${RawToAcesIdt_LIB} ${RawToAcesUtil_LIB} ${RawToAcesUtil2_LIB} ${RawToAces_BIN} ${RawToAces2_BIN}
        NAMESPACE ${PROJECT_NAME}::
        FILE "${CMAKE_CURRENT_BINARY_DIR}/RawToAcesConfig.cmake"
    )
    install(
        EXPORT ${PROJECT_NAME}Config
        DESTINATION "${CMAKE_INSTALL_LIBDIR}/CMake/RawToAces"
        NAMESPACE ${PROJECT_NAME}::
    )
    install (DIRECTORY data DESTINATION ${CMAKE_INSTALL_DATADIR}/${PROJECT_NAME})
endif()

add_subdirectory (unittest)

# uninstall target
configure_file (
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY)

add_custom_target(uninstall COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)
