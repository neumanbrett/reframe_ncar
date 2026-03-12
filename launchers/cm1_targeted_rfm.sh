#!/bin/bash
# =============================================================================
# cm1_targeted_rfm.sh — Targeted CM1 ReFrame launcher
#
# Demonstrates the three mechanisms for narrowing a ReFrame run to specific
# node types, hostnames, memory amounts, or node counts:
#
#   1. -n <regex>         Select parameter variants by test name pattern.
#                         ReFrame names variants as:
#                           ClassName %param1=val1 %param2=val2
#                         e.g. "CM1NodeTypeMultiTest %node_type=cascadelake %num_nodes=2"
#                         Use .*param=value in the regex to match a specific value.
#
#   2. -p <regex>         Filter by programming environment (compiler).
#                         e.g. -p gnu   or   -p intel
#                         Do NOT put the env name inside the -n pattern.
#
#   3. -S Class.var=val   Override a variable() field at runtime.
#                         target_hostname and target_mem are variables — they
#                         CAN be set here to add PBS chunk selectors.
#
#   4. -J OPT             Append a raw PBS option to every job in this run.
#                         (use for queue, reservation, wallclock, etc.)
#
# USAGE
# -----
#   Edit the SELECTION SECTION below, then run:
#       bash launchers/cm1_targeted_rfm.sh
#
# =============================================================================

reframe_basedir=/glade/work/bneuman/reframe_ncar/reframe
reframe_testdir=/glade/work/bneuman/reframe_ncar/tests
reframe_configdir=/glade/work/bneuman/reframe_ncar
reframe_logdir=/glade/derecho/scratch/$USER/rfm_logs

reframe_condaenv=/glade/work/bneuman/conda-envs/reframe

ml conda
conda activate ${reframe_condaenv}

cd $reframe_basedir
mkdir -p ${reframe_logdir}

# =============================================================================
# RUN BLOCKS — uncomment the scenario you want
# =============================================================================

TEST_FILE=$reframe_testdir/cm1/cm1_tests.py

# --- Scenario A: All CPU node types, all compiler variants (default sweep) ---
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n CM1NodeTypeTest \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario B: One node type (cascadelake), both compilers -----------------
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario C: One node type (cascadelake), gnu compiler only --------------
#  Use -p to filter by programming environment; do NOT put 'gnu' in -n.
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
#    -p gnu \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario D: Pin to a specific hostname, gnu only ------------------------
#  target_hostname adds ':host=<name>' to the PBS select chunk.
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
#    -p gnu \
#    -S 'CM1NodeTypeTest.target_hostname=crhtc53' \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario E: Override memory on one node type ----------------------------
#  target_mem adds ':mem=<value>' to the PBS select chunk.
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
#    -S 'CM1NodeTypeTest.target_mem=200GB' \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario F: Multi-node — 2 cascadelake nodes, gnu compiler only ---------
#  Variant name: "CM1NodeTypeMultiTest %node_type=cascadelake %num_nodes=2"
./bin/reframe \
    -C $reframe_configdir/config.py \
    -c $TEST_FILE \
    -n 'CM1NodeTypeMultiTest.*node_type=cascadelake.*num_nodes=2' \
    -p gnu \
    --system casper:compute \
    -r | tee $reframe_logdir/reframe.log

# --- Scenario G: Multi-node — 4 cascadelake nodes, both compilers ------------
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n 'CM1NodeTypeMultiTest.*node_type=cascadelake.*num_nodes=4' \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario H: Multi-node with memory override and reservation queue -------
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n 'CM1NodeTypeMultiTest.*node_type=genoa.*num_nodes=2' \
#    -S 'CM1NodeTypeMultiTest.target_mem=500GB' \
#    -J '-q system' \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log

# --- Scenario I: All node types with reservation queue ----------------------
#./bin/reframe \
#    -C $reframe_configdir/config.py \
#    -c $TEST_FILE \
#    -n CM1NodeTypeTest \
#    -J '-q system' \
#    --system casper:compute \
#    -r | tee $reframe_logdir/reframe.log
