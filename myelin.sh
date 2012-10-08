#   python framework/deformable_histology_reconstruction_3.py \
#       --startSlice 0 \
#       --endSlice 263 \
#       --neighbourhood 1 \
#       --iterations 3 \
#       -d /dev/shm/uniform/ \
#       --outputNaming 02_02_NN2_myelin_coarse \
#       --registerSubset 02_02_NN2_myelin_outliers.csv \
#       --antsImageMetricOpt 16 \
#       --antsTransformation 0.25 \
#       --antsRegularization 1.0 1.0 \
#       --antsIterations 1000 1000 0000 0000 0000 \
#       --outputVolumePermutationOrder 0 2 1 \
#       --outputVolumeSpacing 0.01584 0.08 0.01584 \
#       --outputVolumeOrigin 0 0.08 0 \
#       --outputVolumeOrientationCode RAS
#        -i /home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_myelin_r.nii.gz \

    python framework/deformable_histology_reconstruction_3.py \
        --startSlice 0 \
        --endSlice 263 \
        --neighbourhood 1 \
        --iterations 6 \
        -d /dev/shm/uniform/ \
        --outputNaming 02_02_NN2_myelin_coarse \
        --startFromIteration 3 \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000 1000 1000 1000 0000 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.08 0 \
        --outputVolumeOrientationCode RAS
    
    python framework/deformable_histology_reconstruction_3.py \
        --startSlice 0 \
        --startSlice 0 \
        --endSlice 263 \
        --neighbourhood 1 \
        --iterations 9 \
        -d /dev/shm/uniform/ \
        --outputNaming 02_02_NN2_myelin_coarse \
        --startFromIteration 6 \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1 0 0 0 1000 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.08 0 \
        --outputVolumeOrientationCode RAS
