#!bin/bash
set -xe

python ../../deformable_histology_reconstruction.py \
    --inputVolume 1 /home/pmajka/Downloads/marmoset_atlas/images/oo.nii.gz \
    -d /dev/shm/dt2/ \
    --startSlice 0 \
    --endSlice 62 \
    --iterations 2 \
    --neighbourhood 1 \
    --outputNaming output_ \
    --antsImageMetricOpt 2 \
    --antsTransformation 0.025 \
    --antsRegularization 1.0 1.0 \
    --antsIterations 1000x1000x1000x1000x0000 \
    --outputVolumePermutationOrder 0 2 1 \
    --outputVolumeSpacing 0.03 0.5 0.03 \
    --outputVolumeOrigin 0 0 0 \
    --outputVolumeOrientationCode RAS \
    --stackFinalDeformation \
    --glyphConfiguration draw_glyphs_configuration.cfg \
    --loglevel DEBUG \
    --skipTransformations
#    --skipTransformations
