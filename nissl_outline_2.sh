mkdir -p /dev/shm/uniform2/
#   c3d \
#       /home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_nissl_r.nii.gz \
#       -scale -1 -shift 255 \
#       /home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_nissl_mask.nii.gz \
#       -times \
#       -scale -1 -shift 255 \
#       -type uchar -o 02_02_NN2_final_nissl_masked.nii.gz

   python framework/deformable_histology_reconstruction_3.py \
       -i mask.nii.gz \
       --startSlice 100 \
       --endSlice 200 \
       --iterations 5 \
       --neighbourhood 1 \
       -d /dev/shm/uniform2/ \
       --outputNaming removing_outliers \
       --antsImageMetricOpt 16 \
       --antsTransformation 0.10 \
       --antsRegularization 1.0 1.0 \
       --antsIterations 1000x1000x1000x0000x0000 \
       --outputVolumePermutationOrder 0 2 1 \
       --outputVolumeSpacing 0.01584 0.08 0.01584 \
       --outputVolumeOrigin 0 0.04 0 \
       --outputVolumeOrientationCode RAS

#      python framework/deformable_histology_reconstruction_3.py \
#          -i 02_02_NN2_final_nissl_masked.nii.gz \
#          --startSlice 150 \
#          --endSlice 200 \
#          --iterations 5 \
#          --neighbourhood 1 \
#          --registerSubset processing/02_02_NN2_outliers.csv \
#          -d /dev/shm/uniform/ \
#          --outputNaming removing_outliers \
#          --antsImageMetricOpt 16 \
#          --antsTransformation 0.10 \
#          --antsRegularization 1.0 1.0 \
#          --antsIterations 1000x1000x1000x0x0 \
#          --outputVolumePermutationOrder 0 2 1 \
#          --outputVolumeSpacing 0.01584 0.08 0.01584 \
#          --outputVolumeOrigin 0 0.04 0 \
#          --outputVolumeOrientationCode RAS

#  python framework/deformable_histology_reconstruction_3.py \
#      -i 02_02_NN2_final_nissl_masked.nii.gz \
#      --outlineVolume /home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_nissl_mask.nii.gz \
#       --startSlice 0 \
#       --endSlice 263 \
#       --neighbourhood 1 \
#       --startFromIteration 8 \
#       --iterations 10 \
#       -d /dev/shm/uniform2/ \
#       --outputNaming DG-dilated-rs \
#       --antsImageMetricOpt 16 \
#       --antsTransformation 0.05 \
#       --antsRegularization 1.0 1.0 \
#       --antsIterations 1000x1000x1000x1000x1000 \
#       --outputVolumePermutationOrder 0 2 1 \
#       --outputVolumeSpacing 0.01584 0.08 0.01584 \
#       --outputVolumeOrigin 0 0.04 0 \
#       --outputVolumeOrientationCode RAS
