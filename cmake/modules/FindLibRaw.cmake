#
# FindLibRaw.cmake - Locate LibRaw
#
# This will define:
#   LibRaw_FOUND - True if LibRaw was found
#   LibRaw_INCLUDE_DIRS - Include directories for LibRaw
#   LibRaw_LIBRARIES - Libraries to link against
#   LibRaw_VERSION - Detected version
# And create imported target:
#   LibRaw::LibRaw
#

find_package(PkgConfig QUIET)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(PC_LibRaw QUIET libraw)
endif()

if(${CMAKE_SYSTEM_NAME} MATCHES "Darwin" AND PC_LibRaw_FOUND AND "${PC_LibRaw_INCLUDEDIR}" MATCHES ".*/Cellar/.*")
    set(_LibRaw_HINT_INCLUDE /usr/local/include)
    set(_LibRaw_HINT_LIB /usr/local/lib)
endif()

if(PC_LibRaw_FOUND)
    set(LibRaw_CFLAGS ${PC_LibRaw_CFLAGS_OTHER})
    set(LibRaw_LIBRARY_DIRS ${PC_LibRaw_LIBRARY_DIRS})
    set(LibRaw_LDFLAGS ${PC_LibRaw_LDFLAGS_OTHER})
    if("${_LibRaw_HINT_INCLUDE}" STREQUAL "")
        set(_LibRaw_HINT_INCLUDE ${PC_LibRaw_INCLUDEDIR} ${PC_LibRaw_INCLUDE_DIRS})
        set(_LibRaw_HINT_LIB ${PC_LibRaw_LIBDIR} ${PC_LibRaw_LIBRARY_DIRS})
    endif()
endif()

find_path(LibRaw_INCLUDE_DIR libraw/libraw.h
    HINTS ${_LibRaw_HINT_INCLUDE}
)
# Detect version
if(LibRaw_INCLUDE_DIR AND EXISTS "${LibRaw_INCLUDE_DIR}/libraw_version.h")
    file(STRINGS "${LibRaw_INCLUDE_DIR}/libraw_version.h" libraw_version_str
         REGEX "^#define[\t ]+LIBRAW_VERSION_STR[\t ]+\".*")
    string(REGEX REPLACE "^#define[\t ]+LIBRAW_VERSION_STR[\t ]+\"([^ \\n]*)\".*"
           "\\1" LibRaw_VERSION "${libraw_version_str}")
endif()

find_library(LibRaw_LIBRARY
    NAMES raw libraw
    HINTS ${_LibRaw_HINT_LIB}
)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(LibRaw
    REQUIRED_VARS LibRaw_LIBRARY LibRaw_INCLUDE_DIR
    VERSION_VAR LibRaw_VERSION
)

if(LibRaw_FOUND)
    set(LibRaw_INCLUDE_DIRS ${LibRaw_INCLUDE_DIR})
    set(LibRaw_LIBRARIES ${LibRaw_LIBRARY})

    # Create imported target
    if(NOT TARGET LibRaw::LibRaw)
        add_library(LibRaw::LibRaw UNKNOWN IMPORTED)
        set_target_properties(LibRaw::LibRaw PROPERTIES
            IMPORTED_LOCATION "${LibRaw_LIBRARY}"
            INTERFACE_INCLUDE_DIRECTORIES "${LibRaw_INCLUDE_DIRS}"
        )
    endif()
endif()

mark_as_advanced(LibRaw_INCLUDE_DIR LibRaw_LIBRARY)
