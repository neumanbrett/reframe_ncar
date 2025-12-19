"""
Simple CM1 Test Suite - Compilation and Quick Validation Only

This simplified test suite contains just two tests:
1. CM1CompileTest - Verify CM1 compiles successfully
2. CM1QuickTest - Quick validation run with basic checks
"""

import reframe as rfm
import reframe.utility.sanity as sn

cm1_base_dir = '/glade/work/bneuman/reframe_apps/cm1/'

# ============================================================================
# BASE TEST CLASS
# ============================================================================

class CM1BaseTest(rfm.RegressionTest):
    """ Base class for CM1 tests with common configuration
        Works across all nodes of each system
        Compiles and runs the application
    """
    
    # Valid systems and environments
    valid_systems = ['casper:compute']
    valid_prog_environs = ['gnu', 'intel']
    
    # CM1 source directory
    cm1_source_dir = variable(str, value='/glade/work/bneuman/reframe_apps/cm1/cm1r21.1_base')
    
    # Build configuration
    build_system = 'Make'
    
    # @run_before('run')
    # def setup_run_environment(self):
    #     """Set up runtime environment"""
    #     # Copy necessary input files
    #     self.prerun_cmds = [
    #         'cp ../run/cm1.exe .',
    #         'cp ../run/namelist.input .',
    #         'ls -lh'
    #     ]
        
    #     # Set environment variables
    #     self.env_vars = {
    #         'OMP_NUM_THREADS': '1',
    #         'MALLOC_TRIM_THRESHOLD_': '0'
    #     }

# ============================================================================
# COMPILE AND RUN TEST
# ============================================================================
@rfm.simple_test
class CM1FullTest(CM1BaseTest):
    """Test that CM1 compiles and runs successfully"""
    
    descr = 'CM1 compile and run test'
    tags = {'compile_run', 'core'}
    
    valid_systems = ['casper:compute']
    #valid_partitions = []
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
        
        # Copy source files to stage directory
        self.prebuild_cmds = [
            f'cp -r {self.cm1_source_dir}/src .',
            f'cp -r {self.cm1_source_dir}/run .',
            'cd src',
            'make clean'
        ]

        # Casper system flags
        if self.current_system.name == 'casper':
            if self.current_environ.name == 'gnu':
                #'cp -f Makefile.gnu Makefile'
                self.build_system.cppflags = ['cpp', '-C', '-P', '-traditional', '-Wno-invalid-pp-token', '-ffreestanding']
                self.build_system.options = [
                    'OPTS="-ffree-form -ffree-line-length-none -O2 -finline-functions -fallow-argument-mismatch"',
                    'DM="-DMPI"'
                ]
            elif self.current_environ.name == 'intel':
                self.build_system.cppflags = ['-O3', '-ip', '-assume byterecl', '-fp-model precise', '-ftz', '-no-fma']
                self.build_system.options = [
                    'OPTS="-O3 -ip -assume byterecl -fp-model precise -ftz -no-fma"',
                    'DM="-DMPI"'
                ]
            # Linking NetCDF
            self.build_system.ldflags = ['-lnetcdf']

    # @run_before('run')
    # def configure_job(self):
    #     """Configure job submission and environment"""
        
    #     # Configure PBS to wait
    #     self.job.options = ['-Wblock=true']
        
    #     # Set poll interval
    #     self.job.poll_interval = 30
    
    #def setup_from_compile(self):
        """Configure namelist for quick test"""
        # Modify namelist.input for a quick 2D test
        self.prerun_cmds = [
            # Nav to run dir with exe and namelist
            f'cd {self.stagedir}/run'
            #f'cp ./run/cm1.exe .',
            #f'cp ./run/config_files/squall_line/namelist.input .'
        ]

    # def setup_namelist(self):
    #     self.prerun_cmds.extend([
    #         f'cd run'
    #     ])

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
# COMPILATION TEST
# ============================================================================

