.. -*- rest -*-
.. vim:syntax=rest


Nonlinear volumetric reconstruction framework
========================================


Overwiew
========

The poSSum framework is a set of scripts and workflows which purpose it to
reconstruct the volumetric datasets based on series of serial sections of
different modality and quality.


Installation
============

Below one can find the description of the dependencies.
For the exact installation steps, check the <<section>> section.

Requirements and dependencies
-----------------------------

In order to make the poSSum framework working, several dependencies has to be
satisfied. Below one can find the list of dependencies with a brief instuction
on installing the individual dependencies.


Operating system
----------------

Installation was tested using the Ubuntu 12.04 server, amd64 version::

    http://releases.ubuntu.com/12.04/ubuntu-12.04.4-server-amd64.iso

The system was instatlled with the default settings.
Only the system locale were altered.


InsightToolkit 4.3.1
--------------------

The poSSum framework required the InsightToolkit (ITK, http://www.itk.org/)
image processing library. PosSSum was created and tested with ITK 4.3.1
(http://sourceforge.net/projects/itk/files/itk/4.3/InsightToolkit-4.3.1.tar.gz/download)
thus this ITK version is reccomended. Due to rapid developement of the ITK
framework it is not guaranteed (although qute likely) that the poSSum will work
newer and some of the older ITK versions.

In order to install the InsightToolkit one has to perform the steps described on
the ITK website: 

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
     the compilation as a overnight task and be patient and not to
     irritate if something goes wrong (as it surely will).


Advanced Normalization Tools
----------------------------

The Advanced Normalization Tools (or shortly ANTS) is an image normalization and
registration framework which provides reliable and algorithms for image
registration. ANTS binaries may be downloaded from the ANTS website: ..
- Advanced Normalizatin Tools (ANTS, http://stnava.github.io/ANTs/),
The posSSum framework was tested with ANTS v3 as well as ANTS v4.


Convert 3D and ItkSnap tool
---------------------------
Convert 3D (cruical) and ItkSnap (not criucal but extremely usefull).
Visit the http://www.itksnap.org/ in order to get both, the Convert 3D
as well as the ItkSnap.


Exact installation procedure
======================================


Install the system
------------------------------------

Download the system installation disk image::

    http://releases.ubuntu.com/12.04/ubuntu-12.04.4-server-amd64.iso

And install the system with the default settings.


Install the necessacy packages
------------------------------------

  1. NumpPy, SciPy and Sphinx packages::

     sudo apt-get install python-numpy python-scipy python-sphinx python-setuptools

     And the required python modules::

     sudo easy_install -U config
     sudo easy_install -U networkx

  2. Install the ImageMagick package::
     
     sudo apt-get install imagemagick

  3. Install packages required for the Itk installation::

     sudo apt-get install build-essential ccmake cmake-curses-gui


Install InsightToolkit
--------------------------

As described below::

     cd 
     wget http://sourceforge.net/projects/itk/files/itk/4.3/InsightToolkit-4.3.1.tar.gz/download -O InsightToolkit-4.3.1.tar.gz
     tar -xvvzf InsightToolkit-4.3.1.tar.gz
     mkdir -p InsightToolkit-4.3.1-build && cd InsightToolkit-4.3.1-build
     cmake ../InsightToolkit-4.3.1

Setup the cmake so the python wrapping will be installed and make the build::

     make


Install ANTS, Convert 3d and setup the paths
----------------------------------------------

As described below::

    wget http://heanet.dl.sourceforge.net/project/advants/ANTS/ANTS_Latest/ANTs-1.9.v4-Linux.tar.gz -O ANTs-1.9.v4-Linux.tar.gz
    wget http://skylink.dl.sourceforge.net/project/c3d/c3d/Nightly/c3d-nightly-Linux-x86_64.tar.gz -O c3d-nightly-Linux-x86_64.tar.gz
    tar -xvvzf ANTs-1.9.v4-Linux.tar.gz
    tar -xvvzf c3d-nightly-Linux-x86_64.tar.gz

    find InsightToolkit-4.3.1-build/ -name "*.pth" | xargs cat
    export PYTHONPATH=${PYTHONPATH}:/home/test/InsightToolkit-4.3.1-build/Wrapping/Generators/Python
    export PYTHONPATH=${PYTHONPATH}:InsightToolkit-4.3.1-build/lib/
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:InsightToolkit-4.3.1-build/lib/

    export PATH=$PATH:ANTs-1.9.v4-Linux/
    export PATH=$PATH:c3d-1.0.0-Linux-x86_64/

Install git so the actual framework could be downloaded::

    sudo apt-get install git-core

Starting with the fresh system installation: window 160x50.
