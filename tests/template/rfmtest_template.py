"""
Simple Fasteddy Test Suite - Compilation and Quick Validation Only

This test suite contains two tests:
1. FasteddyCompileTest - Verify Fasteddy compiles successfully
2. FasteddyQuickTest - Quick validation run with basic checks
"""

import reframe as rfm
import reframe.utility.sanity as sn

# ============================================================================
# BASE TEST CLASS
# ============================================================================

class FastEddyBaseTest(rfm.RegressionTest):
    """Base class for Fasteddy tests with common configuration"""
    
    # Valid systems and environments
    valid_systems = ['casper:gpu-mpi']
    valid_prog_environs = ['cuda']
    
    # Fasteddy source directories
    fasteddy_source_dir = variable(str, value='/glade/work/bneuman/reframe_apps/fasteddy/fasteddy_a100')
    exe_dir = 'SRC/FEMAIN'
    data_dir = 'tutorials/examples'
    
    # Build configuration
    build_system = 'Make'
    
    sourcesdir = '.'
    executable = 'set_gpu_rank ./FastEddy'
    executable_opts = ['Example02_CBL_veryshort.in']

    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '20m'

    num_gpus_per_node = 4

    @run_before('compile')
    def setup_build_environment(self):
        
        # Unload all modules
        #self.modules.unload_all()
        #self.modules = ['-netcdf', 'netcdf-mpi/4.9.2 parallel-netcdf/1.14.0 parallelio/2.6.5 hdf5-mpi/1.12.3 ucx/1.17.0']
        # Copy source files to stage directory
        self.prebuild_cmds = [
            f'cp -r {self.fasteddy_source_dir} .',
            f'cd fasteddy_a100/{self.exe_dir}',
            'make clean',
            'module list'
        ]
    
    @run_before('run')
    def setup_run_environment(self):
        """Set up runtime environment"""
        # Unload conflict
        #self.modules.remove
        #self.modules = ['-netcdf', 'netcdf-mpi/4.9.2', 'parallel-netcdf/1.14.0', 'parallelio/2.6.5', 'hdf5-mpi/1.12.3']
        # Copy the exe and input file
        self.prerun_cmds = [
            f'cp -r fasteddy_a100/{self.exe_dir}/FastEddy .',
            f'cp -r fasteddy_a100/{self.data_dir}/Example02_CBL_veryshort.in .',
            'module list'
            #'module --force purge',
            #'module load ncarenv/24.12 nvhpc/24.11 cuda/12.3.2 ncarcompilers/1.0.0 openmpi/5.0.6 -netcdf netcdf-mpi/4.9.2 parallel-netcdf/1.14.0 parallelio/2.6.5 hdf5-mpi/1.12.3 ucx/1.17.0'
        ]

        # self.extra_resources ={
        #     'gpu_type': 'a100'
        # }
        self.job.options = [
            f'ngpus={self.num_tasks}',
            'gpu_type=a100',
            'mem=100gb'
        ]

@rfm.simple_test
class FastEddyFullTest(FastEddyBaseTest):

    valid_prog_environs = ['cuda']

    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'!!!!!	  TIMESTEP PERFORMANCE',
            self.stdout,
            msg='Fasteddy did not start a timestep'
        )
    
    @performance_function('s')
    def total_time(self):
        """Extract total test time in seconds"""
        return sn.extractsingle(
            r'^\s*(\d+\.\d+)\s+\|\s+\d+\s+\|',
            self.stdout,
            1,
            float
        )
    
    @performance_function('s')
    def time_per_step(self):
        """Extract Time/step (s) - third column"""
        return sn.extractsingle(
            r'^\s*\d+\.\d+\s+\|\s+\d+\s+\|\s+(\d+\.\d+)',
            self.stdout,
            1,
            float
        )
    
# @rfm.simple_test
# class FasteddyCompileTest(rfm.CompileOnlyRegressionTest):
#     """Test that Fasteddy compiles successfully"""
    
#     descr = 'Fasteddy compilation test'
#     tags = {'compile', 'quick', 'memory'}
    
#     sourcesdir = '.'
    
