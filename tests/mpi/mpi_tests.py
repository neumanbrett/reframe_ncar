"""
Generic MPI Application Test Template
======================================

Copy this file to ``tests/<your_app>/<your_app>_tests.py`` and follow the
FIXME markers to adapt it for your application.  The node-type infrastructure
(dynamic discovery, NodeTypeTest, NodeTypeMultiTest) is ready to use as-is.

Quick-start checklist
---------------------
1. Rename the three classes: replace ``MPIApp`` with your application name
   (e.g. ``WRF``, ``MPAS``, ``CESM``).
2. In ``MPIAppBaseTest``:
   a. Set ``app_source_dir`` to your application's source/install path.
   b. Set ``executable`` to your binary name.
   c. Fill in ``setup_build_environment()`` with your compile commands.
   d. Fill in ``prerun_cmds`` with any pre-execution setup.
3. In ``MPIAppNodeTypeTest`` and ``MPIAppNodeTypeMultiTest``:
   a. Update ``valid_prog_environs`` if you only support one compiler.
   b. Update ``time_limit`` to match your workload.
4. Replace the placeholder ``validate_output()`` regex with a string that
   appears in your application's stdout when it completes successfully.
5. Replace the placeholder ``total_time()`` regex with the timing line
   your application prints.

Runtime resource overrides (via launcher -S flags)
---------------------------------------------------
Both node-type tests inherit two optional override variables from the base
class.  Leave them empty (the default) to accept node-type defaults from
pbsnodes.  Set them from the launcher to create targeted runs:

    # Pin to a specific node
    -S 'MPIAppNodeTypeTest.target_hostname=crhtc53'

    # Override the memory allocation
    -S 'MPIAppNodeTypeTest.target_mem=200GB'

Selecting which variants to run (via launcher -n flag)
------------------------------------------------------
ReFrame names parameter variants as ``ClassName_paramval_envname``.
Use ``-n`` with a regex to select subsets:

    # All cascadelake variants
    -n 'MPIAppNodeTypeTest.*cascadelake'

    # Only gnu compiler variants on genoa nodes
    -n 'MPIAppNodeTypeTest.*genoa.*gnu'

    # Multi-node test: only 4-node variants on cascadelake
    -n 'MPIAppNodeTypeMultiTest.*cascadelake.*4'
"""

import reframe as rfm
import reframe.utility.sanity as sn

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import pbsnodes


# =============================================================================
# BASE CLASS — customise your application details here
# =============================================================================

class MPIAppBaseTest(rfm.RegressionTest):
    """Base class for a generic MPI application.

    Subclasses (MPIAppNodeTypeTest, MPIAppNodeTypeMultiTest) inherit all
    settings defined here and add the node-type parameterisation on top.
    """

    # --- Target systems and compiler environments ----------------------------
    valid_systems      = ['casper:compute', 'derecho:compute']
    valid_prog_environs = ['gnu', 'intel']   # FIXME: narrow if needed

    # --- Application paths ---------------------------------------------------
    # FIXME: point to your application's source or install directory
    app_source_dir = variable(str, value='/path/to/your/application')

    build_system = 'Make'                    # FIXME: or 'CMake', 'Autotools', etc.
    sourcesdir   = '.'
    executable   = 'your_app.exe'           # FIXME: your binary name

    # --- Optional PBS resource overrides (set via -S from the launcher) ------
    # Leave as '' to use the node-type defaults from pbsnodes.
    #   -S 'MPIAppNodeTypeTest.target_hostname=crhtc53'
    #   -S 'MPIAppNodeTypeTest.target_mem=200GB'
    target_hostname = variable(str, value='')
    target_mem      = variable(str, value='')

    # -------------------------------------------------------------------------
    # FIXME: configure your compiler-specific build flags here.
    # Called from setup_build_environment() in subclasses.
    # -------------------------------------------------------------------------
    def _setup_compiler_flags(self):
        if self.current_environ.name == 'gnu':
            self.build_system.options = [
                'OPTS="-O2 -ffree-form -ffree-line-length-none"',
                'DM="-DMPI"',
            ]
        elif self.current_environ.name == 'intel':
            self.build_system.options = [
                'OPTS="-O3 -ip"',
                'DM="-DMPI"',
            ]
        # FIXME: add linker flags if needed, e.g.:
        # self.build_system.ldflags = ['-lnetcdf', '-lhdf5']

    # -------------------------------------------------------------------------
    # Helper: build the extra_resources dict from a NodeTypeSpec plus any
    # overrides.  Shared by both node-type test subclasses.
    # -------------------------------------------------------------------------
    def _build_extra_resources(self, spec) -> dict:
        """Return an extra_resources dict for *spec*, applying overrides."""
        resources = {}
        if spec.cpu_type is not None:
            resources['cpu_type'] = {'cpu_type': spec.cpu_type}
        if self.target_mem:
            resources['mem'] = {'mem': self.target_mem}
        if self.target_hostname:
            resources['host'] = {'hostname': self.target_hostname}
        return resources


# =============================================================================
# PER-NODE-TYPE TEST  (1 node per type, PBS picks any available node)
# =============================================================================

