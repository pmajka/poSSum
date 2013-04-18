set -xe

python ../../pos_mdt_main.py \
    --jobId minimum_deformation_template_test_2 \
    --firstImageIndex 0 \
    --lastImageIndex 4 \
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
    --settingsFile configuration.json 2>&1 | tee > mdt_test_2.log
