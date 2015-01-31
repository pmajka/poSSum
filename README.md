

poSSum volumetric reconstruction framework
===========================================================

[![Build Status](https://travis-ci.org/pmajka/poSSum.svg?branch=master)](https://travis-ci.org/pmajka/poSSum) [![Coverage Status](https://coveralls.io/repos/pmajka/poSSum/badge.png?branch=master)](https://coveralls.io/r/pmajka/poSSum?branch=master)

========
Overview
========

The poSSum framework is a set of scripts and workflows which purpose it to
reconstruct the volumetric datasets based on series of serial sections of
different modality and quality.


Preconfigured VM
================

If you would like to start using the poSSum framework immediately
without necessity of installation and configuration, you are strongly 
encouraged to download preconfigured virtual machine.

The appliance can be imported to VirtualBox software
(https://www.virtualbox.org/) which operates on multiple operating systems
including Windows, OSX and Linux. Note however, that the file
to download is a substantial one: about 2GB. Have also in mind that, although we're trying to keep the VM updated, the environment installed on th VM might be slightly behind the current develop branch of the framework. You have to update it on your own.

You can download the poSSum preconfigured virtual machine
using the link below:
http://doc.3dbar.org/possum/possum_framework_vm.ova

Should you have any problem with importing the virtual appliance,
please refer to the VirtualBox documentation:

http://docs.oracle.com/cd/E26217_01/E26796/html/qs-import-vm.html

http://www.virtualbox.org/manual/ch01.html#ovf

or other online resources, e.g:
http://www.maketecheasier.com/import-export-ova-files-in-virtualbox/

Note that all usernames and passwords (including the root passord) are: testuser
Also, please let the VM have at least 4GB of memory (8GB recommended) 
and 4CPUs (however, the more the better).



Installation
============

Below one can find the description of the dependencies.
For the exact installation steps, check the `installation procedure` section below.

Requirements and dependencies
-----------------------------

In order to make the poSSum framework working, several dependencies have to be
satisfied. Below one can find the list of dependencies with a brief instruction
on installing the individual dependencies.


Operating system
----------------

Installation was tested using the Ubuntu 12.04 server, amd64 version::

    http://releases.ubuntu.com/12.04/ubuntu-12.04.4-server-amd64.iso

The system was installed with the default settings.
Only the system locale were altered.


InsightToolkit 4.3.1
--------------------

The poSSum framework requires the InsightToolkit (ITK, http://www.itk.org/)
image processing library. PosSSum was created and tested using ITK 4.3.1
(http://sourceforge.net/projects/itk/files/itk/4.3/InsightToolkit-4.3.1.tar.gz/download)
thus this ITK version is recommended. Due to rapid development of the ITK
framework it is not guaranteed (although quite likely) that the poSSum will work
with newer as well as with some of the older ITK versions.

In order to install the InsightToolkit one has to perform the steps described on
the ITK website (http://www.itk.org/Wiki/ITK/Complete_Setup): 

  1. Install the packages required to install ITK. Check ITK website for
     details.

  2. Download the InsightToolkit 4.3.1 and unzip the file. 

  3. Run cmake or ccmake and provide compilation settings. Make sure that
     the listed parameters are set as shown below. Basically this build
     the itk with a python wrappers and support for different types of
     RGB images which are not included by default. Follow the instructions
     from http://www.itk.org/Wiki/ITK/Python_Wrapping to compile itk with
     python wrapping.

  4. Make the build. Note that the build process usually takes a long
     time (a couple of hours) to complete. It is a good idea to leave
     the compilation as a overnight task and be patient.


Advanced Normalization Tools
----------------------------

The Advanced Normalization Tools (or shortly ANTS) is an image normalization and
registration framework which provides reliable and algorithms for image
registration. ANTS binaries may be downloaded from the ANTS website: http://stnava.github.io/ANTs/,
The posSSum framework was tested with ANTS v3 as well as ANTS v4.


Convert 3D and ItkSnap tool
---------------------------

Convert 3D (crucial) and ItkSnap (not crucial but extremely useful).
Visit the http://www.itksnap.org/ in order to get both, the Convert 3D
as well as the ItkSnap.



Exact installation procedure
======================================


Install the system
------------------------------------

Download the system installation disk image::

    http://releases.ubuntu.com/12.04/ubuntu-12.04.4-server-amd64.iso

And install the system with the default settings.


Install the necessary packages
------------------------------------

NumpPy, SciPy and Sphinx packages::

    sudo apt-get install python-numpy python-scipy python-sphinx python-setuptools parallel

And the required python modules::

    sudo easy_install -U config
    sudo easy_install -U networkx
    sudo easy_install coverage

Install the ImageMagick and parallel packages::

    sudo apt-get install imagemagick parallel

Install packages required for the Itk installation::

    sudo apt-get install build-essential cmake-curses-gui


Install InsightToolkit
--------------------------

As described below::

     cd 
     wget http://sourceforge.net/projects/itk/files/itk/4.3/InsightToolkit-4.3.1.tar.gz/download -O InsightToolkit-4.3.1.tar.gz
     tar -xvvzf InsightToolkit-4.3.1.tar.gz
     mkdir -p InsightToolkit-4.3.1-build && cd InsightToolkit-4.3.1-build
     ccmake ../InsightToolkit-4.3.1

Setup the cmake so the python wrappings will be installed::

    BUILD_EXAMPLES                   OFF
    BUILD_SHARED_LIBS                ON
    BUILD_TESTING                    OFF
    CMAKE_BUILD_TYPE                 Release
    INSTALL_WRAP_ITK_COMPATIBILITY   ON
    ITKV3_COMPATIBILITY              ON
    ITK_BUILD_ALL_MODULES            ON
    ITK_USE_REVIEW                   ON 
    ITK_USE_SYSTEM_SWIG              OFF
    ITK_WRAP_DIMS                    2;3
    ITK_WRAP_DOC                     OFF
    ITK_WRAP_EXPLICIT                OFF
    ITK_WRAP_GCCXML                  ON
    ITK_WRAP_JAVA                    OFF
    ITK_WRAP_PERL                    OFF
    ITK_WRAP_PYTHON                  ON
    ITK_WRAP_RUBY                    OFF
    ITK_WRAP_SWIGINTERFACE           ON
    ITK_WRAP_TCL                     OFF
    ITK_WRAP_complex_double          ON
    ITK_WRAP_complex_float           ON
    ITK_WRAP_covariant_vector_doub   OFF
    ITK_WRAP_covariant_vector_floa   ON
    ITK_WRAP_double                  ON
    ITK_WRAP_float                   ON
    ITK_WRAP_rgb_unsigned_char       ON
    ITK_WRAP_rgb_unsigned_short      OFF
    ITK_WRAP_rgba_unsigned_char      ON
    ITK_WRAP_rgba_unsigned_short     OFF
    ITK_WRAP_signed_char             OFF
    ITK_WRAP_signed_long             OFF
    ITK_WRAP_signed_short            ON
    ITK_WRAP_unsigned_char           ON
    ITK_WRAP_unsigned_long           OFF
    ITK_WRAP_unsigned_short          ON
    ITK_WRAP_vector_double           ON
    ITK_WRAP_vector_float            ON
    SWIG_DIR                         /home/test/InsightToolkit-4.3.1-build/Wrapping/Generators/SwigInterface/swig/share/swig/2
    SWIG_EXECUTABLE                  /home/test/InsightToolkit-4.3.1-build/Wrapping/Generators/SwigInterface/swig/bin/swig

And then make the build::

     make


Install ANTS, Convert 3d and setup the paths
----------------------------------------------

As described below (provided that `/home/test/` is you home ddirectory)::


    cd
    wget http://heanet.dl.sourceforge.net/project/advants/ANTS/ANTS_Latest/ANTs-1.9.v4-Linux.tar.gz -O ANTs-1.9.v4-Linux.tar.gz
    wget http://skylink.dl.sourceforge.net/project/c3d/c3d/Nightly/c3d-nightly-Linux-x86_64.tar.gz -O c3d-nightly-Linux-x86_64.tar.gz
    tar -xvvzf ANTs-1.9.v4-Linux.tar.gz
    tar -xvvzf c3d-nightly-Linux-x86_64.tar.gz

    find InsightToolkit-4.3.1-build/ -name "*.pth" | xargs cat
    export PYTHONPATH=${PYTHONPATH}:/home/test/InsightToolkit-4.3.1-build/Wrapping/Generators/Python
    export PYTHONPATH=${PYTHONPATH}:/home/test/InsightToolkit-4.3.1-build/lib/
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/test/InsightToolkit-4.3.1-build/lib/

    export PATH=$PATH:/home/test/ANTs-1.9.v4-Linux/bin/
    export PATH=$PATH:/home/test/c3d-1.0.0-Linux-x86_64/bin/

Install git so the actual framework could be downloaded::

    sudo apt-get install git-core

Then simply clone the repository and set up the environmental variables::

    cd && git clone https://github.com/pmajka/poSSum.git
    cd poSSum && source setenv.sh 
    
The framework should be ready to use.
    
Installation screencast
-------------------------

You may also want to check out the screencast showing how to install the framework ::

    http://youtu.be/j89KxyluiCM

<!---
Starting with the fresh system installation: window 160x50.
-->
