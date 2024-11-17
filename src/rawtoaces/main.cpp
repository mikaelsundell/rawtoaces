// Copyright Contributors to the rawtoaces project.
// SPDX-License-Identifier: Apache-2.0
// https://github.com/AcademySoftwareFoundation/rawtoaces

#include <rawtoaces/rawtoaces_util.h>

#include <filesystem>

using namespace rta;

int main( int argc, const char *argv[] )
{
    std::cout << "rawtoaces2" << std::endl;
    
    std::cout << std::endl;
    
    ImageConverter converter;

    if ( !converter.parse( argc, argv ) )
    {
        return 1;
    }

    std::cout << "Parse arguments" << std::endl
              << "-----------------------------------" << std::endl;

    for (int i = 0; i < argc; ++i)
    {
        std::cout << argv[i] << std::endl;
    }
    
    auto                    &argParse = converter.argParse();
    auto                     files = argParse["filename"].as_vec<std::string>();
    std::vector<std::string> files_to_convert;

    for ( auto filename: files )
    {
        if ( !std::filesystem::exists( filename ) )
        {
            std::cerr << "File or directory not found: " << filename
                      << std::endl;
            return 1;
        }

        auto canonical_filename = std::filesystem::canonical( filename );

        if ( std::filesystem::is_directory( filename ) )
        {
            auto it = std::filesystem::directory_iterator( filename );

            for ( auto filename2: it )
            {
                if ( std::filesystem::is_regular_file( filename2 ) ||
                     std::filesystem::is_symlink( filename2 ) )
                {
                    files_to_convert.push_back( filename2.path().string() );
                }
            }
        }
        else if (
            std::filesystem::is_regular_file( filename ) ||
            std::filesystem::is_symlink( filename ) )
        {
            files_to_convert.push_back( filename );
        }
        else
        {
            std::cerr << "Not a file or directory: " << filename << std::endl;
            return 1;
        }
    }

    bool result = true;
    for ( auto const &input_filename: files_to_convert )
    {
        std::string output_filename = input_filename;
        size_t      pos             = input_filename.rfind( '.' );
        if ( pos != std::string::npos )
        {
            output_filename = input_filename.substr( 0, pos );
        }
        output_filename += "_oiio.exr";
        
        std::cout << std::endl;

        std::cout << "Configure conversion" << std::endl
                  << "-----------------------------------" << std::endl;
        
        if ( !converter.configure( input_filename ) )
        {
            std::cerr << "Failed to configure the reader for the file: "
                      << input_filename << std::endl;
            result = false;
            continue;
        }
        
        std::cout << std::endl;

        std::cout << "Load file: " << input_filename << std::endl
                  << "-----------------------------------" << std::endl;

        
        if ( !converter.load( input_filename ) )
        {
            std::cerr << "Failed to read for the file: " << input_filename
                      << std::endl;
            result = false;
            continue;
        }
        
        std::cout << std::endl;

        std::cout << "Process conversion" << std::endl
                  << "-----------------------------------" << std::endl;
        
        if ( !converter.process() )
        {
            std::cerr << "Failed to convert the file: " << input_filename
                      << std::endl;
            result = false;
            continue;
        }
        
        std::cout << std::endl;

        std::cout << "Save to file: " << output_filename << std::endl
                  << "-----------------------------------" << std::endl;

        if ( !converter.save( output_filename ) )
        {
            std::cerr << "Failed to save the file: " << output_filename
                      << std::endl;
            result = false;
            continue;
        }
        
        std::cout << "Conversion successful" << std::endl;
    }
    return result ? 0 : 1;
}