#     @run_after('setup')
#     def skip_run(self):
#         """Only compile, don't run"""
#         self.build_system.makefile = 'Makefile'
    
#     # @run_before('compile')
#     # def setup_makefile(self):
#     #     """Configure Makefile for compilation"""
#     #     self.prebuild_cmds.extend([
#     #         'make clean'
#     #     ])
    
#     @sanity_function
#     def validate_compilation(self):
#         """Check that executable was created"""
#         return sn.assert_true(
#             sn.os.path.exists('Fasteddy/fasteddy_c.exe'),
#             msg='fasteddy_c.exe not found after compilation'
#         )
    
# ============================================================================
# QUICK VALIDATION TEST
# ============================================================================

# @rfm.simple_test
# class FasteddyQuickTest(rfm.RunOnlyRegressionTest):
#     """Quick validation run with minimal configuration"""
    
#     descr = 'Fasteddy validation test'
#     tags = {'production', 'validation', 'quick', 'memory'}

#     valid_systems = ['casper:gpu']
#     valid_prog_environs = ['cuda']
    
#     # num_tasks = 4
#     # num_tasks_per_node = 4
#     # time_limit = '10m'
    
#     # @run_after('init')
#     # def set_dependencies(self):
#     #     """Depend on compilation test"""
#     #     self.depends_on('FasteddyCompileTest')

#     # @require_deps
#     # def setup_from_compile(self, FasteddyCompileTest):
#     #     """Copy executable from compile test"""
#     #     compile_dir = FasteddyCompileTest().stagedir
#     #     """Configure namelist for quick test"""
#     #     # Modify namelist.input for a quick 2D test
#     #     self.prerun_cmds.extend([
#     #         # Copy base namelist
#     #         f'cp {compile_dir}/Fasteddy/fasteddy_c.exe .',
#     #         "pwd"
#     #     ])
    
#     # @run_before('run')
#     # def configure_job(self):
#     #     """Configure job submission and environment"""
        
#     #     # Configure PBS to wait
#     #     self.job.options = ['-Wblock=true']
        
#     #     # Set poll interval
#     #     self.job.poll_interval = 30

#     @sanity_function
#     def validate_output(self):
#         """Check that simulation completed successfully"""
#         return sn.assert_found(
#             r'Solution Validates:',
#             self.stdout,
#             msg='Fasteddy did not terminate normally'
#         )
    
#     @performance_function('MB/s')
#     def copy_time(self):
#         """Extract copy test time in seconds"""
#         return sn.extractsingle(
#             r'Copy:\s+(\S+)',
#             self.stdout,
#             1,
#             float
#         )

@rfm.simple_test
class FastEddySWStackTest(FastEddyBaseTest):
    # Valid systems and environments
    #valid_systems = ['casper:gpu-mpi']
    valid_prog_environs = ['cuda', 'cuda-last', 'cuda-dev']
    
    # Fasteddy source directories
    #fasteddy_source_dir = variable(str, value='/glade/work/bneuman/reframe_apps/fasteddy/fasteddy_a100')
    #fasteddy_exe_dir = variable(str, value=fasteddy_source_dir + '/SRC/FEMAIN')
    #fasteddy_data_dir = variable(str, value=fasteddy_source_dir + '/tutorials/examples')
    
    # Build configuration
    build_system = 'Make'
    
    sourcesdir = '.'
    executable = 'set_gpu_rank ./FastEddy'
    executable_opts = ['Example02_CBL_veryshort.in']

    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '20m'

    num_gpus_per_node = 4

    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'!!!!!	  TIMESTEP PERFORMANCE',
            self.stdout,
            msg='Fasteddy did not start a timestep'
        )
    
    @performance_function('s')
    def total_time(self):
        """Extract total test time in seconds"""
        return sn.extractsingle(
            r'^\s*(\d+\.\d+)\s+\|\s+\d+\s+\|',
            self.stdout,
            1,
            float
        )
    
    @performance_function('s')
    def time_per_step(self):
        """Extract Time/step (s) - third column"""
        return sn.extractsingle(
            r'^\s*\d+\.\d+\s+\|\s+\d+\s+\|\s+(\d+\.\d+)',
            self.stdout,
            1,
            float
        )