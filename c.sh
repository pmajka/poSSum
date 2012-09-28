python deformable_histology_reconstruction_3.py \
    --startSlice 90 \
    --endSlice 190 \
    --neighbourhood 1 \
    --iterations 10 \
    -d /dev/shm/uniform/ \
    --antsImageMetricOpt 8 \
    --antsTransformation 0.05 \
    --antsRegularization 1.0 1.0 \
    --antsIterations 1000 1000 1000 1000 1000 \
    --outputVolumePermutationOrder 0 2 1 \
    --outputVolumeSpacing 0.0316492 0.08 0.0316492 \
    --outputVolumeOrientationCode RAS
#    --antsIterations 1000 1000 1000 1000 1000 \
#    --outputVolumePermutationOrder 0 2 1 \
#    --outputVolumeSpacing 0.01584 0.08 0.01584 \
#    --outputVolumeSpacing 0.0316492 0.08 0.0316492 \
#    --outputVolumeSpacing 0.0339 0.04 0.0339 \
#    --weightsFile /home/pmajka/Dropbox/02_02_NN2_weights.csv \
