#!/bin/bash -xe

#WORK_DIR=/dev/shm/uniform_myelin/
WORK_DIR=/home/pmajka/deformable_myelin/

START_SLICE=0
END_SLICE=263

GRAYSCALE_VOLUME=/home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_myelin_r.nii.gz
RGB_VOLUME=/home/pmajka/possum/data/02_02_NN2/70_blockface_to_histology_registration/02_02_NN2_final_myelin_rgb.nii.gz
VOLUME_MASK=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_myelin_mask.nii.gz
MASK_FILENAME=/home/pmajka/possum/data/02_02_NN2/73_deformable_histology_reconstruction/02_02_NN2_deformable_histology_reconstruction_myelin_mask.nii.gz
OUTLINE_FILENAME=/home/pmajka/possum/data/02_02_NN2/73_deformable_histology_reconstruction/02_02_NN2_deformable_histology_reconstruction_myelin_outline.nii.gz
MASKED_FILENAME=/home/pmajka/possum/data/02_02_NN2/73_deformable_histology_reconstruction/02_02_NN2_deformable_histology_reconstruction_myelin_masked.nii.gz
OUTLIER_MASK_FILENAME=/home/pmajka/Dropbox/Photos/oposy_skrawki/02_02_NN2/02_02_NN2_final_myelin_mask_outlier_removal.nii.gz
CUSTOM_MASK_FILENAME=processing/02_02_NN2_myelin_masked_custom.csv
CUSTOM_MASK_FILENAME2=processing/02_02_NN2_myelin_masked_custom_mask.csv
REGISTER_SUBSET_FILENAME=processing/02_02_NN2_myelin_outliers.csv
REGISTER_SUBSET_FILENAME_ANTERIOR=processing/02_02_NN2_myelin_outliers_anteriror.csv
OUTPUT_NAMING=02_02_NN2_deformable_hist_reconstruction_myelin
#ARCHIVE_DIR=/home/pmajka/possum/`date +"deformable_myelin_summary_%Y-%m-%d_%H-%M"`
ARCHIVE_DIR=/home/pmajka/possum/deformable_myelin_summary

EVALUATE_REGISTRATION_SCRIPT=framework/pos_evaluate_registration.py
DEFORMABLE_REGISTRATION_SCRIPT=framework/deformable_histology_reconstruction.py

TEMP_VOLUME_FILENAME="/dev/shm/${OUTPUT_NAMING}__temp__vol__gray.vtk"

DO_PREPROCESS='true'
DO_REGISTRATION='true'
DO_ARCHIVE='true'

# ----------------------------------------------------------
# Output volume configuration
# ----------------------------------------------------------
OUTPUT_VOLUME_SPACING="0.01584 0.08 0.01584"
OUTPUT_VOLUME_ORGIN="0.0 -0.04 0.0"
OUTPUT_VOLUME_ORIENTATION_CODE="RAS"
OUTPUT_VOLUME_PERMURATION_ORDER='0 2 1'

mkdir -p $WORK_DIR

function archive_results {
SRC_DIR=${1}
TARGET_DIR=${2}

mkdir -p ${TARGET_DIR}
mkdir -p ${TARGET_DIR}/12_jacobian/ 

cp -rfv ${SRC_DIR}/08_intermediate_results ${TARGET_DIR}
cp -rfv ${SRC_DIR}/09_final_deformation    ${TARGET_DIR}

cp -v ${MASKED_FILENAME} ${TARGET_DIR}
cp -v ${MASK_FILENAME} ${TARGET_DIR}
cp -v ${CUSTOM_MASK_FILENAME} ${TARGET_DIR}
cp -v ${OUTLIER_MASK_FILENAME} ${TARGET_DIR}/custom_outliers_mask.nii.gz
cp -v ${REGISTER_SUBSET_FILENAME} ${TARGET_DIR}
cp -v ${REGISTER_SUBSET_FILENAME_ANTERIOR} ${TARGET_DIR}

#   python ${EVALUATE_REGISTRATION_SCRIPT}     \
#       --msqFilename ${TARGET_DIR}/msq.txt    \
#       --plotMsqFilename ${TARGET_DIR}/msq    \
#       --ncorrFilename ${TARGET_DIR}/corr.txt \
#       --plotNcorrFilename ${TARGET_DIR}/corr  \
#       ${TARGET_DIR}/08_intermediate_results/intermediate_${OUTPUT_NAMING}_00*.nii.gz
}

