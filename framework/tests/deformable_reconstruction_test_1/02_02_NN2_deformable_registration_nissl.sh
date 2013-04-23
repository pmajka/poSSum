#!bin/bash
set -xe

source setenv.sh

#----------------------------------------------------------
# Should not be changed
# -----------------------------------------------------------------------------
specimen_name=02_02_NN2

DIRECOTRY_DATA=`pwd`/data/
DIRECTORY_SUPPLEMENT=`pwd`/processing_supplement

#----------------------------------------------------------
# Definitions of directories
#----------------------------------------------------------
#WORK_DIR=/dev/shm/uniform/
WORK_DIR=/home/pmajka/deformable_nissl/
#ARCHIVE_DIR=/home/pmajka/possum/`date +"deformable_nissl_summary_%Y-%m-%d_%H-%M"`
ARCHIVE_DIR=/home/pmajka/possum/deformable_nissl_summary
SUPPLEMENTARIES=${DIRECTORY_SUPPLEMENT}/${specimen_name}_deformable_histology_reconstruction/

START_SLICE=0
END_SLICE=263

LATST_ITERATION_IDX=0025

# -----------------------------------------------------------------------------
# Source volumes and masks
GRAYSCALE_VOLUME=${DIRECOTRY_DATA}/${specimen_name}/70_blockface_to_histology_registration/${specimen_name}_final_nissl_r.nii.gz
RGB_VOLUME=${DIRECOTRY_DATA}${specimen_name}/70_blockface_to_histology_registration/${specimen_name}_final_nissl_rgb.nii.gz
VOLUME_MASK=${SUPPLEMENTARIES}/${specimen_name}_final_nissl_mask.nii.gz
MASK_FILENAME=${DIRECOTRY_DATA}/${specimen_name}/73_deformable_histology_reconstruction/${specimen_name}_deformable_histology_reconstruction_nissl_outline.nii.gz
MASKED_FILENAME=${DIRECOTRY_DATA}/${specimen_name}/73_deformable_histology_reconstruction/${specimen_name}_deformable_histology_reconstruction_nissl_masked.nii.gz
OUTLIER_MASK_FILENAME=${SUPPLEMENTARIES}/${specimen_name}_final_nissl_mask_outlier_removal.nii.gz

#------------------------------------------------------------------------------
# Files defining slices assignment for nonstandard registration
CUSTOM_MASK_FILENAME=${SUPPLEMENTARIES}/${specimen_name}_nissl_masked_custom.csv
REGISTER_SUBSET_FILENAME=${SUPPLEMENTARIES}/${specimen_name}_nissl_outliers.csv
REGISTER_SUBSET_FILENAME_ANTERIOR=${SUPPLEMENTARIES}/${specimen_name}_nissl_outliers_anteriror.csv
OUTPUT_NAMING=${specimen_name}_deformable_hist_reconstruction_nissl

#------------------------------------------------------------------------------
# Paths for scripts
EVALUATE_REGISTRATION_SCRIPT=/home/pmajka/Dropbox/python_multiprocessing_tests/framework/pos_evaluate_registration.py
DEFORMABLE_REGISTRATION_SCRIPT=/home/pmajka/Dropbox/python_multiprocessing_tests/framework/deformable_histology_reconstruction.py
DEFORMABLE_REGISTRATION_ANALYSIS=/home/pmajka/Dropbox/python_multiprocessing_tests/framework/draw_glyphs_2d.py

TEMP_VOLUME_FILENAME="/dev/shm/${OUTPUT_NAMING}__temp__vol__gray.vtk"

# -----------------------------------------------------------------------------
# End of should not be changed
# -----------------------------------------------------------------------------

DO_PREPROCESS='true'
DO_REGISTRATION='true'
DO_ARCHIVE='true'

DO_GLOBAL_RESLICE='true'
DO_RESLICE_IMAGE='true'
DO_RESLICE_MASKS='true'
DO_CREATE_JACOBIAN='true'
DO_ANALYZE_DEFORMATIONS='true'

# ----------------------------------------------------------
# Output volume configuration
# ----------------------------------------------------------
OUTPUT_PLANE_RES="0.01584"
OUTPUT_VOLUME_SPACING="${OUTPUT_PLANE_RES} 0.08 ${OUTPUT_PLANE_RES}"
OUTPUT_VOLUME_ORGIN="0.0 0.04 0.0"
OUTPUT_VOLUME_ORIENTATION_CODE="RAS"
OUTPUT_VOLUME_PERMURATION_ORDER='0 2 1'

mkdir -p $WORK_DIR

