#!/bin/bash

reframe_basedir=/glade/work/bneuman/reframe_ncar/reframe
reframe_testdir=/glade/work/bneuman/reframe_ncar/tests
reframe_configdir=/glade/work/bneuman/reframe_ncar
reframe_logdir=/glade/derecho/scratch/$USER/rfm_logs

reframe_condaenv=/glade/work/bneuman/conda-envs/reframe

ml conda
conda activate ${reframe_condaenv}

cd $reframe_basedir
mkdir -P ${reframe_logdir}
 
./bin/reframe -C $reframe_configdir/config.py -c $reframe_testdir/mg2/mg2_tests.py -n Mg2ProdTest --system casper:compute -r --purge-env | tee $reframe_logdir/reframe.log