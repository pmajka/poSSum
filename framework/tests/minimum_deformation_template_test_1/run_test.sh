set -xe

python ../../pos_mdt_main.py \
    --jobId minimum_deformation_template_test_1 \
    --firstImageIndex 0 \
    --lastImageIndex 7 \
    --iterations 10 \
    -i ./ \
    --antsImageMetric CC \
    --antsImageMetricOpt 5 \
    --antsTransformation 0.25 \
    --antsRegularization 3 0 \
    --antsIterations 30x90x20 \
    --antsDimension 2 \
    --antsAffineIterations 10000x10000x10000x10000x10000 \
    --loglevel DEBUG \
    --settingsFile configuration.json # 2>&1 | tee > mdt_test_1.log

cp -rfv /dev/shm/minimum_deformation_template_test_1/12_transf_f/sddm0009.nii.gz test_sddm.nii.gz
cp -rfv /dev/shm/minimum_deformation_template_test_1/05_iterations/0000/21_resliced/average.nii.gz test_average.nii.gz

diff reference_sddm.nii.gz test_sddm.nii.gz > sddm_diff.txt
diff reference_average.nii.gz test_average.nii.gz > average_diff.txt
