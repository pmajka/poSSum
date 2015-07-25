#!/bin/bash

export LC_ALL=C

#--------------------------------------------------------------------
# Check if the necessary shell commands are available

EXECUTABLES='mkdir rm cp tar ANTSJacobian ANTS WarpImageMultiTransform AverageAffineTransform AverageImages c3d c2d parallel convert awk sed'

for executable in ${EXECUTABLES}
do
    prog_path=`which $executable`
    if [ $? -ne 0 ]; then
        echo "(!) The ${executable} is not available."
        echo "(!) The environment cannot be set. Exiting."
        exit 1
    fi
done

echo "(+) All necessary shell commands are available."

#--------------------------------------------------------------------

POS_DIR=`pwd`
export PYTHONPATH=$PYTHONPATH:${POS_DIR}
export PATH=$PATH:${POS_DIR}/bin/
echo "(+) The paths are set."

source autocomplete.sh
