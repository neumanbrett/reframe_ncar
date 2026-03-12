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
 
./bin/reframe -C $reframe_configdir/config.py -c $reframe_testdir/cm1/cm1_tests.py -n CM1NodeTypeTest --system casper:compute -r | tee $reframe_logdir/reframe.log
