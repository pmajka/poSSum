set -xe

python pos_mdt_main.py \
    --firstImageIndex 0 \
    --lastImageIndex 4 \
    --iterations 10 \
    -i /home/pmajka/Downloads/q \
    --antsImageMetric CC \
    --antsImageMetricOpt 5 \
    --antsTransformation 0.25 \
    --antsRegularization 3 0 \
    --antsIterations 30x90x20 \
    --antsDimension 2 \
    --antsAffineIterations 10000x10000x10000x10000x10000
#   -i /home/pmajka/ \
#   -i /home/pmajka/Downloads/a/ANTS/trunk/Examples/Data \
#   -i /home/pmajka/Downloads/qweqwe \
#   -i /home/pmajka/Downloads/a/ANTS/ \
