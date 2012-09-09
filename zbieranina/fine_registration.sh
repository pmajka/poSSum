DIR_ITER_SRC_VOL='01_source_volume'
DIR_ITER_SRC_SLICES='02_source_slices'
DIR_ITER_PROCESS_SLICES='03_process_slices'
DIR_ITER_TRANSF='04_transformations'
DIR_ITER_RESLICED='05_resliced_grayscale'
DIR_ITER_FINAL_VOL='06_final_volume'
DIR_ITER_RESL_NEXT='07_slices_for_next_iteration'

DIR_JOB_SOURCE_VOL='01_source_volume'
DIR_JOB_RESULTS_INTERMEDIATE='08_results_intermediate'
DIR_FINAL_VOL='10_final_volume'

source_vol_name=source_volume.nii.gz
#source_vol_name_sm=source_volume_sm.nii.gz
#source_vol_name_sm=myelin.nii.gz
source_vol_name_sm=02_02_NN2_final_myelin_rgb.nii.gz

mkdir -p ${DIR_JOB_SOURCE_VOL} ${DIR_JOB_RESULTS_INTERMEDIATE} ${DIR_FINAL_VOL}

startslice=0
endlice=263
endlicec=264

ITERATIONS=10


#outputSpacing='0.03168 0.08 0.03168'
outputSpacing='0.01584 0.08 0.01584'

iter=1
DIR_CUR_ITER=iteration_`printf %04d $iter`
mkdir -p ${DIR_CUR_ITER}/${DIR_ITER_SRC_VOL} \
         ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES} \
         ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES} \
         ${DIR_CUR_ITER}/${DIR_ITER_TRANSF} \
         ${DIR_CUR_ITER}/${DIR_ITER_RESLICED} \
         ${DIR_CUR_ITER}/${DIR_ITER_FINAL_VOL} \
         ${DIR_CUR_ITER}/${DIR_ITER_RESL_NEXT}

#   c3d ${DIR_JOB_SOURCE_VOL}/${source_vol_name} \
#       -resample 50%x100%x50% \
#       -o ${DIR_JOB_SOURCE_VOL}/${source_vol_name_sm}
#       
        sliceVol.py \
            -i ${DIR_JOB_SOURCE_VOL}/${source_vol_name_sm} \
            -r ${startslice} ${endlicec} 1 -s 1 \
            -o "${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/%04d.png"
    
    for i in `seq -s" "  ${startslice} 1 ${endlice}`
    do
        ii=`printf %04d $i`
       convert ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/${ii}.png \
           ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.png
#        c2d ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/${ii}.png -thresh 70 180 0 255 \
#            -type uchar -o ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.png
    done
    
#   rm -vf gadsm_${iter}.txt
#   for i in `seq -s" "  ${startslice} 1 ${endlice}`
#   do
#       ii=`printf %04d $i`
#       echo "GradientAnisotropicDiffusionImageFilter.py -i ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/${ii}.png -d 2 -t 0.04 -c 3.0 -n  80 -o ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.nii.gz; c2d ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.nii.gz -type ushort -o ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.png" >> gadsm_${iter}.txt
#   done
#   cat  gadsm_${iter}.txt | parallel -j 16 -k 
#   rm -rfv ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/*.nii.gz
    
     python average_register_to_multiply_ref.py CC 16 1,1 1 0.05 ${iter}  | grep  0001_REGISTER | cut -f1 -d#>g; cat g | parallel -j 8 -k
     python average_register_to_multiply_ref.py CC 16 1,1 1 0.05 ${iter}  | grep '#0005_RE' | parallel -j 8 -k
     StackSlices ${DIR_CUR_ITER}/stack.nii.gz -1 -1 0 ${DIR_CUR_ITER}/${DIR_ITER_RESLICED}/*
    
    reorientImage.py -i ${DIR_CUR_ITER}/stack.nii.gz \
                     -o ${DIR_JOB_RESULTS_INTERMEDIATE}/`printf %04d $iter`.nii.gz \
                    --permutationOrder 0 2 1 \
                    --orientationCode RAS \
                    --outputVolumeScalarType uchar \
                    --setOrigin 0 0 0 \
                    --setSpacing ${outputSpacing} \
                    --cleanup | bash -xe

for iter in `seq -s" "  2 1 ${ITERATIONS}`
do
    previter=`echo $iter -1 | bc`
    DIR_CUR_ITER=iteration_`printf %04d $iter`
    mkdir -p ${DIR_CUR_ITER}/${DIR_ITER_SRC_VOL} \
             ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES} \
             ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES} \
             ${DIR_CUR_ITER}/${DIR_ITER_TRANSF} \
             ${DIR_CUR_ITER}/${DIR_ITER_RESLICED} \
             ${DIR_CUR_ITER}/${DIR_ITER_FINAL_VOL} \
             ${DIR_CUR_ITER}/${DIR_ITER_RESL_NEXT}
    
    sliceVol.py \
        -i ${DIR_JOB_RESULTS_INTERMEDIATE}/`printf %04d $previter`.nii.gz \
        -r ${startslice} ${endlicec} 1 -s 1 \
        -o "${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/%04d.png"
    
    for i in `seq -s" "  ${startslice} 1 ${endlice}`
    do
        ii=`printf %04d $i`
        convert ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/${ii}.png \
            ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.png
#        c2d ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/${ii}.png -thresh 50 200 0 255 \
#           -type uchar -o ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.png
    done

#   rm -vf gadsm_${iter}.txt
#   for i in `seq -s" "  ${startslice} 1 ${endlice}`
#   do
#       ii=`printf %04d $i`
#       echo "GradientAnisotropicDiffusionImageFilter.py -i ${DIR_CUR_ITER}/${DIR_ITER_SRC_SLICES}/${ii}.png -d 2 -t 0.03 -c 5.0 -n 120 -o ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.nii.gz; c2d ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.nii.gz -type ushort -o ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/${ii}.png" >> gadsm_${iter}.txt
#   done
#   cat  gadsm_${iter}.txt | parallel -j 16 -k 
#   rm -rfv ${DIR_CUR_ITER}/${DIR_ITER_PROCESS_SLICES}/*.nii.gz
    
    python average_register_to_multiply_ref.py CC 16 1,1 1 0.05 ${iter}  | grep  0001_REGISTER | cut -f1 -d#>g; cat g | parallel -j 8 -k
    python average_register_to_multiply_ref.py CC 16 1,1 1 0.05 ${iter}  | grep '#0005_RE' | parallel -j 8 -k
    StackSlices ${DIR_CUR_ITER}/stack.nii.gz -1 -1 0 ${DIR_CUR_ITER}/${DIR_ITER_RESLICED}/*
    
    reorientImage.py -i ${DIR_CUR_ITER}/stack.nii.gz \
                     -o ${DIR_JOB_RESULTS_INTERMEDIATE}/`printf %04d $iter`.nii.gz \
                    --permutationOrder 0 2 1 \
                    --orientationCode RAS \
                    --outputVolumeScalarType uchar \
                    --setOrigin 0 0 0 \
                    --setSpacing ${outputSpacing} \
                    --cleanup | bash -xe
done

