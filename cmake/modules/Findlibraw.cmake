# Copyright Contributors to the rawtoaces project.
# SPDX-License-Identifier: Apache-2.0
# https://github.com/AcademySoftwareFoundation/rawtoaces

find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
  pkg_check_modules(PC_LIBRAW QUIET libraw)
endif()

# Adjust paths on macOS
if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  if(PC_LIBRAW_FOUND AND "${PC_LIBRAW_INCLUDEDIR}" MATCHES ".*/Cellar/.*")
    set(_libraw_HINT_INCLUDE /usr/local/include)
    set(_libraw_HINT_LIB /usr/local/lib)
  endif()
endif()

if(PC_LIBRAW_FOUND)
  set(libraw_CFLAGS ${PC_LIBRAW_CFLAGS_OTHER})
  set(libraw_LIBRARY_DIRS ${PC_LIBRAW_LIBRARY_DIRS})
  set(libraw_LDFLAGS ${PC_LIBRAW_LDFLAGS_OTHER})
  if("${_libraw_HINT_INCLUDE}" STREQUAL "")
    set(_libraw_HINT_INCLUDE ${PC_LIBRAW_INCLUDEDIR} ${PC_LIBRAW_INCLUDE_DIRS})
    set(_libraw_HINT_LIB ${PC_LIBRAW_LIBDIR} ${PC_LIBRAW_LIBRARY_DIRS})
  endif()
else()
  if(UNIX)
    set(libraw_CFLAGS "-pthread")
    if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    else()
      set(libraw_LDFLAGS "-pthread")
    endif()
  endif()
endif()

# Locate include directory
find_path(libraw_INCLUDE_DIR libraw_version.h
          HINTS ${_libraw_HINT_INCLUDE}
          PATH_SUFFIXES libraw)
if(libraw_INCLUDE_DIR AND EXISTS "${libraw_INCLUDE_DIR}/libraw_version.h")
  set(libraw_VERSION ${PC_LIBRAW_VERSION})

  if("${libraw_VERSION}" STREQUAL "")
    file(STRINGS "${libraw_INCLUDE_DIR}/libraw_version.h" libraw_version_str
         REGEX "^#define[\t ]+LIBRAW_VERSION_STR[\t ]+\".*")

    string(REGEX REPLACE "^#define[\t ]+LIBRAW_VERSION[\t ]+\"([^ \\n]*)\".*"
           "\\1" libraw_VERSION "${libraw_version_str}")
    unset(libraw_version_str)
  endif()
endif()

# Locate the library
find_library(RAW_LIBRARY
             NAMES raw
             HINTS ${_libraw_HINT_LIB})

if(RAW_LIBRARY)
  set(libraw_LIBRARY ${RAW_LIBRARY})
  mark_as_advanced(${RAW_LIBRARY})
endif()

unset(_libraw_HINT_INCLUDE)
unset(_libraw_HINT_LIB)

set(libraw_LIBRARIES ${libraw_LIBRARY})
set(libraw_INCLUDE_DIRS ${libraw_INCLUDE_DIR})

if(NOT PC_LIBRAW_FOUND)
  get_filename_component(libraw_LDFLAGS_OTHER ${libraw_LIBRARY} PATH)
  set(libraw_LDFLAGS_OTHER -L${libraw_LDFLAGS_OTHER})
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(libraw
  REQUIRED_VARS libraw_LIBRARY libraw_INCLUDE_DIR
  VERSION_VAR libraw_VERSION
  FAIL_MESSAGE "Unable to find LibRaw library")

if(LIBRAW_FOUND AND NOT libraw_FOUND)
  set(libraw_FOUND 1)
endif()

mark_as_advanced(libraw_INCLUDE_DIR libraw_LIBRARY)

# Create a CMake interface target
if(libraw_FOUND)
  add_library(libraw INTERFACE)

  # Set include directories
  target_include_directories(libraw INTERFACE ${libraw_INCLUDE_DIRS})

  # Set libraries
  target_link_libraries(libraw INTERFACE ${libraw_LIBRARIES})

  # Set compile options
  target_compile_options(libraw INTERFACE ${libraw_CFLAGS})

  # Set linker flags
  target_link_options(libraw INTERFACE ${libraw_LDFLAGS})
endif()
