mkdir -p /dev/shm/uniform/

#  python framework/deformable_histology_reconstruction_3.py \
#      -i /home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_nissl_r.nii.gz \
#      --weightsFile processing/02_02_NN2_weights.csv \
#      --startSlice 0 \
#      --endSlice 263 \
#      --neighbourhood 1 \
#      --iterations 6 \
#      -d /dev/shm/uniform/ \
#      --outputNaming testing_weights_image \
#      --antsImageMetricOpt 16 \
#      --antsTransformation 0.05 \
#      --antsRegularization 1.0 1.0 \
#      --antsIterations 1000x1000x1000x1000x0000 \
#      --outputVolumePermutationOrder 0 2 1 \
#      --outputVolumeSpacing 0.01584 0.08 0.01584 \
#      --outputVolumeOrigin 0 0.04 0 \
#      --outputVolumeOrientationCode RAS
    
#  python framework/deformable_histology_reconstruction_3.py \
#      -i /home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_nissl_mask.nii.gz \
#      --weightsFile processing/02_02_NN2_weights.csv \
#      --startSlice 0 \
#      --startSlice 0 \
#      --endSlice 263 \
#      --neighbourhood 1 \
#      --iterations 6 \
#      -d /dev/shm/uniform/ \
#      --outputNaming testing_weights_masks \
#      --antsImageMetricOpt 16 \
#      --antsTransformation 0.05 \
#      --antsRegularization 1.0 1.0 \
#      --antsIterations 1000x1000x1000x1000x0000 \
#      --outputVolumePermutationOrder 0 2 1 \
#      --outputVolumeSpacing 0.01584 0.08 0.01584 \
#      --outputVolumeOrigin 0 0.04 0 \
#      --outputVolumeOrientationCode RAS