# @rfm.simple_test
# class CM1CompileTest(CM1BaseTest):
#     """Test that CM1 compiles successfully"""
    
#     descr = 'CM1 compilation test'
#     tags = {'compile', 'core'}
    
#     sourcesdir = '.'

#     num_tasks = 8
#     num_tasks_per_node = 8
#     time_limit = '15m'
    
#     @run_after('setup')
#     def skip_run(self):
#         """Only compile, don't run"""
#         self.build_system.makefile = 'Makefile'
    
#     @run_before('compile')
#     def setup_makefile(self):
#         """Configure Makefile for compilation"""
#         self.prebuild_cmds.extend([
#             'make clean'
#         ])
    
#     @sanity_function
#     def validate_compilation(self):
#         """Check that executable was created"""
#         return sn.assert_true(
#             sn.os.path.exists('run/cm1.exe'),
#             msg='cm1.exe not found after compilation'
#         )


# ============================================================================
# QUICK VALIDATION TEST
# ============================================================================

# @rfm.simple_test
# class CM1RunTest(rfm.RunOnlyRegressionTest):
#     """Quick validation run with minimal configuration"""
    
#     descr = 'CM1 quick validation test (2D squall line)'
#     tags = {'production', 'run'}

#     valid_systems = ['casper:compute']
#     valid_prog_environs = ['gnu', 'intel']
    
#     sourcesdir = '.'
#     executable = 'cm1.exe'
    
#     num_tasks = 4
#     num_tasks_per_node = 4
#     time_limit = '10m'
    
#     @run_after('init')
#     #def setup_resources(self):
#     #   if self.current_system.name == 'casper':
#     #       if self.current_partition ...

#     def setup_executable(self):
#         if self.current_system.name == 'casper':
#             if 'run' in self.tags:
#                 if self.current_environ.name == 'intel': 
#                     cm1_source_dir = variable(str, value=cm1_base_dir + 'cm1r21.1_intel')
#                 elif self.current_environ.name == 'gnu':
#                     cm1_source_dir = variable(str, value=cm1_base_dir + 'cm1r21.1_gnu')
#             else:
#                 """Depend on compilation test"""
#                 self.depends_on('CM1CompileTest')

#                 @require_deps
#                 def setup_from_compile(self, CM1CompileTest):
#                     """Copy executable from compile test"""
#                     compile_dir = CM1CompileTest().stagedir
#                     """Configure namelist for quick test"""
#                     # Modify namelist.input for a quick 2D test
#                     self.prerun_cmds.extend([
#                         # Copy base namelist
#                         f'cp {compile_dir}/run/cm1.exe .',
#                         f'cp {compile_dir}/run/config_files/squall_line/namelist.input .',
#                         # Modify for quick run
#                         "sed -i 's/run_time.*/run_time = 300.0/' namelist.input",
#                         "sed -i 's/nx.*/nx = 128/' namelist.input",
#                         "sed -i 's/ny.*/ny = 2/' namelist.input",
#                         "sed -i 's/nz.*/nz = 32/' namelist.input",
#                         "sed -i 's/output_format.*/output_format = 2/' namelist.input",
#                         'cat namelist.input | grep -E "(run_time|nx|ny|nz)"'
#                     ])
    
#     @run_before('run')
#     def configure_job(self):
#         """Configure job submission and environment"""
        
#         # Configure PBS to wait
#         self.job.options = ['-Wblock=true']
        
#         # Set poll interval
#         self.job.poll_interval = 30

#     @sanity_function
#     def validate_output(self):
#         """Check that simulation completed successfully"""
#         return sn.assert_found(
#             r'approximate core-hours',
#             self.stdout,
#             msg='CM1 did not terminate normally'
#         )
    
#     @performance_function('s')
#     def total_time(self):
#         """Extract total simulation time in seconds"""
#         return sn.extractsingle(
#             r'Total time:\s+(\S+)',
#             self.stdout,
#             1,
#             float
#         )