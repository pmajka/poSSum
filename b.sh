python deformable_histology_reconstruction_2.py \
    --startSlice 0 \
    --endSlice 263 \
    --neighbourhood 1 \
    --iterations 10 \
    -d /dev/shm/uniform/ \
    --antsImageMetric CC \
    --antsImageMetricOpt 8 \
    --antsTransformation 0.15 \
    --antsRegularization 1.0 1.0 \
    --antsIterations 1000 1000 1000 1000 0000 \
    --outputVolumePermutationOrder 0 2 1 \
    --outputVolumeSpacing 0.01584 0.08 0.01584 \
    --outputVolumeOrientationCode RAS
#    --antsIterations 1000 1000 1000 1000 1000 \
#    --outputVolumePermutationOrder 0 2 1 \
#    --outputVolumeSpacing 0.0316492 0.08 0.0316492 \
#    --outputVolumeSpacing 0.0339 0.04 0.0339 \
