    blockfaceVol="/home/pmajka/possum/data/02_02_NN2/59_blockface_volume/02_02_NN2_blockface_fine_volume_blue.nii.gz"

#   for i in 'nissl_rgb'  'myelin_rgb'
#   do
#       c3d -verbose \
#         ${blockfaceVol} -popas F \
#         -mcs 02_02_NN2_final_${i}.nii.gz \
#         -foreach \
#             -insert F 1 \
#             -origin -7.4595233649x-8.95999979973x6.86344613135mm \
#             -background 255\
#             -reslice-identity \
#             -type uchar \
#             -endfor \
#         -omc 3 resliced_${i}.nii.gz
#   done

#   for i in 'nissl_mask' 'myelin_mask'
#   do
#       c3d -verbose \
#         ${blockfaceVol} \
#         02_02_NN2_final_${i}.nii.gz \
#         -origin -7.4595233649x-8.95999979973x6.86344613135mm \
#         -background 255\
#         -reslice-identity \
#         -type uchar \
#         -o resliced_${i}.nii.gz
#   done
    
for i in 'fine_nissl_rgb'  'fine_myelin_rgb' 'coarse_myelin_rgb' 'coarse_nissl_rgb'
do
    c3d -verbose \
      ${blockfaceVol} -popas F \
      -mcs 02_02_NN2_${i}.nii.gz \
      -foreach \
          -insert F 1 \
          -origin -7.4595233649x-8.95999979973x6.86344613135mm \
          -background 255\
          -reslice-identity \
          -type uchar \
          -endfor \
      -omc 3 resliced_${i}.nii.gz
done
