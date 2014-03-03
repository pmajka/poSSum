#!bin/bash
set -xe

# XXX Very important assumption. This script assumes that
# the spacing of the image being coregistered is 1x1mm
# and all the parameters are tuned to serve 1x1 spacing image!

python ../../deformable_histology_reconstruction.py --specimenId marmoset\
    --inputVolume 1 /home/pmajka/Downloads/other/marmoset_atlas/images/ooo.nii.gz \
    -d /dev/shm/dt1/ \
    --slicingPlane 1\
    --startSlice 0 \
    --endSlice 62 \
    --iterations 8 \
    --neighbourhood 1 \
    --outputNaming output_ \
    --antsImageMetricOpt 2 \
    --antsTransformation 0.025 \
    --antsRegularization 1 1 \
    --antsIterations 1000x1000x1000x1000x0000 \
    --planeSpacing 0.03 \
    --outputVolumePermutationOrder 0 2 1 \
    --outputVolumeSpacing 0.03 0.5 0.03 \
    --outputVolumeOrigin 0 0 0 \
    --outputVolumeOrientationCode RAS \
    --stackFinalDeformation \
    --loglevel DEBUG \
    --glyphConfiguration deformable_reconstruction_marmoset_glyphs.cfg \
    --skipTransformations 
