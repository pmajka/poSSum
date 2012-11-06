#!/bin/bash -xe

WORK_DIR=/dev/shm/uniform/

START_SLICE=0
END_SLICE=263

GRAYSCALE_VOLUME=/home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_nissl_r.nii.gz
RGB_VOLUME=/home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_nissl_rgb.nii.gz
VOLUME_MASK=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_nissl_mask.nii.gz
MASK_FILENAME=/home/pmajka/possum/data/02_02_NN2/73_deformable_histology_reconstruction/02_02_NN2_deformable_histology_reconstruction_nissl_outline.nii.gz
MASKED_FILENAME=/home/pmajka/possum/data/02_02_NN2/73_deformable_histology_reconstruction/02_02_NN2_deformable_histology_reconstruction_nissl_masked.nii.gz
OUTLIER_MASK_FILENAME=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_nissl_mask_outlier_removal.nii.gz
CUSTOM_MASK_FILENAME=processing/02_02_NN2_masked_custom.csv
REGISTER_SUBSET_FILENAME=processing/02_02_NN2_outliers.csv
OUTPUT_NAMING=02_02_NN2_deformable_hist_reconstruction_nissl
ARCHIVE_DIR=/home/pmajka/possum/`date +"deformable_nissl_summary_%Y-%m-%d_%H-%M"`

EVALUATE_REGISTRATION_SCRIPT=framework/pos_evaluate_registration.py
DEFORMABLE_REGISTRATION_SCRIPT=framework/deformable_histology_reconstruction.py

DO_PREPROCESS='false'
DO_REGISTRATION='true'
DO_ARCHIVE='true'

mkdir -p $WORK_DIR

function archive_results {
    SRC_DIR=${1}
    TARGET_DIR=${2}
    
    mkdir -p ${TARGET_DIR}
    
    cp -rfv ${SRC_DIR}/08_intermediate_results ${TARGET_DIR}
    cp -rfv ${SRC_DIR}/09_final_deformation    ${TARGET_DIR}
    
    cp -v ${MASKED_FILENAME} ${TARGET_DIR}
    cp -v ${MASK_FILENAME} ${TARGET_DIR}
    cp -v ${CUSTOM_MASK_FILENAME} ${TARGET_DIR}
    cp -v ${OUTLIER_MASK_FILENAME} ${TARGET_DIR}/custom_outliers_mask.nii.gz
    cp -v ${REGISTER_SUBSET_FILENAME} ${TARGET_DIR}
    
    python ${EVALUATE_REGISTRATION_SCRIPT}     \
        --msqFilename ${TARGET_DIR}/msq.txt    \
        --plotMsqFilename ${TARGET_DIR}/msq    \
        --ncorrFilename ${TARGET_DIR}/corr.txt \
        --plotNcorrFilename ${TARGET_DIR}/corr  \
        ${TARGET_DIR}/08_intermediate_results/intermediate_${OUTPUT_NAMING}_00*.nii.gz
}

