#!/bin/bash -xe

clear
cat <<InputComesFromHERE
                 _____ _____                 
                / ____/ ____|                
     _ __   ___| (___| (___  _   _ _ __ ___  
    | '_ \ / _  \___  \___ \| | | | '_ \ _ \ 
    | |_) | (_) |___) |___) | |_| | | | | | |
    | .__/ \___/_____/_____/ \__,_|_| |_| |_|
    | |                                      
    |_|  Piotr Majka <p.majka@nencki.gov.pl>

      Volumetric Reconstruction Framework
      version. ${possum_version}

Type possum_test to conduct a basic sanity checks
of the famework.
You can find the most recent code snapshot on:
https://github.com/pmajka/poSSum
To update the code to the most recent developmental
version simply type: possum_update .
You can find the most recent version of the VM on:
http://doc.3dbar.org/possum/possum_vm.tgz

InputComesFromHERE

##One should append the lines below to the ~/.bashrc, ~./.bash_profile or ~/.profile files
##cat .possum_vm_welcome_screen.sh | grep '#'  | tail -n +2 | sed 's/^.//'

#   function possum_test {

#       echo ""
#       echo ".------------------------------------------."
#       echo "|         Conducting the tests             |"
#       echo "*------------------------------------------*"
#       echo ""

#       cd ${possum_dir}
#       python setup.py test
#       cd 
#   }


#   function possum_update {

#       cd ${possum_dir}
#       git pull origin && git checkout develop
#       cd 
#   }


#   function possum_build_examples {
#       echo "Note that bulding the examples may take"
#       echo "up to serveral hours depending on the VM settings."
#       echo "Press C-c to break."
#       sleep 1 && echo "5"
#       sleep 1 && echo "4"
#       sleep 1 && echo "3"
#       sleep 1 && echo "2"
#       sleep 1 && echo "1"
#       sleep 1 && echo "0"

#       cd ${possum_dir}/test/test_stack_sections/
#       make clean && make

#       cd ${possum_dir}/test/test_slice_preprocess/
#       bash test_slice_preprocess.sh

#       cd ${possum_dir}/test/test_pos_reorder_volume/
#       make -i

#       cd ${possum_dir}/test/test_pos_pairwise_alignment_rigid/
#       bash test_pos_pairwise_alignment_rigid.sh

#       cd ${possum_dir}/test/test_pos_pairwise_alignment_ellipses/
#       bash test_pos_pairwise_alignment_ellipses.sh 

#       cd ${possum_dir}/test/test_banana_pairwise/
#       make

#       cd ${possum_dir}/test/test_banana_effect/
#       make

#       cd ${possum_dir}/test/test_bananas_and_graphs/
#       make

#       cd
#   }


#   if [ -e ${HOME}/.possum_cache ]
#   then
#       possum_vm_filename=`cat ${HOME}/.possum_cache`
#   else
#       find ${HOME} ~ -name .possum_vm_welcome_screen.sh | head -n 1 > ${HOME}/.possum_cache
#       possum_vm_filename=`cat ${HOME}/.possum_cache`
#   fi

#   possum_dir=`dirname ${possum_vm_filename}`
#   possum_version=`grep __version__ ${possum_dir}/possum/__init__.py | cut -f2 -d = | tr -d " '"`
#   source ${possum_vm_filename}
#   cd ${possum_dir} && source setenv.sh && cd
