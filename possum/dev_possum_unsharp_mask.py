#!/usr/bin/python

import itk
from sys import argv
from optparse import OptionParser, OptionGroup


class unsharpMaskImageFilter():
    def __init__(self, InputImage, sigmaArray, ammount):
        """
        Simple workflow implementing unsharp masking.
        """
        im = itk.image(InputImage)
        InType = itk.class_(im)

        self.gaussianSmooth = itk.SmoothingRecursiveGaussianImageFilter[InType,InType].New(\
                InputImage,
                SigmaArray = sigmaArray)

        self.substract = itk.SubtractImageFilter[InType,InType,InType].New(\
                Input1 = InputImage,
                Input2 = self.gaussianSmooth.GetOutput())

        self.shiftScale = itk.ShiftScaleImageFilter[InType,InType].New(\
                Input = self.substract.GetOutput(),
                Scale = ammount,
                Shift = 0)

        self.addFilter = itk.AddImageFilter[InType,InType,InType].New(\
                Input1 = self.shiftScale.GetOutput(),
                Input2 = InputImage)

    def GetOutput(self):
        self.addFilter.Update()
        return self.addFilter.GetOutput()


def launchFilterMultichannel(options, args):
    """
    Multichannel unsharp mask workflow. This is acctually grayscale workflow
    applied for each separate color channel. This function is limited only for
    3D images, it will not work for
    """

    # Define image dimensions, pixels and image type
    imageDim = options.imageDim
    MultichannelPixelType = itk.RGBPixel
    ScalarPixelType = itk.UC

    ScalarImageType       = itk.Image[ScalarPixelType,imageDim]
    MCImageType = itk.Image.RGBUC3

    # Read image (define reader and writer)
    reader = itk.ImageFileReader.IRGBUC3.New(FileName = options.inputFile)
    writer = itk.ImageFileWriter[MCImageType].New()

    # Split multichannel image apart into channel
    extractR = itk.VectorIndexSelectionCastImageFilter[MCImageType,ScalarImageType].New(\
            Input = reader.GetOutput(),
            Index = 0)

    extractG = itk.VectorIndexSelectionCastImageFilter[MCImageType,ScalarImageType].New(\
            Input = reader.GetOutput(),
            Index = 1)

    extractB = itk.VectorIndexSelectionCastImageFilter[MCImageType,ScalarImageType].New(\
            Input = reader.GetOutput(),
            Index = 2)

    # Apply unsharp mask to each channel separately
    unsharpR = unsharpMaskImageFilter(extractR.GetOutput(),
                           sigmaArray = options.sigmaArray,
                           ammount = options.unsharpAmmount)

    unsharpG = unsharpMaskImageFilter(extractG.GetOutput(),
                           sigmaArray = options.sigmaArray,
                           ammount = options.unsharpAmmount)

    unsharpB = unsharpMaskImageFilter(extractB.GetOutput(),
                           sigmaArray = options.sigmaArray,
                           ammount = options.unsharpAmmount)

    # Merge image back into multichannel image.
    composeFilter = itk.ComposeImageFilter[ScalarImageType,MCImageType].New(\
            Input1 = unsharpR.GetOutput(),
            Input2 = unsharpG.GetOutput(),
            Input3 = unsharpB.GetOutput())

    # And then write it
    writer = itk.ImageFileWriter[MCImageType].New(composeFilter, FileName = options.outputFile)
    writer.Update();

def launchFilterGrayscale(options, args):
    """
    Grayscale unsharp mask workflow
    """

    # Define image dimensions, pixels and image type
    imageDim = options.imageDim

    InputPixelType = itk.F
    OutputPixelType = itk.F

    InputImageType = itk.Image[InputPixelType, imageDim]
    OutputImageType = itk.Image[OutputPixelType, imageDim]

    WritePixelType = itk.UC
    WriteImageType = itk.Image[WritePixelType, imageDim]

    # Read the input image, process it and then save
    reader = itk.ImageFileReader[InputImageType].New(FileName = options.inputFile)

    unsharp = unsharpMaskImageFilter(reader.GetOutput(),
                           sigmaArray = options.sigmaArray,
                           ammount = options.unsharpAmmount)

    # Rescale image intensity to match 16bit grayscale image, then save
    rescaler = itk.RescaleIntensityImageFilter[OutputImageType,WriteImageType].New(unsharp.GetOutput(), OutputMinimum=0, OutputMaximum=255)
    writer = itk.ImageFileWriter[WriteImageType].New(rescaler, FileName = options.outputFile)
    writer.Update();

def launchFilter(options, args):
    """
    In this filter only 3D unsharp masking is possible. If you want to apply
    unsharp mask to a 2D image use e.g. ImageMagic instead as it would be easier
    and faster.
    """
    if options.multichannelWorkflow:
        launchFilterMultichannel(options, args)
    else:
        launchFilterGrayscale(options, args)

def parseArgs():
    usage = "python unsharpMaskFilter.py -i b.nii.gz -o c.nii.gz --sigmaArray 0.05 0.05 0.05 --unsharpAmmount 4"

    parser = OptionParser(usage = usage)
    parser.add_option('--imageDim', '-d', dest='imageDim', type='int',
            default=3, help='')
    parser.add_option('--outputFile', '-o', dest='outputFile', type='str',
            default=None, help='')
    parser.add_option('--inputFile', '-i', dest='inputFile', type='str',
            default=None, help='')
    parser.add_option('--multichannelWorkflow', default=False,
            dest='multichannelWorkflow', action='store_const', const=True,
            help='Indicate that provided image is a RGB image and the RGB workflow has to be used.')
    parser.add_option('--sigmaArray', default=[1,1,1],
            type='float', nargs=3, dest='sigmaArray',
            help='Sigma array used during gaussian smoothing')
    parser.add_option('--unsharpAmmount', default=0.5,
            type='float', dest='unsharpAmmount',
            help='Sigma array used during gaussian smoothing')

    (options, args) = parser.parse_args()
    if (not options.outputFile) or (not options.inputFile):
        parser.print_help()
        exit(1)
    return (options, args)

if __name__ == '__main__':
    options, args = parseArgs()
    launchFilter(options,args)