function archive_results {
    SRC_DIR=${1}
    TARGET_DIR=${2}
    
    mkdir -p ${TARGET_DIR}
    mkdir -p ${TARGET_DIR}/12_jacobian/ 
    mkdir -p ${TARGET_DIR}/13_resliced_grayscale/
    mkdir -p ${TARGET_DIR}/14_resliced_outline/
    mkdir -p ${TARGET_DIR}/15_deformation_analysis/
        
    cp -rfv ${SRC_DIR}/01_init_slices ${TARGET_DIR}
    cp -rfv ${SRC_DIR}/08_intermediate_results ${TARGET_DIR}
    cp -rfv ${SRC_DIR}/09_final_deformation    ${TARGET_DIR}
    cp -rfv ${SRC_DIR}/05_iterations/${LATST_ITERATION_IDX}/21_resliced/* \
            ${TARGET_DIR}/13_resliced_grayscale/
    cp -rfv ${SRC_DIR}/05_iterations/${LATST_ITERATION_IDX}/22_resliced_outline/* \
            ${TARGET_DIR}/14_resliced_outline/
    
    cp -v ${MASKED_FILENAME} ${TARGET_DIR}
    cp -v ${MASK_FILENAME} ${TARGET_DIR}
    cp -v ${CUSTOM_MASK_FILENAME} ${TARGET_DIR}
    cp -v ${OUTLIER_MASK_FILENAME} ${TARGET_DIR}/custom_outliers_mask.nii.gz
    cp -v ${REGISTER_SUBSET_FILENAME} ${TARGET_DIR}
    cp -v ${REGISTER_SUBSET_FILENAME_ANTERIOR} ${TARGET_DIR}
    
    python ${EVALUATE_REGISTRATION_SCRIPT}     \
        --msqFilename ${TARGET_DIR}/msq.txt    \
        --plotMsqFilename ${TARGET_DIR}/msq    \
        --ncorrFilename ${TARGET_DIR}/corr.txt \
        --plotNcorrFilename ${TARGET_DIR}/corr  \
        ${TARGET_DIR}/08_intermediate_results/intermediate_${OUTPUT_NAMING}_00*.nii.gz
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

function reslice_multichannel {
    SOURCE_VOLUME=${1}
    SRC_DIR=${2}
    TARGET_DIR=${3}
    START_SLICE=${4}
    END_SLICE=${5}
    
    TEMPDIR=${TARGET_DIR}/10_resliced_multichannel/
    TEMPDIRM=${TARGET_DIR}/11_resliced_mask/
    mkdir -p ${TEMPDIR} ${TEMPDIRM}
    
    if [ ${DO_CREATE_JACOBIAN} = 'true' ]
    then
        
        for slice in `seq ${START_SLICE} 1 ${END_SLICE}`
        do
            ii=`printf %04d $slice`
            ANTSJacobian 2 \
                ${SRC_DIR}/09_final_deformation/${ii}.nii.gz \
                ${TARGET_DIR}/12_jacobian/${ii}
        done
    fi
    
    if [ ${DO_RESLICE_IMAGE} = 'true' ]
    then
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
    fi
    
    if [ ${DO_RESLICE_MASKS} = 'true' ]
    then
        
        sliceVol.py \
            -i ${VOLUME_MASK} \
            -o "${TARGET_DIR}/11_resliced_mask/%04d.png" \
            -r ${START_SLICE} $((END_SLICE+1)) 1 \
            -s 1 
        
        for slice in `seq ${START_SLICE} 1 ${END_SLICE}`
        do
            ii=`printf %04d $slice`
            
            WarpImageMultiTransform 2 \
                ${TEMPDIRM}/${ii}.png \
                ${TEMPDIRM}/${ii}.nii.gz \
                -R ${TEMPDIR}/resliced_${ii}.nii.gz\
                --use-NN \
                ${SRC_DIR}/09_final_deformation/${ii}.nii.gz
        done
        
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
    fi
    
    if [ ${DO_ANALYZE_DEFORMATIONS} = 'true' ]
    then
        #export DISPLAY=:0.0
        #rm -rfv ${TARGET_DIR}/mean_slice_deformation
        
#       for slice in `seq ${START_SLICE} 1 ${END_SLICE}`
#       do
#           ii=`printf %04d ${slice}`
#           
#           python ${DEFORMABLE_REGISTRATION_ANALYSIS} \
#               -w ${TARGET_DIR}/09_final_deformation/${ii}.nii.gz \
#               -i ${TARGET_DIR}/01_init_slices/${ii}.nii.gz \
#               --deformationOverlayOpacity 0.0 \
#               --jacobianOverlayOpacity 0.3 \
#               --deformationScaleRange 0 1.0 \
#               --glyphConfiguration 5000 10 1 \
#               --spacing ${OUTPUT_PLANE_RES} ${OUTPUT_PLANE_RES} \
#               --screenshot ${TARGET_DIR}/15_deformation_analysis/${ii}.png 
#       done
        
        for slice in `seq ${START_SLICE} 1 ${END_SLICE}`
        do
            ii=`printf %04d ${slice}`
            ip=`echo ${ii} -1 | bc | awk ' { if($1>=0) { print $1} else {print $1*-1 }}'`
            ip=`printf %04d ${ip}`
            
            c2d ${TARGET_DIR}/13_resliced_grayscale/${ip}.nii.gz \
                ${TARGET_DIR}/13_resliced_grayscale/${ii}.nii.gz \
                     -scale -1 -add -shift 128 -clip 0 255 -type uchar \
                -o __finaldiff${ii}.png
            
            c2d ${TARGET_DIR}/01_init_slices/${ip}.nii.gz \
                ${TARGET_DIR}/01_init_slices/${ii}.nii.gz \
                     -scale -1 -add -shift 128 -clip 0 255 -type uchar \
                -o __initdiff${ii}.png
            
            c2d ${TARGET_DIR}/01_init_slices/${ii}.nii.gz -type uchar -o __moving${ii}.png
            c2d ${TARGET_DIR}/13_resliced_grayscale/${ip}.nii.gz -type uchar -o __reference${ii}.png
            c2d ${TARGET_DIR}/13_resliced_grayscale/${ii}.nii.gz -type uchar -o __resliced${ii}.png
            c2d ${TARGET_DIR}/13_resliced_grayscale/${ip}.nii.gz -type uchar -o __reference${ii}.png
            
            convert  __reference${ii}.png __moving${ii}.png __initdiff${ii}.png \
                     ${TARGET_DIR}/15_deformation_analysis/${ii}.png __resliced${ii}.png __finaldiff${ii}.png \
                     miff:- |montage -  -tile 3x -geometry 900x900+0+0 ${TARGET_DIR}/15_deformation_analysis/comparison${ii}.png
            
            rm -rfv __reference${ii}.png __moving${ii}.png __initdiff${ii}.png __resliced${ii}.png __finaldiff${ii}.png 
        done
        
#       for slice in `seq ${START_SLICE} 1 ${END_SLICE}`
#       do
#           ii=`printf %04d ${slice}`
#           
#           mag=`c2d \
#               -mcs ${TARGET_DIR}/09_final_deformation/${ii}.nii.gz -popas x -popas y -clear \
#               ${TARGET_DIR}/14_resliced_outline/${ii}.nii.gz -clip 0 255 -stretch 0 255 0 1 -scale -1 -shift 1 -spacing ${OUTPUT_PLANE_RES}x${OUTPUT_PLANE_RES}mm -popas m -clear \
#               -push x -dup -times -popas xx -push y -dup -times -popas yy -clear -push xx -push yy -times -sqrt -scale ${OUTPUT_PLANE_RES} -spacing ${OUTPUT_PLANE_RES}x${OUTPUT_PLANE_RES}mm \
#               -push m -times \
#               -voxel-integral | sed "s/Voxel Integral://"`
#           s=`c2d \
#               ${TARGET_DIR}/14_resliced_outline/${ii}.nii.gz -clip 0 255 -stretch 0 255 0 1 -scale -1 -shift 1 -spacing ${OUTPUT_PLANE_RES}x${OUTPUT_PLANE_RES}mm -voxel-integral | sed "s/Voxel Integral://"`
#           echo $slice $mag $s >> ${TARGET_DIR}/mean_slice_deformation
#       done
    fi
    
    rm -rfv ${TEMPDIRM}
    rm -rfv ${TEMPDIR}
    rm -rfv ${TEMP_VOLUME_FILENAME}
}


if [ ${DO_REGISTRATION} = 'true' ]
then
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --maskedVolume  1 ${OUTLIER_MASK_FILENAME} \
        --maskedVolumeFile ${CUSTOM_MASK_FILENAME} \
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
        --iterations 8 \
        --startFromIteration 4 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 16 \
        --antsTransformation 0.05 \
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
        --startFromIteration 8 \
        --iterations 13 \
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
        --startFromIteration 13 \
        --iterations 18 \
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
        --skipSlicePreprocess \
        --startFromIteration 18 \
        --iterations 24 \
        --neighbourhood 1 \
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
    
    python ${DEFORMABLE_REGISTRATION_SCRIPT} \
        --inputVolume   1 ${MASKED_FILENAME} \
        --outlineVolume 0 ${MASK_FILENAME} \
        --startSlice ${START_SLICE} \
        --endSlice ${END_SLICE} \
        --registerSubset ${REGISTER_SUBSET_FILENAME_ANTERIOR} \
        --skipSlicePreprocess \
        --stackFinalDeformation \
        --startFromIteration 24 \
        --iterations 26 \
        --neighbourhood 1 \
        -d $WORK_DIR \
        --outputNaming ${OUTPUT_NAMING} \
        --antsImageMetricOpt 4 \
        --antsTransformation 0.05 \
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
fi

if [ ${DO_GLOBAL_RESLICE} = 'true' ]
then
    reslice_multichannel \
        ${RGB_VOLUME} \
        ${WORK_DIR} \
        ${ARCHIVE_DIR} \
        $START_SLICE \
        $END_SLICE 
fi
