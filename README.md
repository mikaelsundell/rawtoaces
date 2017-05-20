# RAW to ACES Utility

## Table of Contents
1. [Introduction](#introduction)
2. [Package Contents](#package-contents)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Known Issues](#known-issues)
6. [License](#license)

## Introduction
The RAW to ACES Utility or `rawtoaces`, is a software package that converts digital camera RAW file to ACES container files containing image data encoded according the the Academy Color Encoding Specification (ACES) as specified in SMPTE 2065-1.  This is accomplished through one of two methods.

1. CameraRAW RGB data (generated by libraw) is converted to ACES by calculating an Input Device Transform (IDT) based on the camera's sensitivity and a light source.

2. CameraRAW RGB data (generated by libraw) is converted to ACES by calculating and RGB to XYZ matrix using information included in `libraw` and metadata found in the RAW file.

The output image complies with the ACES Container specification (*SMPTE S2065-4*).

## Package Contents

The source code contains the following:

* [`cmake/`](./cmake) - CMake modules for locating dependencies (e.g.,  `libraw `)
* [`config/`](./config) - CMake configuration files
* [`data/`](./data) - Data files containing camera sensitivity, light source, color matching function and 190 training patch data
* [`lib/`](./lib) - IDT and math libraries
* [`src/`](./src) - AcesRender wrapper library and C++ header file containing `rawtoaces` usage information
* [`test/`](./test) - Sample testing materials such as a ".NEF" RAW image and a camera spectral sensitivity data file
* [`main.cpp`](main.cpp) - C++ source code file for call routines to process images

## Prerequisites

###### CMake

CMake can be downloaded directly from [https://cmake.org/]() and/or installed using one of the commands below.

* Ubuntu

	```sh
	$ sudo apt-get install cmake
	```

* Redhat

	```sh
	$ yum install cmake
	```

* OS X

	Install homebrew if not already installed
	
	```sh
	$ ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
	```
	
	Install cmake
	
	```sh
	$ brew install cmake
	```

###### IlmBase

The rawtoaces depends on an essential part of IlmBase software package, which can be downloaded from [http://www.openexr.com]() and/or installed using one of the commands below.

* Ubuntu

	```sh
	$ sudo apt-get install libilmbase-dev
	```

* Redhat

	```sh
	$ yum install ilmbase-devel
	```

* OS X

	Install homebrew if not already installed
	
	```sh
	$ ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
	```
	
	Install ilmBase
	
	```sh
	$ brew install ilmBase
	```
	
###### ACES Container 

ACES Container is the reference implementation for a file writer intended to be used with the Academy Color Encoding System (ACES). `rawtoaces` relies on it to produce images that comply with the ACES container specification (SMPTE S2065-4). LibRaw can be downloaded from [https://github.com/ampas/aces_container]() or installed using one of the commands below.

* Ubuntu / Redhat / OS X

	__NOTE : During the beta period please use the build of ACES container specified below__
	
	Install aces-container
	
	```sh
	git clone https://github.com/miaoqi/aces_container.git
	cd aces_container
	git checkout windowBuildSupport

	mkdir build && cd build
	cmake ..
	make
	sudo make install	
	```

###### LibRaw

LibRaw is the library that obtains RAW files from digital cameras. It handles image pre-processing for rawtoaces. LibRaw can be downloaded from [http://www.libraw.org/download]() or installed using one of the commands below.

* Ubuntu

	```sh
	$ sudo apt-get install libraw-dev
	```

* Redhat

	```sh
	$ yum install libraw1394-devel
	```

* OS X

	Install homebrew if not already installed
	
	```sh
	$ ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
	```
	
	Install `LibRaw`
	
	```sh
	$ brew install libraw
	```

###### Boost

Boost has multiple C++ libraries that support tasks related to linear algebra, multithreading, image processing, unit testing, etc. It handles data loading an unit-test for rawtoaces. Boost can be downloaded from [http://www.boost.org/]() or installed using one of the commands below.

* Ubuntu

	```sh
	$ sudo apt-get install libboost-all-dev
	```

* Redhat

	```sh
	$ yum install boost-devel
	```

* OS X

	Install homebrew if not already installed
	
	```sh
	$ ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
	```
	
	Install `boost`
	
	```sh
	$ brew install boost
	```

###### Ceres Solver

Ceres Solver is an open source library for solving Non-linear Least Squares problems with bounds constraints and unconstrained optimization problems. It processes non-linear regression for rawtoaces. Ceres Solver can be downloaded from [http://ceres-solver.org/]() or installed using one of the commands below.

* Linux (e.g. Ubuntu)

	Install `google-glog + gflags`
	
	``` sh
	sudo apt-get install libgoogle-glog-dev
	```
	
	Install `BLAS & LAPACK`
	
	``` sh
	sudo apt-get install libatlas-base-dev
	```
	
	Install `Eigen3`

	``` sh
	sudo apt-get install libeigen3-dev
	```
	
   Install `SuiteSparse and CXSparse` (*optional*)
   
   	``` sh
	sudo apt-get install libsuitesparse-dev
	sudo add-apt-repository ppa:bzindovic/suitesparse-bugfix-1319687
	sudo apt-get update
	sudo apt-get install libsuitesparse-dev
	```

	
   Build, Test and Install `Ceres`
	
	``` sh
	tar zxf ceres-solver-version#.tar.gz
	mkdir ceres-bin
	cd ceres-bin
	cmake ../ceres-solver-version#
	make -j3
	make test
	sudo make install
	```

* OS X

	Install homebrew if not already installed
	
	```sh
	$ ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"
	```
	
	Install `Ceres`
	
	```sh
	$ brew install ceres-solver --HEAD
	```
If there are errors with regard to version mis-match of *Eigen* library, please consider brew-installing required libraries first and then buiding Ceres from source (see above).

## Installation

* OS X

	Install homebrew if not already installed

	```sh
	$ ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"
	```

	Install rawtoaces

	```sh
	$ (coming soon ...)
	```

*  From Source

	From the root source directory:

	```sh
	$ mkdir build && cd build
	$ cmake ..
	$ make
	$ sudo make install
	```

	The default process will install `librawtoacesIDT.dylib` to `/usr/local/lib`, a few header files to `/usr/local/include/rawtoaces` and a number of data files into `/usr/local/include/rawtoaces/data`
	
## Usage

### Overview

`rawtoaces` uses one of three methods to convert RAW image files to ACES.

1. Camera spectral sensitivities and illuminant spectral power distributions
2. Camera file metadata
3. Camera data included in the `libraw` software

The preferred, and most accurate, method of converting RAW image files to ACES is to use camera spectral sensitivities and illuminant spectral power distributions, if available.  If spectral sensitivity data is available for the camera, `rawtoaces` uses the method described in Academy document [P-2013-001](http://j.mp/P-2013-001).

While preferred, camera spectral sensitivity data is not commonly known by a general user. When that is the case, `rawtoaces` can use either the metadata embedded in the camera file or camera data included in `libraw` to approximate a conversion to ACES.

### Help message

The help message with a description of all command line options can be obtained by typing the following command.

	$ rawtoaces --help
	rawtoaces - convert RAW digital camera files to ACES

	Usage:
	  rawtoaces file ...
	  rawtoaces [options] file
	  rawtoaces --help
	  rawtoaces --version
	
	IDT options:
	  --help                  Show this screen
	  --version               Show version
	  --wb-method [0-4] [str] White balance factor calculation method
	                            0=Calculate white balance from camera spec sens. Optional 
	                            string may be included to specify adopted white. 
	                            1=Use file metadata for white balance
	                            2=Average the whole image for white balance
	                            3=Average a grey box for white balance <x y w h>
	                            4=Use custom white balance  <r g b g>
	                            (default = 0)
	  --mat-method [0-2]      IDT matrix calculation method
	                            0=Calculate matrix from camera spec sens
	                            1=Use file metadata color matrix
	                            2=Use adobe coeffs
	                            (default = 0)
	  --ss-path <path>        Specify the path to camera sensitivity data
	                            (default = /usr/local/include/RAWTOACES/data/camera)
	  --exp-comp float        Set exposure compensation factor (default = 1.0)
	
	Raw conversion options:
	  -c float                Set adjust maximum threshold (default = 0.75)
	  -C <r b>                Correct chromatic aberration
	  -P <file>               Fix the dead pixels listed in this file
	  -K <file>               Subtract dark frame (16-bit raw PGM)
	  -k <num>                Set the darkness level
	  -S <num>                Set the saturation level
	  -n <num>                Set threshold for wavelet denoising
	  -H [0-9]                Highlight mode (0=clip, 1=unclip, 2=blend, 3+=rebuild) (default = 2)
	  -t [0-7]                Flip image (0=none, 3=180, 5=90CCW, 6=90CW)
	  -j                      Don't stretch or rotate raw pixels
	  -W                      Don't automatically brighten the image
	  -b <num>                Adjust brightness (default = 1.0)
	  -q [0-3]                Set the interpolation quality
	  -h                      Half-size color image (twice as fast as "-q 0")
	  -f                      Interpolate RGGB as four colors
	  -m <num>                Apply a 3x3 median filter to R-G and B-G
	  -s [0..N-1]             Select one raw image from input file
	  -G                      Use green_matching() filter
	  -B <x y w h>            Use cropbox
	
	Benchmarking options:
	  -v                      Verbose: print progress messages (repeated -v will add verbosity)
	  -F                      Use FILE I/O instead of streambuf API
	  -d                      Detailed timing report
	  -E                      Use mmap()-ed buffer instead of plain FILE I/O
	  
### RAW conversion options

In most cases the default values for all "RAW conversion options" should be sufficient.  Please see the help menu for details of the RAW conversion options.

### Conversion using spectral sensitivities

If spectral sensitivity data for your camera is included with `rawtoaces` then the following command will convert your RAW file to ACES using that information.

	$ rawtoaces input.raw
	
This command is equivalent to :
	
	$ rawtoaces --wb-method 0 --mat-method 0 input.raw
	
This is the preferred method as camera white balance gain factors and the RGB to ACES conversion matrix will be calculated using the spectral sensitivity data from your camera. This provides the most accurate conversion to ACES. 

By default, `rawtoaces` will determine the adopted white by finding the set of white balance gain factors calculated from spectral sensitivities closest to the "As Shot" (aka Camera Multiplier) white balance gain factors included in the RAW file metadata.  This default behavior can be overridden by including the desired adopted white name after white balance method.  The following example will use the white balance gain factors calculated from spectral sensitivities for D55. 

	$ rawtoaces --wb-method 0 D55 --mat-method 0 input.raw

If you have spectral sensitivity data for your camera but it is not included with `rawtoaces` you may place that data in `/usr/local/include/RAWTOACES/data/camera` or use the `--ss-path` option to point `rawtoaces` to the path of data.

An example of the use of the --ss-path option would be 

	$ rawtoaces --ss-path /path/to/my/ss/data/ input.raw

#### Camera spectral sensitivity data format

Include basic information on the data format here

### Conversion using camera file metadata

In lieu of spectral sensitivity data, camera metadata can be used to convert RAW files to ACES.  This includes the camera multiplier white balance gains and any RGB to XYZ matrix included.  The RGB to XYZ matrix included in metadata will be used to calculate the final RGB to ACES matrix used for conversion.  The accuracy of this method is dependent on the camera manufacturer building writing correct metadata into their RAW files.

The following commands will convert RAW to ACES using the camera file metadata for both white balance and the RGB to XYZ matrix.

	$ rawtoaces --wb-method 1 --mat-method 1 input.raw
	
### Conversion using camera data included in libraw

`libraw` includes matrices for a wide range of cameras which may provide a reasonable basis for conversion from RGB to ACES.  These matrices were calculated by Adobe and are often referred to as the Adobe coefficients. To use these built in matrices the following command may be used.

	$ rawtoaces --mat-method 2
	
`libraw` also provides a few other methods for calculating white balance, including averaging the entire image, averaging a specified box within the image, or explicitly specifying the white balance gain factors to be used.  These options can be utilized by using `--wb-method [2-4]` as desired.

## Known Issues

For a lise of currently known issues see the [issues list](https://github.com/ampas/rawtoaces/issues) in github.  Please add any issue found to the github list.


## License

__For 3rd party license details see [LICENSES.md](LICENSES.md)__

The RAW to ACES Utility Reference Implementation is provided by the Academy under the following terms and conditions:

Copyright © 2017 Academy of Motion Picture Arts and Sciences ("A.M.P.A.S."). Portions contributed by others as indicated. All rights reserved.

A worldwide, royalty-free, non-exclusive right to copy, modify, create derivatives, and use, in source and binary forms, is hereby granted, subject to acceptance of this license. Performance of any of the aforementioned acts indicates acceptance to be bound by the following terms and conditions:

Copies of source code, in whole or in part, must retain the above copyright notice, this list of conditions and the Disclaimer of Warranty.

Use in binary form must retain the above copyright notice, this list of conditions and the Disclaimer of Warranty in the documentation and/or other materials provided with the distribution.

Nothing in this license shall be deemed to grant any rights to trademarks, copyrights, patents, trade secrets or any other intellectual property of A.M.P.A.S. or any contributors, except as expressly stated herein.

Neither the name "A.M.P.A.S." nor the name of any other contributors to this software may be used to endorse or promote products derivative of or based on this software without express prior written permission of A.M.P.A.S. or the contributors, as appropriate.

This license shall be construed pursuant to the laws of the State of California, and any disputes related thereto shall be subject to the jurisdiction of the courts therein.

Disclaimer of Warranty: THIS SOFTWARE IS PROVIDED BY A.M.P.A.S. AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT ARE DISCLAIMED. IN NO EVENT SHALL A.M.P.A.S., OR ANY CONTRIBUTORS OR DISTRIBUTORS, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, RESITUTIONARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

WITHOUT LIMITING THE GENERALITY OF THE FOREGOING, THE ACADEMY SPECIFICALLY DISCLAIMS ANY REPRESENTATIONS OR WARRANTIES WHATSOEVER RELATED TO PATENT OR OTHER INTELLECTUAL PROPERTY RIGHTS IN THE RAW TO ACES UTILITY REFERENCE IMPLEMENTATION, OR APPLICATIONS THEREOF, HELD BY PARTIES OTHER THAN A.M.P.A.S., WHETHER DISCLOSED OR UNDISCLOSED.
