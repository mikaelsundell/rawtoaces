cmake_minimum_required(VERSION 3.5)
project( RAWTOACES )

set( RAWTOACES_MAJOR_VERSION 1 )
set( RAWTOACES_MINOR_VERSION 0 )
set( RAWTOACES_PATCH_VERSION 0 )
set( RAWTOACES_VERSION ${RAWTOACES_MAJOR_VERSION}.${RAWTOACES_MINOR_VERSION}.${RAWTOACES_PATCH_VERSION} )

set(RAWTOACESIDTLIB "rawtoaces_idt")
set(RAWTOACESLIB "rawtoaces_util")

set( CMAKE_MACOSX_RPATH 1 )

if ("${CMAKE_CXX_COMPILER_ID}" STREQUAL "MSVC")
#    set(warnings "/W4 /WX /EHsc")
    add_compile_options ( /W0 )
    add_compile_definitions( NOMINMAX )
endif()

if (NOT CONFIGURED_ONCE)
	set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${warnings}")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${warnings}")
endif()

## Make install directories overridable
set( INSTALL_LIB_DIR lib CACHE PATH "Install directory for libraries" )
set( INSTALL_BIN_DIR bin CACHE PATH "Install directory for executable binaries" )
set( INSTALL_INCLUDE_DIR include CACHE PATH "Install directory for public header files" )
if( WIN32 AND NOT CYGWIN )
  set(DEF_INSTALL_CMAKE_DIR CMake)
else()
  set(DEF_INSTALL_CMAKE_DIR lib/CMake/RAWTOACES)
endif()
set(INSTALL_CMAKE_DIR ${DEF_INSTALL_CMAKE_DIR} CACHE PATH "Install directory for project CMake files" )

# use, i.e. don't skip the full RPATH for the build tree
SET(CMAKE_SKIP_BUILD_RPATH FALSE)
# when building, don't use the install RPATH already
# (but later on when installing)
SET(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE) 
# SET(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
# add the automatically determined parts of the RPATH
# which point to directories outside the build tree to the install RPATH
SET(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
# the RPATH to be used when installing, but only if it's not a system directory
LIST(FIND CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES "${CMAKE_INSTALL_PREFIX}/lib" isSystemDir)
IF("${isSystemDir}" STREQUAL "-1")
  SET(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
ENDIF("${isSystemDir}" STREQUAL "-1")

## convert install paths to absolute
foreach( p LIB BIN INCLUDE CMAKE )
  set( var INSTALL_${p}_DIR )
  if( NOT IS_ABSOLUTE "${${var}}" )
    set( ${var} "${CMAKE_INSTALL_PREFIX}/${${var}}" )
  endif()
endforeach()

option( ENABLE_SHARED "Enable Shared Libraries" ON )
option( RTA_CENTOS7_CERES_HACK "Work around broken config in ceres-solver 1.12" OFF )

if ( ENABLE_SHARED )
  set ( DO_SHARED SHARED )
else ()
  set ( DO_SHARED STATIC )
endif ()

include ( configure.cmake )

# generated config files end up in binary dir so to find them, need
# to add to include path
include_directories( "${PROJECT_SOURCE_DIR}/include" )

add_definitions( -DPACKAGE="RAWTOACES" -DVERSION="${RAWTOACES_VERSION}" )
add_subdirectory("src/${RAWTOACESIDTLIB}")
add_subdirectory("src/${RAWTOACESLIB}")

if ( APPLE OR UNIX )
	install (DIRECTORY data DESTINATION include/rawtoaces)
endif()

### to build rawtoaces ###

add_executable( rawtoaces
    main.cpp
)

target_include_directories(rawtoaces
    PRIVATE
        ${AcesContainer_INCLUDE_DIRS}
)

target_link_libraries(rawtoaces
    PRIVATE
        ${RAWTOACESLIB}
        Boost::filesystem
        Boost::system
)

if ( LIBRAW_CONFIG_FOUND )
    target_link_libraries ( rawtoaces PUBLIC libraw::raw )
else ()
    target_link_directories(rawtoaces PUBLIC ${LibRaw_LIBRARY_DIRS} )
    target_link_libraries(rawtoaces PUBLIC ${LibRaw_LIBRARIES} ${LibRaw_LDFLAGS_OTHER} )
endif ()

enable_testing()
add_subdirectory(unittest)

install( TARGETS rawtoaces DESTINATION bin )

include( GNUInstallDirs )
include( CMakePackageConfigHelpers )

if ( PKG_CONFIG_FOUND )
   configure_file (config/RAWTOACES.pc.in "${PROJECT_BINARY_DIR}/RAWTOACES.pc" @ONLY )
   install (FILES "${PROJECT_BINARY_DIR}/RAWTOACES.pc" DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig COMPONENT dev )
endif ()

file( WRITE "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Targets.cmake" "# Dummy file" )

write_basic_package_version_file(
    "${PROJECT_NAME}ConfigVersion.cmake"
    VERSION ${RAWTOACES_VERSION}
    COMPATIBILITY SameMajorVersion
)

configure_package_config_file(
    config/${PROJECT_NAME}Config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)

install(FILES cmake/modules/FindLibRaw.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}/modules
)

install (
    FILES
        "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}Config.cmake"
        "${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}ConfigVersion.cmake"
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
)

install(
    EXPORT ${PROJECT_NAME}Targets
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME}
    FILE ${PROJECT_NAME}Targets.cmake
    NAMESPACE ${PROJECT_NAME}::
    EXPORT_LINK_INTERFACE_LIBRARIES
)

install( DIRECTORY data DESTINATION ${CMAKE_INSTALL_DATADIR}/${PROJECT_NAME} )
