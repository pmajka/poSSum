#!/bin/bash -xe

#TODO: Describe the purpose of this file

#clear
cat <<InputComesFromHERE
                 _____ _____                 
                / ____/ ____|                
     _ __   ___| (___| (___  _   _ _ __ ___  
    | '_ \ / _  \___  \___ \| | | | '_ \ _ \ 
    | |_) | (_) |___) |___) | |_| | | | | | |
    | .__/ \___/_____/_____/ \__,_|_| |_| |_|
    | |                                      
    |_|  Piotr Majka <p.majka@nencki.gov.pl>

      Volumetric reconstruction framework
      Framework version: ${possum_version}

Type possum_test to conduct a basic sanity checks
of the famework.

You can find the most recent code snapshot on:
https://github.com/pmajka/poSSum

You can find the most recent version of the VM on:
xxxx
InputComesFromHERE

# One should append the lines below to the .bashrc file

#   function possum_test {

#   echo ""
#   echo ".------------------------------------------."
#   echo "|         Conducting the tests             |"
#   echo "*------------------------------------------*"
#   echo ""

#   cd ${possum_dir}
#   python setup.py test
#   cd 
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
