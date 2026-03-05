#!/bin/bash

reframe_basedir=/glade/work/bneuman/reframe_ncar/reframe
reframe_testdir=/glade/work/bneuman/reframe_ncar/tests
reframe_configdir=/glade/work/bneuman/reframe_ncar
reframe_logdir=/glade/derecho/scratch/$USER/rfm_logs

reframe_condaenv=/glade/work/bneuman/conda-envs/reframe

ml conda
conda activate ${reframe_condaenv}

cd $reframe_basedir
mkdir -p ${reframe_logdir}
 
#./bin/reframe -C $reframe_configdir/config.py -c $reframe_testdir/fasteddy/fasteddy_tests.py -n FastEddyFullTest --system casper:gpu-mpi --job-option='-q R1895362' -r --purge-env | tee $reframe_logdir/reframe.log
#./bin/reframe -C config.py -c /glade/work/bneuman/reframe/ncar/fasteddy/fasteddy_tests.py --system casper:compute -r --purge-env | tee $reframe_logdir/reframe.log
#./bin/reframe -C $reframe_configdir/config.py -c $reframe_testdir/fasteddy/fasteddy_tests.py -n FastEddyMultiGPUTest --system casper:gpu-mpi --job-option='-q R1895362' -r --purge-env | tee $reframe_logdir/reframe.log
./bin/reframe -C $reframe_configdir/config.py -c $reframe_testdir/fasteddy/fasteddy_tests.py -n FastEddyMultiGPUTest --system casper:gpu-mpi --job-option='-q system' -r --purge-env | tee $reframe_logdir/reframe.log