# Build CPU node type label list once at import time from live pbsnodes.
_cpu_node_specs      = pbsnodes.get_cpu_node_types()
_all_cpu_node_labels = sorted(_cpu_node_specs.keys())


@rfm.simple_test
class MPIAppNodeTypeTest(MPIAppBaseTest):
    """Compile and run the MPI application on each CPU node type.

    One variant per (node_type x compiler).  PBS targets the node type with
    ``cpu_type=<label>`` so any available node of that type satisfies the
    request.  Useful for a broad coverage sweep across all node types.
    """

    descr = 'MPI app compile and run — one node per type'
    tags  = {'compile_run', 'node_type'}

    node_type  = parameter(_all_cpu_node_labels)
    time_limit = '30m'    # FIXME: adjust to your workload

    @run_after('setup')
    def skip_if_not_applicable(self):
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            self.skip(f'node_type={self.node_type!r} not in pbsnodes registry')

    @run_after('setup')
    def set_job_resources(self):
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return
        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.num_tasks_per_node = spec.tasks
        self.num_tasks          = spec.tasks
        self.num_nodes          = 1
        resources = self._build_extra_resources(spec)
        if resources:
            self.extra_resources = resources

    @run_before('compile')
    def setup_build_environment(self):
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return
        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.build_system.max_concurrency = spec.tasks

        # FIXME: replace with your application's build steps
        self.prebuild_cmds = [
            f'cp -r {self.app_source_dir}/src .',
            'cd src',
            'make clean',
        ]
        self._setup_compiler_flags()

    # FIXME: replace with your application's pre-run setup
    # prerun_cmds = ['cd run', 'cp namelist.input.default namelist.input']

    @sanity_function
    def validate_output(self):
        # FIXME: replace with a string your application prints on success
        return sn.assert_found(
            r'FIXME_SUCCESS_PATTERN',
            self.stdout,
            msg='Application did not complete successfully',
        )

    @performance_function('s')
    def total_time(self):
        # FIXME: replace with your application's timing output pattern.
        # Group 1 must capture the numeric value.
        return sn.extractsingle(
            r'Total time:\s+(\S+)',
            self.stdout,
            1,
            float,
        )


# =============================================================================
# PER-NODE-TYPE MULTI-NODE TEST  (N nodes per type, configurable)
# =============================================================================

@rfm.simple_test
class MPIAppNodeTypeMultiTest(MPIAppBaseTest):
    """Compile and run the MPI application across N nodes of each CPU type.

    Parameterised over both ``node_type`` and ``num_nodes``.  PBS targets the
    type with ``cpu_type=<label>`` and requests ``num_nodes`` chunks.

    Default ``num_nodes`` values are ``[2, 4]``.  To run with a different
    count without editing this file, pass it from the launcher:

        -n 'MPIAppNodeTypeMultiTest.*cascadelake' -S 'MPIAppNodeTypeMultiTest.num_nodes=8'

    Note: ``-S`` cannot override a ``parameter()``; to use a single custom
    value, filter to one variant with ``-n`` and set a ``variable()`` instead.
    For ad-hoc node counts, copy this class and change ``num_nodes`` from
    ``parameter([2, 4])`` to ``variable(int, value=8)``.
    """

    descr = 'MPI app compile and run — configurable node count per type'
    tags  = {'compile_run', 'node_type', 'multi_node'}

    node_type  = parameter(_all_cpu_node_labels)
    num_nodes  = parameter([2, 4])           # FIXME: adjust default node counts
    time_limit = '60m'                       # FIXME: adjust to your workload

    @run_after('setup')
    def skip_if_not_applicable(self):
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            self.skip(f'node_type={self.node_type!r} not in pbsnodes registry')

    @run_after('setup')
    def set_job_resources(self):
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return
        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.num_tasks_per_node = spec.tasks
        self.num_tasks          = spec.tasks * self.num_nodes
        resources = self._build_extra_resources(spec)
        if resources:
            self.extra_resources = resources

    @run_before('compile')
    def setup_build_environment(self):
        if self.node_type not in pbsnodes.NODE_TYPE_SPECS:
            return
        spec = pbsnodes.NODE_TYPE_SPECS[self.node_type]
        self.build_system.max_concurrency = spec.tasks

        # FIXME: replace with your application's build steps
        self.prebuild_cmds = [
            f'cp -r {self.app_source_dir}/src .',
            'cd src',
            'make clean',
        ]
        self._setup_compiler_flags()

    # FIXME: replace with your application's pre-run setup
    # prerun_cmds = ['cd run', 'cp namelist.input.default namelist.input']

    @sanity_function
    def validate_output(self):
        # FIXME: replace with a string your application prints on success
        return sn.assert_found(
            r'FIXME_SUCCESS_PATTERN',
            self.stdout,
            msg='Application did not complete successfully',
        )

    @performance_function('s')
    def total_time(self):
        # FIXME: replace with your application's timing output pattern.
        # Group 1 must capture the numeric value.
        return sn.extractsingle(
            r'Total time:\s+(\S+)',
            self.stdout,
            1,
            float,
        )
