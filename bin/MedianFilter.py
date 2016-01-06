#!/usr/local/python/2.7.8-gcc/bin/python
# -*- coding: utf-8 -*

import itk
from optparse import OptionParser, OptionGroup

#itk.auto_progress(2)


def launchFilter(options, args):
  imageDim = options.imageDim

  InputPixelType = itk.F
  OutputPixelType = itk.F

  InputImageType = itk.Image[InputPixelType, imageDim]
  OutputImageType = itk.Image[OutputPixelType, imageDim]

  WritePixelType = itk.US
  WriteImageType = itk.Image[WritePixelType, imageDim]

  reader = itk.ImageFileReader[InputImageType].New( FileName = options.inputFile)

  filter = itk.MedianImageFilter[InputImageType, OutputImageType].New(\
                  reader,
                  Radius = options.radius)
  filter.Update();

  rescaler = itk.RescaleIntensityImageFilter[OutputImageType, WriteImageType].New( filter, OutputMinimum=0, OutputMaximum=255)
  writer = itk.ImageFileWriter[WriteImageType].New( rescaler, FileName = options.outputFile )
  writer.Update();

def parseArgs():
    parser = OptionParser()
    parser.add_option('--radius', '-r', nargs=3,
                      type='int', dest='radius', default=[2, 0, 2],
                      help='Median filter radius')
    parser.add_option('--imageDim', '-d', dest='imageDim', type='int',
            default=3, help='')
    parser.add_option('--outputFile', '-o', dest='outputFile', type='str',
            default=None, help='')
    parser.add_option('--inputFile', '-i', dest='inputFile', type='str',
            default=None, help='')

    (options, args) = parser.parse_args()
    if (not options.outputFile) or (not options.inputFile):
        parser.print_help()
        exit(1)
    return (options, args)

if __name__ == '__main__':
    options, args = parseArgs()
    launchFilter(options,args)
