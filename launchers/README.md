# ReFrame Launchers

Bash scripts that activate the ReFrame conda environment and invoke the
ReFrame test runner against a specific test file and partition.  Each script
logs output to `$SCRATCH/rfm_logs/reframe.log`.

---

## Available launchers

| Script | Test class | Partition | Notes |
|--------|-----------|-----------|-------|
| `cm1_rfm.sh` | `CM1ScaleTest` | `casper:compute-oldhtc` | MPI scaling (4–32 tasks) |
| `cm1_nodetype_rfm.sh` | `CM1NodeTypeTest` | `casper:compute` | One node per CPU type |
| `cm1_rfm_rez.sh` | `CM1ScaleTest` | `casper:compute` | Scaling test via reservation queue (`-q system`) |
| `cm1_targeted_rfm.sh` | `CM1NodeTypeTest` / `CM1NodeTypeMultiTest` | `casper:compute` | Targeted runs — see below |
| `mg2_rfm.sh` | `Mg2ProdTest` | `casper:compute` | MG2 production run |
| `mg2_rfm_rez.sh` | `Mg2ProdTest` | `casper:compute` | MG2 via reservation queue |
| `fasteddy_rfm.sh` | `FastEddyLongMultiGPUTest` | `casper:gpu-mpi` | FastEddy multi-GPU |
| `fasteddy_rfm_rez.sh` | `FastEddyMultiGPUTest` | `casper:gpu-mpi` | FastEddy via reservation queue |

---

## Core ReFrame CLI flags used in launchers

```
-C <config.py>       Site configuration file (systems, environments, resources)
-c <test_file.py>    Test file to load
-n <regex>           Filter tests/variants by name (matches against full variant name)
-p <regex>           Filter by programming environment name (e.g. -p gnu, -p intel)
--system <sys:part>  Target system and partition (e.g. casper:compute, casper:gpu-mpi)
-S Class.var=value   Override a variable() field in a test class at runtime
-J OPT               Append a raw PBS option to every job submitted in this run
--purge-env          Unload all modules before setting up the test environment
-r                   Run (execute) the selected tests
-l                   List matching tests without running
```

---

## Targeting specific resources

Tests that use `CM1NodeTypeTest`, `CM1NodeTypeMultiTest`, or the generic
`MPIAppNodeTypeTest` / `MPIAppNodeTypeMultiTest` from `tests/mpi/mpi_tests.py`
support three layers of resource targeting.

### Layer 1 — Select node type and node count with `-n`, compiler with `-p`

ReFrame names parameter variants using `%param=value` notation:

```
CM1NodeTypeTest %node_type=cascadelake
CM1NodeTypeMultiTest %node_type=cascadelake %num_nodes=2
```

The programming environment (`gnu`, `intel`) is **not** part of the test name —
use `-p` to filter by compiler.

| Want to filter by | Use |
|---|---|
| node type / cpu_type | `-n 'ClassName.*node_type=cascadelake'` |
| node count | `-n 'ClassName.*num_nodes=2'` |
| compiler / environment | `-p gnu` (separate flag, **not** inside `-n`) |

```bash
# All cascadelake variants (both gnu and intel)
-n 'CM1NodeTypeTest.*node_type=cascadelake'

# Cascadelake, gnu compiler only
-n 'CM1NodeTypeTest.*node_type=cascadelake' -p gnu

# Multi-node test: 4-node cascadelake variants only
-n 'CM1NodeTypeMultiTest.*node_type=cascadelake.*num_nodes=4'

# Multi-node test: 2-node variants, all node types
-n 'CM1NodeTypeMultiTest.*num_nodes=2'

# Multi-node test: 2-node genoa, intel compiler
-n 'CM1NodeTypeMultiTest.*node_type=genoa.*num_nodes=2' -p intel
```

> **Rule:** use `-n` for `node_type` and `num_nodes`; use `-p` for compiler.

---

### Layer 2 — Pin hostname or override memory with `-S`

