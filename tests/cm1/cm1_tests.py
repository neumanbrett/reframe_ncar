"""
Simple CM1 Test Suite - Compilation and Quick Validation Only

This simplified test suite contains four test classes:

1. CM1FullTest           - Verify CM1 compiles and runs on any available compute node
2. CM1NodeTypeTest       - Parameterized test targeting each CPU node type discovered
                           dynamically via ``pbsnodes -a`` (one node per type)
3. CM1NodeTypeMultiTest  - Same node-type parameterisation but with a configurable
                           node count (parameter: ``num_nodes``).  Use this when you
                           want to run the same workload across 2, 4, … nodes of a
                           given type.
4. CM1ScaleTest          - Scaling test across MPI task counts (4/8/16/32) on a
                           single cascadelake node

Node types are discovered at import time by querying ``pbsnodes -a`` through
``pbsnodes.py``.  No manual registry maintenance is needed — new node types
appear automatically.

How system/node filtering works
--------------------------------
ReFrame instantiates test classes at load time before ``current_system`` is
set (that happens at the 'setup' stage).  The parameter lists are built once
at import time from the live ``pbsnodes`` query.  The ``skip_if_not_applicable``
hook (``@run_after('setup')``) drops any variant whose label is absent from
the live registry, which is the earliest point where ``current_system`` is
available.
"""

import reframe as rfm
import reframe.utility.sanity as sn

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pbsnodes

cm1_base_dir = '/glade/work/bneuman/reframe_apps/cm1/cm1r21.1_base'


# ============================================================================
# BASE TEST CLASS
# ============================================================================

class CM1BaseTest(rfm.RegressionTest):
    """Base class for CM1 tests with common configuration.
    Works across all nodes of each system. Compiles and runs the application.
    """

    valid_systems = ['casper:compute', 'derecho:compute']
    valid_prog_environs = ['gnu', 'intel']

    cm1_source_dir = variable(str, value='/glade/work/bneuman/reframe_apps/cm1/cm1r21.1_base')
    build_system = 'Make'

    # Optional resource overrides — set from the launcher with -S or left empty
    # to accept node-type defaults from pbsnodes.
    #   -S 'CM1NodeTypeTest.target_hostname=crhtc53'   pin to a specific node
    #   -S 'CM1NodeTypeTest.target_mem=200GB'          override memory request
    target_hostname = variable(str, value='')
    target_mem      = variable(str, value='')

    def _setup_compiler_flags(self):
        """Configure compiler flags for the current system and environment.
        Called from setup_build_environment in each subclass.
        """
        if self.current_system.name in ('casper', 'derecho'):
            if self.current_environ.name == 'gnu':
                self.build_system.cppflags = [
                    'cpp', '-C', '-P', '-traditional',
                    '-Wno-invalid-pp-token', '-ffreestanding'
                ]
                self.build_system.options = [
                    'OPTS="-ffree-form -ffree-line-length-none -O2 -finline-functions -fallow-argument-mismatch"',
                    'DM="-DMPI"'
                ]
            elif self.current_environ.name == 'intel':
                self.build_system.cppflags = [
                    '-O3', '-ip', '-assume byterecl',
                    '-fp-model precise', '-ftz', '-no-fma'
                ]
                self.build_system.options = [
                    'OPTS="-O3 -ip -assume byterecl -fp-model precise -ftz -no-fma"',
                    'DM="-DMPI"'
                ]
            self.build_system.ldflags = ['-lnetcdf']


# ============================================================================
# COMPILE AND RUN TEST (any node)
# ============================================================================
@rfm.simple_test
class CM1FullTest(CM1BaseTest):
    """Test that CM1 compiles and runs successfully on any available compute node"""

    descr = 'CM1 compile and run test'
    tags = {'compile_run', 'core'}

    valid_systems = ['casper:compute', 'derecho:compute']
    valid_prog_environs = ['gnu', 'intel']

    sourcesdir = '.'
    executable = 'cm1.exe'

    num_tasks = 8
    num_tasks_per_node = 8
    time_limit = '15m'

    @run_before('compile')
    def setup_build_environment(self):
        """Set up build environment for CM1"""
        self.build_system.max_concurrency = 8
        self.prebuild_cmds = [
            f'cp -r {self.cm1_source_dir}/src .',
            f'cp -r {self.cm1_source_dir}/run .',
            'cd src',
            'make clean'
        ]
        self._setup_compiler_flags()

    prerun_cmds = [f'cd {cm1_base_dir}/run']

    @run_after('run')
    def wait_for_completion(self):
        import time
        time.sleep(60)

    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'approximate core-hours',
            self.stdout,
            msg='CM1 did not terminate normally'
        )

    @performance_function('s')
    def total_time(self):
        """Extract total simulation time in seconds"""
        return sn.extractsingle(
            r'Total time:\s+(\S+)',
            self.stdout,
            1,
            float
        )


