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


Requirements
------------

The framework requires a several depe

In order to make the poSSum framework working, several dependencies has to be
satisfied. Below one can find the list of dependencies with a brief instuction
on installing the individual dependencies.


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

  0. Install the packages required to install ITK. Check ITK website for
     details.

  1. Download the InsightToolkit 4.3.1: 
     >> wget http://sourceforge.net/projects/itk/files/itk/4.3/InsightToolkit-4.3.1.tar.gz/download -O InsightToolkit-4.3.1.tar.gz

     and unzip the file:
     >> tar -xvvzf InsightToolkit-4.3.1.tar.gz

  2. Run cmake or ccmake and provide compilation settings. Make sure that the
     listed parameters are set as shown below. Basically this build the itk with a python wrappers and support for
     different types of RGB images which are not included by default.

     Follow the instructions from http://www.itk.org/Wiki/ITK/Python_Wrapping
     to compile itk with python wrapping.

  3. Make the build:
     >>> make.

     Please note that the build process usually takes a long time (a couple of
     hours) to complete. It is a good idea to leave the compilation as a
     overnight task and be patient and not to irritate if something goes wrong
     (as it surely will).


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
as well as 2the ItkSnap.


Ubuntu packages
---------------

  1. NumpPy, SciPy and Sphinx packages: Issue the following command to install
     the required Python packages.
    ````$sudo apt-get install python-numpy python-scipy python-sphinx````

  3. ImageMagick
    ````$sudo apt-get install imagemagick````


Python modules
--------------
    ````sudo easy_install networkx````