`CM1BaseTest` (and `MPIAppBaseTest`) expose two optional `variable()` fields
that are empty by default and can be set from the launcher:

| Variable | PBS chunk effect | Example |
|----------|-----------------|---------|
| `target_hostname` | `:host=<name>` | `-S 'CM1NodeTypeTest.target_hostname=crhtc53'` |
| `target_mem` | `:mem=<value>` | `-S 'CM1NodeTypeTest.target_mem=200GB'` |

```bash
# Cascadelake gnu variant pinned to a specific node
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
    -p gnu \
    -S 'CM1NodeTypeTest.target_hostname=crhtc53' \
    --system casper:compute -r

# Genoa variants with an explicit memory limit
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeTest.*node_type=genoa' \
    -S 'CM1NodeTypeTest.target_mem=500GB' \
    --system casper:compute -r
```

Multiple `-S` flags are allowed in one invocation:

```bash
-S 'CM1NodeTypeTest.target_hostname=crhtc53' \
-S 'CM1NodeTypeTest.target_mem=200GB'
```

---

### Layer 3 — PBS-level options with `-J`

Applies a raw PBS flag to **every** job submitted in the run.  Useful for
queues, reservations, and wallclock overrides.

```bash
# Submit via the system reservation queue
-J '-q system'

# Submit into a named reservation
-J '-q R1234567'

# Extend the wallclock for all jobs
-J '-l walltime=02:00:00'
```

---

## Combining all three layers — examples

```bash
# 1. All CPU node types, all compilers (default sweep)
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n CM1NodeTypeTest \
    --system casper:compute -r

# 2. One node type, both compilers
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
    --system casper:compute -r

# 3. One node type, gnu compiler only
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
    -p gnu \
    --system casper:compute -r

# 4. One node type + pinned hostname, gnu only
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeTest.*node_type=cascadelake' \
    -p gnu \
    -S 'CM1NodeTypeTest.target_hostname=crhtc53' \
    --system casper:compute -r

# 5. One node type + memory override + reservation queue
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeTest.*node_type=genoa' \
    -S 'CM1NodeTypeTest.target_mem=500GB' \
    -J '-q system' \
    --system casper:compute -r

# 6. Multi-node, 4 nodes, cascadelake, gnu only
./bin/reframe -C config.py -c tests/cm1/cm1_tests.py \
    -n 'CM1NodeTypeMultiTest.*node_type=cascadelake.*num_nodes=4' \
    -p gnu \
    --system casper:compute -r

# 7. GPU test via reservation queue
./bin/reframe -C config.py -c tests/fasteddy/fasteddy_tests.py \
    -n FastEddyMultiGPUTest \
    -J '-q system' \
    --system casper:gpu-mpi -r --purge-env
```

> All examples assume you have run `module load conda && conda activate
> /glade/work/bneuman/conda-envs/reframe` and changed directory to
> `/glade/work/bneuman/reframe_ncar/reframe` first, as the launcher scripts
> do automatically.

---

## Available partitions

| Partition | Launcher flag | Use for |
|-----------|--------------|---------|
| `casper:compute` | `--system casper:compute` | CPU MPI jobs (gnu, intel) |
| `casper:compute-serial` | `--system casper:compute-serial` | Single-core CPU jobs (gnu-serial) |
| `casper:gpu` | `--system casper:gpu` | Single-GPU jobs (cuda, cuda-last, cuda-dev) |
| `casper:gpu-mpi` | `--system casper:gpu-mpi` | Multi-GPU MPI jobs (cuda, cuda-last, cuda-dev) |

---

## Adding a new launcher

Copy the closest existing script and change:
1. The `-c` path to your test file
2. The `-n` filter to your test class name
3. The `--system` partition if needed
4. Add `-p`, `-S`, `-J`, or `-n` filters for targeting

Use `cm1_targeted_rfm.sh` as a reference — it has all selection mechanisms
documented and ready to uncomment.