# ============================================================================
# PER-NODE-TYPE TESTS
#
# Both tests are parameterised over CPU-only node type labels discovered
# dynamically from ``pbsnodes -a`` at import time via ``pbsnodes.py``.
# No manual registry edits are needed when new node types appear.
#
# How filtering works:
#   1. valid_systems limits instantiated variants to recognised systems.
#   2. skip_if_not_applicable() fires at @run_after('setup') — the earliest
#      stage where current_system is available — and calls self.skip() for
#      any label absent from the live pbsnodes registry.
#
# CM1NodeTypeTest      — 1 node per type (PBS picks any available node of
#                        that cpu_type; good for broad coverage sweeps)
# CM1NodeTypeMultiTest — same, but ``num_nodes`` is a parameter so you can
#                        run the workload across 2, 4, … nodes of each type
# ============================================================================

# Build the CPU node type label list once at import time from live pbsnodes.
_cpu_node_specs  = pbsnodes.get_cpu_node_types()   # dict[label, NodeTypeSpec]
_all_cpu_node_labels = sorted(_cpu_node_specs.keys())


@rfm.simple_test
class CM1NodeTypeTest(CM1BaseTest):
    """Compile and run CM1 on each CPU node type discovered via pbsnodes.

    One variant is generated per (node_type x compiler environment).
    PBS targets the node type via ``cpu_type=<label>`` so any available
    node of that type satisfies the request.
    """

    descr = 'CM1 compile and run test per system node type (1 node)'
    tags = {'compile_run', 'core', 'node_type'}

    valid_systems = ['casper:compute', 'derecho:compute']
    valid_prog_environs = ['gnu', 'intel']

    sourcesdir = '.'
    executable = 'cm1.exe'

    node_type = parameter(_all_cpu_node_labels)

    time_limit = '15m'

    @run_after('setup')
    def skip_if_not_applicable(self):
        """Skip variants whose node_type label is absent from the live registry."""
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            self.skip(f'node_type={self.node_type!r} not found in pbsnodes registry')

    @run_after('setup')
    def set_job_resources(self):
        """Configure task counts and PBS chunk resources for this node type.

        Applies target_hostname and target_mem overrides when set via -S.
        """
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return

        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.num_tasks          = spec.tasks
        self.num_tasks_per_node = spec.tasks
        self.num_nodes          = 1

        resources = {}
        if spec.cpu_type is not None:
            resources['cpu_type'] = {'cpu_type': spec.cpu_type}
        if self.target_mem:
            resources['mem'] = {'mem': self.target_mem}
        if self.target_hostname:
            resources['host'] = {'hostname': self.target_hostname}
        if resources:
            self.extra_resources = resources

    @run_before('compile')
    def setup_build_environment(self):
        """Set up build environment for CM1."""
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return

        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.build_system.max_concurrency = spec.tasks
        self.prebuild_cmds = [
            f'cp -r {self.cm1_source_dir}/src .',
            f'cp -r {self.cm1_source_dir}/run .',
            'cd src',
            'make clean'
        ]
        self._setup_compiler_flags()

    prerun_cmds = [f'cd {cm1_base_dir}/run']

    @run_after('run')
    def wait_for_completion(self):
        import time
        time.sleep(60)

    @sanity_function
    def validate_output(self):
        return sn.assert_found(
            r'approximate core-hours',
            self.stdout,
            msg='CM1 did not terminate normally'
        )

    @performance_function('s')
    def total_time(self):
        return sn.extractsingle(
            r'Total time:\s+(\S+)',
            self.stdout,
            1,
            float
        )


# ============================================================================
# PER-NODE-TYPE MULTI-NODE TEST
# ============================================================================