function reslice_multichannel {
    SOURCE_VOLUME=${1}
    SRC_DIR=${2}
    TARGET_DIR=${3}
    START_SLICE=${4}
    END_SLICE=${5}
    
    TEMPDIR=${TARGET_DIR}/10_resliced_multichannel/
    mkdir -p ${TEMPDIR}
    
    sliceVol.py \
        -i ${SOURCE_VOLUME} \
        -o "${TARGET_DIR}/10_resliced_multichannel/%04d.png" \
        -r ${START_SLICE} $((END_SLICE+1)) 1 \
        -s 1 
    
    for slice in `seq ${START_SLICE} 1 ${END_SLICE}`
    do
        ii=`printf %04d $slice`
        
        c2d -mcs ${TEMPDIR}/${ii}.png \
            -type uchar \
            -oo \
            ${TEMPDIR}/${ii}x.nii.gz \
            ${TEMPDIR}/${ii}y.nii.gz \
            ${TEMPDIR}/${ii}z.nii.gz
        
        for c in x y z 
        do
            WarpImageMultiTransform 2 \
                ${TEMPDIR}/${ii}${c}.nii.gz \
                ${TEMPDIR}/resliced_${ii}${c}.nii.gz \
                -R ${TEMPDIR}/${ii}${c}.nii.gz \
                ${SRC_DIR}/09_final_deformation/${ii}.nii.gz
        done
        
        c2d \
            ${TEMPDIR}/resliced_${ii}x.nii.gz \
            ${TEMPDIR}/resliced_${ii}y.nii.gz \
            ${TEMPDIR}/resliced_${ii}z.nii.gz \
            -type uchar -omc 3 ${TEMPDIR}/resliced_${ii}.nii.gz
         
        rm -rfv \
            ${TEMPDIR}/resliced_${ii}x.nii.gz \
            ${TEMPDIR}/resliced_${ii}y.nii.gz \
            ${TEMPDIR}/resliced_${ii}z.nii.gz
    done
    
    stack_rgb_slices.py \
        -b ${START_SLICE} \
        -e ${END_SLICE} \
        -f ${TEMPDIR}/resliced_%04d.nii.gz \
        -o ${SRC_DIR}/08_intermediate_results/__temp__vol__gray.vtk
    
    reorientImage.py \
               -i ${SRC_DIR}/08_intermediate_results/__temp__vol__gray.vtk \
                --permutationOrder 0 2 1\
                --orientationCode RAS\
                --outputVolumeScalarType uchar\
                --setSpacing 0.01584 0.08 0.01584\
                --setOrigin 0.0 0.04 0.0\
                -o ${TARGET_DIR}/nissl_resliced.nii.gz \
                --multichannelImage  \
                --cleanup | bash -xe;
    
    rm ${SRC_DIR}/08_intermediate_results/__temp__vol__gray.vtk;
    rm -rfv ${TEMPDIR}
}

if [ ${DO_PREPROCESS} = 'true' ]
then
    c3d ${VOLUME_MASK} \
        -replace 2 1 \
        -type uchar \
        -o ${MASK_FILENAME}
    
    c3d \
        ${GRAYSCALE_VOLUME} \
        -scale -1 -shift 255 \
        ${MASK_FILENAME} \
        -times \
        -scale -1 -shift 255 \
        -type uchar -o ${MASKED_FILENAME}
fi

if [ ${DO_REGISTRATION} = 'true' ]
then
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --maskedVolume  1 ${OUTLIER_MASK_FILENAME} \
        --maskedVolumeFile ${CUSTOM_MASK_FILENAME} \
        --stackFinalDeformation \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --iterations 4 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
        --antsRegularization 3.0 1.0 \
        --antsIterations 1000x1000x1000x0x0 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.04 0 \
        --outputVolumeOrientationCode RAS
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --registerSubset ${REGISTER_SUBSET_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --iterations 8 \
        --startFromIteration 4 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x0x0 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.04 0 \
        --outputVolumeOrientationCode RAS
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   0 ${MASKED_FILENAME} \
        --outlineVolume 1 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --skipSlicePreprocess \
        --startFromIteration 8 \
        --iterations 13 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x0000x0000 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.04 0 \
        --outputVolumeOrientationCode RAS
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --startFromIteration 13 \
        --iterations 18 \
        --neighbourhood 1 \
        --stackFinalDeformation \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 2 \
        --antsTransformation 0.01 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x0000x0000 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.04 0 \
        --outputVolumeOrientationCode RAS
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --stackFinalDeformation \
        --startFromIteration 18 \
        --iterations 24 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 4 \
        --antsTransformation 0.01 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x1000x0000 \
        --outputVolumePermutationOrder 0 2 1 \
        --outputVolumeSpacing 0.01584 0.08 0.01584 \
        --outputVolumeOrigin 0 0.04 0 \
        --outputVolumeOrientationCode RAS
fi

if [ ${DO_ARCHIVE} = 'true' ]
then
    archive_results ${WORK_DIR} ${ARCHIVE_DIR}
    reslice_multichannel \
        ${RGB_VOLUME} \
        ${WORK_DIR} \
        ${ARCHIVE_DIR} \
        $START_SLICE \
        $END_SLICE 
fi
