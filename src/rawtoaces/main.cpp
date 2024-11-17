// Copyright Contributors to the rawtoaces project.
// SPDX-License-Identifier: Apache-2.0
// https://github.com/AcademySoftwareFoundation/rawtoaces

#include <rawtoaces/rawtoaces_util.h>

#include <filesystem>

using namespace rawtoaces;

int main( int argc, const char *argv[] )
{
    std::cout << "rawtoaces" << std::endl;
    ImageConverter converter;
    if ( !converter.parse( argc, argv ) )
    {
        return 1;
    }
    
    auto &argParse = converter.argParse();
    auto inputfilename = argParse["input-filename"].as_string();
    auto outputfilename = argParse["output-filename"].as_string();
    std::cout << "** Configure conversion" << std::endl;
    
    if (!converter.configure(inputfilename))
    {
        std::cerr << "Failed to configure the converter for the file: "
                  << inputfilename << std::endl;
        return 1;
    }
    
    std::cout << std::endl;

    std::cout << "** Load file: " << inputfilename << std::endl;

    if (!converter.load(inputfilename))
    {
        std::cerr << "Failed to read for the file: " << inputfilename
                  << std::endl;
        return 1;
    }
    
    std::cout << std::endl;

    std::cout << "** Process conversion" << std::endl;
    
    if (!converter.process())
    {
        std::cerr << "Failed to convert the file: " << inputfilename
                  << std::endl;
        return 1;
    }
    
    std::cout << std::endl;

    std::cout << "** Save to file: " << outputfilename << std::endl;

    if (!converter.save(outputfilename))
    {
        std::cerr << "Failed to save the file: " << outputfilename
                  << std::endl;
        return 1;
    }
    
    std::cout << "** Conversion successful" << std::endl;
    return 0;
}
