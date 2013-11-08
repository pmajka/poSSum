set -x

WORK_DIR=/dev/shm/mdt_test_rectangle/

mu=128
sigma=8
n=100
image_size=256

function generate_test_images {
python << END
import numpy as np

mu, sigma, n = $mu, $sigma, $n
samples = np.random.normal(mu, sigma, size=n)

for i in range(n):
    v=samples[i]
    print "convert -size ${image_size}x${image_size} xc:black -draw \"fill none stroke white stroke-linecap round stroke-width %0d line 128,128 128,128.0001\" img_%03d.png; c2d img_%03d.png -o %04d.nii.gz" %(v, i, i, i)
END
}

generate_test_images | bash -x

for vel_reg in 0 1 2 3 4 5
do
    for def_reg in 0 1 2 3 4 5
    do
        python ../../pos_mdt_main.py \
            --jobId mdt_test_rectangle \
            --workDir ${WORK_DIR} \
            --antsDimension 2 \
            --firstImageIndex 0 \
            --lastImageIndex 99 \
            --iterations 10 \
            -i ./ \
            --antsImageMetric CC \
            --antsImageMetricOpt 5 \
            --antsTransformation 0.25 \
            --antsRegularization ${vel_reg} ${def_reg} \
            --antsIterations  1000x1000x1000 \
            --antsAffineIterations 0 \
            --loglevel DEBUG  
        #   --settingsFile configuration.json 

        cp -rfv ${WORK_DIR}/12_transf_f/sddm_convergence.txt sddm_convergence_${vel_reg}_${def_reg}_sigma${sigma}.txt
        cp -rfv ${WORK_DIR}/12_transf_f/sddm0009.nii.gz test_sddm_${vel_reg}_${def_reg}_sigma${sigma}.nii.gz
        cp -rfv ${WORK_DIR}/05_iterations/0009/21_resliced/average.nii.gz test_average_${vel_reg}_${def_reg}_sigma${sigma}.nii.gz

#       diff reference_sddm.nii.gz test_sddm.nii.gz > sddm_diff.txt
#       diff reference_average.nii.gz test_average.nii.gz > average_diff.txt
    done
done

rm -vf ????.nii.gz
rm -vf img_???.png
