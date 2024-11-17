# Copyright Contributors to the rawtoaces project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/rawtoaces

cmake_minimum_required(VERSION 3.5)
project(Rawtoaces)

set(Rawtoaces_MAJOR_VERSION 1)
set(Rawtoaces_MINOR_VERSION 0)
set(Rawtoaces_PATCH_VERSION 0)
set(Rawtoaces_VERSION ${Rawtoaces_MAJOR_VERSION}.${Rawtoaces_MINOR_VERSION}.${Rawtoaces_PATCH_VERSION})

if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC")
    add_compile_options ( /W0 )
    add_compile_definitions( NOMINMAX )
    add_compile_options ( $<$<COMPILE_LANGUAGE:CXX>:/utf-8> )
endif()

if (NOT CONFIGURED_ONCE)
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${warnings}")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${warnings}")
endif()

# make install directories overridable
set( INSTALL_LIB_DIR lib CACHE PATH "Install directory for libraries" )
set( INSTALL_BIN_DIR bin CACHE PATH "Install directory for executable binaries" )
set( INSTALL_INCLUDE_DIR include CACHE PATH "Install directory for public header files" )
if( WIN32 AND NOT CYGWIN )
  set(DEF_INSTALL_CMAKE_DIR CMake)
else()
  set(DEF_INSTALL_CMAKE_DIR lib/CMake/Rawtoaces)
endif()
set(INSTALL_CMAKE_DIR ${DEF_INSTALL_CMAKE_DIR} CACHE PATH "Install directory for project CMake files" )

if (APPLE)
  set(CMAKE_MACOSX_RPATH FALSE)
endif()

# convert install paths to absolute
foreach( p LIB BIN INCLUDE CMAKE )
  set( var INSTALL_${p}_DIR )
  if( NOT IS_ABSOLUTE "${${var}}" )
    set( ${var} "${CMAKE_INSTALL_PREFIX}/${${var}}" )
  endif()
endforeach()

option( ENABLE_SHARED "Enable Shared Libraries" ON )
if ( ENABLE_SHARED )
  set ( DO_SHARED SHARED )
else ()
  set ( DO_SHARED STATIC )
endif ()

include ( configure.cmake )

# generated config files end up in binary dir so to find them, need
# to add to include path
include_directories( "${PROJECT_SOURCE_DIR}/include" )
add_subdirectory("src/rawtoaces_idt")
add_subdirectory("src/rawtoaces_util")
add_subdirectory("src/rawtoaces")
 
# create a RawtoacesBuildTreeSettings.cmake file for the use from the build tree
add_definitions(-DPACKAGE="Rawtoaces" -DVERSION="${Rawtoaces_VERSION}" )
configure_file(config/RawtoacesBuildTreeSettings.cmake.in "${PROJECT_BINARY_DIR}/RawtoacesBuildTreeSettings.cmake" @ONLY)
configure_file(config/RawtoacesConfig.cmake.in "${PROJECT_BINARY_DIR}/RawtoacesConfig.cmake" @ONLY)
configure_file(config/RawtoacesConfigVersion.cmake.in "${PROJECT_BINARY_DIR}/RawtoacesConfigVersion.cmake" @ONLY)

if ( PKG_CONFIG_FOUND )
  configure_file(config/Rawtoaces.pc.in "${PROJECT_BINARY_DIR}/Rawtoaces.pc" @ONLY)
  install( FILES "${PROJECT_BINARY_DIR}/Rawtoaces.pc" DESTINATION lib/pkgconfig COMPONENT dev )
endif()

install( FILES
  "${PROJECT_BINARY_DIR}/RawtoacesConfig.cmake"
  "${PROJECT_BINARY_DIR}/RawtoacesConfigVersion.cmake"
  DESTINATION "${INSTALL_CMAKE_DIR}" COMPONENT dev)

if ( WIN32 AND NOT CYGWIN )
install( FILES "${PROJECT_BINARY_DIR}/RawtoacesLibraryDepends.cmake" DESTINATION
  "${INSTALL_CMAKE_DIR}" COMPONENT dev )
endif( )

if ( APPLE OR UNIX )
	install (DIRECTORY data DESTINATION include/rawtoaces)
endif()

enable_testing()
add_subdirectory(unittest)

# uninstall target
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake_uninstall.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake"
    IMMEDIATE @ONLY)

add_custom_target(uninstall
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake)


