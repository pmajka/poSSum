python deformable_histology_reconstruction_2.py \
    --dryRun \
    --dryRun \
    --startSlice 0 \
    --endSlice 69 \
    --neighbourhood 1 \
    --iterations 10 \
    -d /home/pmajka/possum/uniform/ \
    --antsImageMetricOpt 8 \
    --antsTransformation 0.05 \
    --antsRegularization 1.0 1.0 \
    --antsIterations 1000 1000 1000 1000 1000 \
    --outputVolumePermutationOrder 0 2 1 \
    --outputVolumeSpacing 0.033 0.1 0.033 \
    --outputVolumeOrientationCode RAS
#    --antsIterations 1000 1000 1000 1000 1000 \
#    --outputVolumePermutationOrder 0 2 1 \
