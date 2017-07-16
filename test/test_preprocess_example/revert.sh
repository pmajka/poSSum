#!/bin/bash

# This script is to be executed from the Makefile only

git --version;
GIT_IS_AVAILABLE=${?};
if [ ${GIT_IS_AVAILABLE} -eq 0 ];
then
    git checkout test_case.xls test_case_processed.pickle test_case_processed.xls header.sh
fi;