@rfm.simple_test
class CM1NodeTypeMultiTest(CM1BaseTest):
    """Compile and run CM1 on N nodes of each CPU node type.

    Parameterised over both ``node_type`` (all CPU types from pbsnodes) and
    ``num_nodes`` (selectable node count).  PBS targets the node type via
    ``cpu_type=<label>`` and requests ``num_nodes`` chunks, so the scheduler
    can satisfy the request with any available nodes of that type.

    The default ``num_nodes`` values are ``[2, 4]``.  Override on the command
    line with ``-S CM1NodeTypeMultiTest.num_nodes=8`` if needed.
    """

    descr = 'CM1 compile and run test per node type — configurable node count'
    tags = {'compile_run', 'core', 'node_type', 'multi_node'}

    valid_systems = ['casper:compute', 'derecho:compute']
    valid_prog_environs = ['gnu', 'intel']

    sourcesdir = '.'
    executable = 'cm1.exe'

    node_type = parameter(_all_cpu_node_labels)
    num_nodes = parameter([2, 4])

    time_limit = '30m'

    @run_after('setup')
    def skip_if_not_applicable(self):
        """Skip variants whose node_type label is absent from the live registry."""
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            self.skip(f'node_type={self.node_type!r} not found in pbsnodes registry')

    @run_after('setup')
    def set_job_resources(self):
        """Configure task counts and PBS chunk resources for this node type.

        Applies target_hostname and target_mem overrides when set via -S.
        """
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return

        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.num_tasks_per_node = spec.tasks
        self.num_tasks          = spec.tasks * self.num_nodes

        resources = {}
        if spec.cpu_type is not None:
            resources['cpu_type'] = {'cpu_type': spec.cpu_type}
        if self.target_mem:
            resources['mem'] = {'mem': self.target_mem}
        if self.target_hostname:
            resources['host'] = {'hostname': self.target_hostname}
        if resources:
            self.extra_resources = resources

    @run_before('compile')
    def setup_build_environment(self):
        """Set up build environment for CM1."""
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return

        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.build_system.max_concurrency = spec.tasks
        self.prebuild_cmds = [
            f'cp -r {self.cm1_source_dir}/src .',
            f'cp -r {self.cm1_source_dir}/run .',
            'cd src',
            'make clean'
        ]
        self._setup_compiler_flags()

    prerun_cmds = [f'cd {cm1_base_dir}/run']

    @run_after('run')
    def wait_for_completion(self):
        import time
        time.sleep(60)

    @sanity_function
    def validate_output(self):
        return sn.assert_found(
            r'approximate core-hours',
            self.stdout,
            msg='CM1 did not terminate normally'
        )

    @performance_function('s')
    def total_time(self):
        return sn.extractsingle(
            r'Total time:\s+(\S+)',
            self.stdout,
            1,
            float
        )


# ============================================================================
# SCALING TEST  (single node, cascadelake, 4/8/16/32 MPI tasks)
# ============================================================================
@rfm.simple_test
class CM1ScaleTest(CM1BaseTest):
    """Test CM1 scaling from 4 to 32 MPI tasks on a single Cascade Lake node"""

    descr = 'CM1 compile and run scaling test 1-32 CPUs single node'
    tags = {'compile_run', 'core', 'scaling'}

    valid_systems = ['casper:compute']
    valid_prog_environs = ['gnu', 'intel']

    sourcesdir = '.'
    executable = 'cm1.exe'

    scale = parameter([4, 8, 16, 32])
    time_limit = '15m'

    # Pin scaling baseline to cascadelake for a consistent comparison point
    extra_resources = {
        'cpu_type': {'cpu_type': 'cascadelake'}
    }

    @run_after('init')
    def set_num_tasks(self):
        self.num_nodes          = 1
        self.num_tasks_per_node = self.scale
        self.num_tasks          = self.scale

    @run_before('compile')
    def setup_build_environment(self):
        """Set up build environment for CM1"""
        self.build_system.max_concurrency = self.scale
        self.prebuild_cmds = [
            f'cp -r {self.cm1_source_dir}/src .',
            f'cp -r {self.cm1_source_dir}/run .',
            'cd src',
            'make clean'
        ]
        self._setup_compiler_flags()

    prerun_cmds = [f'cd {cm1_base_dir}/run']

    @run_after('run')
    def wait_for_completion(self):
        import time
        time.sleep(60)

    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'approximate core-hours',
            self.stdout,
            msg='CM1 did not terminate normally'
        )

    @performance_function('s')
    def total_time(self):
        """Extract total simulation time in seconds"""
        return sn.extractsingle(
            r'Total time:\s+(\S+)',
            self.stdout,
            1,
            float
        )