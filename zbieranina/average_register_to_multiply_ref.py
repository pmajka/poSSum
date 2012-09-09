#!/usr/bin/python

import numpy as np
from scipy.stats import norm
import sys, os

# types of arguments to build: 
#  - bool argument 
#  - list of files argument (no prefix)
#  - list of files argument (with custom prefix)
# - generic argument with prefix, content and suffix
# - single filename argument

# Serialization: joint the filenames

ANTS_GET_TRANSFORM_CMD= \
"""%(averageString)s; ANTS 2 -m %(metricName)s[%(fixed)s,%(moving)s,%(weight)f,%(metricParam)d] \
          -t SyN[%(transformationIntensity)f] \
          -r Gauss[%(regularization)s] \
          -i 5000x5000x5000x5000x5000x5000x5000 \
          -o %(outPrefix)s/%(fixedIdx)04d \
          --number-of-affine-iterations 0 \
          --MI-option 32x32000 \
          --use-Histogram-Matching \
          --affine-metric-type MI \
          --rigid-affine true #0001_REGISTER"""

ANTS_RESLICE = \
"""WarpImageMultiTransform 2 \
   %(movingImage)s %(outputImage)s \
   -R %(referenceImage)s %(defomableWarpsList)s %(affineWarp)s #0005_RESLICE_SLICES"""

ANTS_AVERAGE = \
""" c2d  %(inputToAverage)s -mean -type uchar -o 03_process_slices/w%(outputAverage)04d.png """

dirdic = {}
dirdic['src_slices'] = '02_source_slices'
dirdic['prc_slices'] = '03_process_slices'
dirdic['transf']     = '04_transformations'
dirdic['resliced']   = '05_resliced_grayscale'

def gauss(x, sigma, mu):
        return ((2*np.pi*sigma)**.5) * np.e ** (-(x-mu)**2/(2 * sigma**2))

eps=int(sys.argv[4])
start=0
end=260
prefix = 'iteration_%04d' % int(sys.argv[6])

mu, sigma = 0, float(eps/2.) # mean and standard deviation
metricName = str(sys.argv[1])
metricParam  = int(sys.argv[2])

weights = {}

for i in range(start, end +1):
    for j in range(i - eps, i + eps+1):
        if j!=i:
            #weights[(i,j)] = gauss(j-i, sigma, 0)/gauss(0, sigma, 0)
            weights[(i,j)] = (eps+1)-abs(i-j)

for i in range(start, end +1):
    wcmd = {}
    im_to_av = " "
    for j in range(i -eps, i + eps+1):
        if j >= start and j <= end and i!=j:
            im_to_av +=  os.path.join(prefix,dirdic['prc_slices'],"%04d.png " % j)
    wcmd['averageString'] = \
            "c2d " + im_to_av + "-mean -type uchar -o "+ os.path.join(prefix,dirdic['prc_slices']  +"/w%04d.png" % i)
    
    wcmd['transformationIntensity'] = float(sys.argv[5])
    wcmd['regularization'] = sys.argv[3]
    wcmd['outPrefix'] = os.path.join(prefix, dirdic['transf'])
    
    wcmd['metricName']  = metricName
    wcmd['metricParam'] = metricParam
    wcmd['weight'] = 1 #weights[(i,j)]
    wcmd['fixed']  = os.path.join(prefix, dirdic['prc_slices'], "w%04d.png" % i)
    wcmd['moving'] = os.path.join(prefix, dirdic['prc_slices'], "%04d.png" % i)
    
    wcmd['fixedIdx'] =  i
    wcmd['movingIdx'] = i
    print ANTS_GET_TRANSFORM_CMD % wcmd

for i in range(start, end +1):
    cmdD = {}
    cmdD['movingImage']    =  os.path.join(prefix, dirdic['src_slices'], "%04d.png" % i)
    cmdD['outputImage']    =  os.path.join(prefix, dirdic['resliced'],   "%04d.nii.gz" % i)
    cmdD['referenceImage'] =  os.path.join(prefix, dirdic['src_slices'], "%04d.png" % i )
    cmdD['defomableWarpsList'] = os.path.join(prefix, dirdic['transf'], '%04dWarp.nii.gz'  % i)
    #cmdD['defomableWarpsList'] = ''
    #cmdD['affineWarp'] = "_f%04dAffine.txt" % i
    cmdD['affineWarp'] = ""
    print ANTS_RESLICE % cmdD