function reslice_multichannel {
    SOURCE_VOLUME=${1}
    SRC_DIR=${2}
    TARGET_DIR=${3}
    START_SLICE=${4}
    END_SLICE=${5}
    
    TEMPDIR=${TARGET_DIR}/10_resliced_multichannel/
    TEMPDIRM=${TARGET_DIR}/11_resliced_mask/
    mkdir -p ${TEMPDIR} ${TEMPDIRM}
    
    sliceVol.py \
        -i ${VOLUME_MASK} \
        -o "${TARGET_DIR}/11_resliced_mask/%04d.png" \
        -r ${START_SLICE} $((END_SLICE+1)) 1 \
        -s 1 
    
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
        
        WarpImageMultiTransform 2 \
            ${TEMPDIRM}/${ii}.png \
            ${TEMPDIRM}/${ii}.nii.gz \
            -R ${TEMPDIR}/resliced_${ii}.nii.gz\
            --use-NN \
            ${SRC_DIR}/09_final_deformation/${ii}.nii.gz
         
        rm -rfv \
            ${TEMPDIR}/resliced_${ii}x.nii.gz \
            ${TEMPDIR}/resliced_${ii}y.nii.gz \
            ${TEMPDIR}/resliced_${ii}z.nii.gz
        
        ANTSJacobian 2 \
            ${SRC_DIR}/09_final_deformation/${ii}.nii.gz \
            ${TARGET_DIR}/12_jacobian/${ii}
    done
    
    stack_rgb_slices.py \
        -b ${START_SLICE} \
        -e ${END_SLICE} \
        -f ${TEMPDIR}/resliced_%04d.nii.gz \
        -o ${TEMP_VOLUME_FILENAME}
    
    reorientImage.py \
               -i ${TEMP_VOLUME_FILENAME} \
                --permutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER}\
                --orientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}\
                --outputVolumeScalarType uchar\
                --setSpacing ${OUTPUT_VOLUME_SPACING}\
                --setOrigin ${OUTPUT_VOLUME_ORGIN}\
                -o ${TARGET_DIR}/${OUTPUT_NAMING}_resliced.nii.gz \
                --multichannelImage  \
                --cleanup | bash -xe;
    
    StackSlices \
        ${TEMP_VOLUME_FILENAME} \
        -1 -1 0 \
        ${TEMPDIRM}/*.nii.gz
    
    reorientImage.py \
               -i ${TEMP_VOLUME_FILENAME} \
                --permutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER}\
                --orientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}\
                --outputVolumeScalarType uchar\
                --setSpacing ${OUTPUT_VOLUME_SPACING}\
                --setOrigin ${OUTPUT_VOLUME_ORGIN}\
                -o ${TARGET_DIR}/${OUTPUT_NAMING}_resliced_mask.nii.gz \
                --cleanup | bash -xe;
    
    rm ${TEMP_VOLUME_FILENAME}
    rm -rfv ${TEMPDIR}
}

if [ ${DO_PREPROCESS} = 'true' ]
then
    c3d ${VOLUME_MASK} \
        -replace 4 1 \
        -replace 2 0 \
        -replace 3 0 \
        -type uchar \
        -o ${MASK_FILENAME}
    
    c3d ${VOLUME_MASK} \
        -replace 4 1 \
        -replace 2 1 \
        -replace 3 0 \
        -type uchar \
        -o ${OUTLINE_FILENAME}
    
    c3d \
        ${GRAYSCALE_VOLUME} \
        -scale -1 -shift 255 \
        ${OUTLINE_FILENAME} \
        -times \
        -scale -1 -shift 255 \
        -type uchar -o ${MASKED_FILENAME}
fi

if [ ${DO_REGISTRATION} = 'true' ]
then
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASK_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --maskedVolume  1 ${OUTLIER_MASK_FILENAME} \
        --maskedVolumeFile ${CUSTOM_MASK_FILENAME2} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --iterations 1 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.1 \
        --antsRegularization 3.0 1.0 \
        --antsIterations 1000x1000x1000x0x0 \
        --outputVolumePermutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER} \
        --outputVolumeSpacing ${OUTPUT_VOLUME_SPACING} \
        --outputVolumeOrigin ${OUTPUT_VOLUME_ORGIN} \
        --outputVolumeOrientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}

    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --maskedVolume  1 ${OUTLIER_MASK_FILENAME} \
        --maskedVolumeFile ${CUSTOM_MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --iterations 2 \
        --startFromIteration 1 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.1 \
        --antsRegularization 3.0 1.0 \
        --antsIterations 1000x1000x1000x0x0 \
        --outputVolumePermutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER} \
        --outputVolumeSpacing ${OUTPUT_VOLUME_SPACING} \
        --outputVolumeOrigin ${OUTPUT_VOLUME_ORGIN} \
        --outputVolumeOrientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --registerSubset ${REGISTER_SUBSET_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --skipSlicePreprocess \
        --iterations 7 \
        --startFromIteration 2 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.15 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x0x0 \
        --outputVolumePermutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER} \
        --outputVolumeSpacing ${OUTPUT_VOLUME_SPACING} \
        --outputVolumeOrigin ${OUTPUT_VOLUME_ORGIN} \
        --outputVolumeOrientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   0 ${MASKED_FILENAME} \
        --outlineVolume 1 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --skipSlicePreprocess \
        --startFromIteration 7 \
        --iterations 17 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x0000x0000 \
        --outputVolumePermutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER} \
        --outputVolumeSpacing ${OUTPUT_VOLUME_SPACING} \
        --outputVolumeOrigin ${OUTPUT_VOLUME_ORGIN} \
        --outputVolumeOrientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --skipSlicePreprocess \
        --startFromIteration 15 \
        --iterations 20 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 2 \
        --antsTransformation 0.01 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x0000x0000 \
        --outputVolumePermutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER} \
        --outputVolumeSpacing ${OUTPUT_VOLUME_SPACING} \
        --outputVolumeOrigin ${OUTPUT_VOLUME_ORGIN} \
        --outputVolumeOrientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --registerSubset ${REGISTER_SUBSET_FILENAME_ANTERIOR} \
        --skipSlicePreprocess \
        --stackFinalDeformation \
        --startFromIteration 20 \
        --iterations 24 \
        --neighbourhood 2 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 4 \
        --antsTransformation 0.01 \
        --antsRegularization 1.0 1.0 \
        --antsIterations 1000x1000x1000x1000x0000 \
        --outputVolumePermutationOrder ${OUTPUT_VOLUME_PERMURATION_ORDER} \
        --outputVolumeSpacing ${OUTPUT_VOLUME_SPACING} \
        --outputVolumeOrigin ${OUTPUT_VOLUME_ORGIN} \
        --outputVolumeOrientationCode ${OUTPUT_VOLUME_ORIENTATION_CODE}
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
