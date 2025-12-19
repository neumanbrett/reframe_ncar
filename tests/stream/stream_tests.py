"""
Simple STREAM Test Suite - Compilation and Quick Validation Only

This test suite contains two tests:
1. STREAMCompileTest - Verify STREAM compiles successfully
2. STREAMQuickTest - Quick validation run with basic checks
"""

import reframe as rfm
import reframe.utility.sanity as sn

# ============================================================================
# BASE TEST CLASS
# ============================================================================

class STREAMBaseTest(rfm.RegressionTest):
    """Base class for STREAM tests with common configuration"""
    
    # Valid systems and environments
    valid_systems = ['casper:compute']
    valid_prog_environs = ['gnu-serial']
    
    # STREAM source directory
    stream_source_dir = variable(str, value='/glade/work/bneuman/reframe_apps/STREAM')
    
    # Build configuration
    build_system = 'Make'
    
    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '10m'

    @run_before('compile')
    def setup_build_environment(self):
        
        # Copy source files to stage directory
        self.prebuild_cmds = [
            f'cp -r {self.stream_source_dir} .',
            'cd STREAM',
            'make clean'
        ]
        
        # CC = gcc
        #CFLAGS = -O2 -fopenmp

        #FC = gfortran
        #FFLAGS = -O2 -fopenmp
        # Environment specific Makefileet netCDF paths based on environment
        if self.current_environ.name == 'gnu':
            #'cp -f Makefile.gnu Makefile'
            self.build_system.cflags = ['-O2','-fopenmp']
            self.build_system.fflags = ['-O2','-fopenmp']
    
    @run_before('run')
    def setup_run_environment(self):
        """Set up runtime environment"""
        # Copy necessary input files
        self.prerun_cmds = [
            'ls -lh'
        ]

@rfm.simple_test
class STREAMCompileTest(STREAMBaseTest):
    """Test that STREAM compiles successfully"""
    
    descr = 'STREAM compilation test'
    tags = {'compile', 'quick', 'memory'}
    
    sourcesdir = '.'
    
    @run_after('setup')
    def skip_run(self):
        """Only compile, don't run"""
        self.build_system.makefile = 'Makefile'
    
    # @run_before('compile')
    # def setup_makefile(self):
    #     """Configure Makefile for compilation"""
    #     self.prebuild_cmds.extend([
    #         'make clean'
    #     ])
    
    @sanity_function
    def validate_compilation(self):
        """Check that executable was created"""
        return sn.assert_true(
            sn.os.path.exists('STREAM/stream_c.exe'),
            msg='stream_c.exe not found after compilation'
        )
    
# ============================================================================
# QUICK VALIDATION TEST
# ============================================================================

@rfm.simple_test
class STREAMQuickTest(rfm.RunOnlyRegressionTest):
    """Quick validation run with minimal configuration"""
    
    descr = 'STREAM validation test'
    tags = {'production', 'validation', 'quick', 'memory'}

    valid_systems = ['casper:compute']
    valid_prog_environs = ['gnu-serial']
    
    sourcesdir = '.'
    executable = 'stream_c.exe'
    
    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '10m'
    
    @run_after('init')
    def set_dependencies(self):
        """Depend on compilation test"""
        self.depends_on('STREAMCompileTest')

    @require_deps
    def setup_from_compile(self, STREAMCompileTest):
        """Copy executable from compile test"""
        compile_dir = STREAMCompileTest().stagedir
        """Configure namelist for quick test"""
        # Modify namelist.input for a quick 2D test
        self.prerun_cmds.extend([
            # Copy base namelist
            f'cp {compile_dir}/STREAM/stream_c.exe .',
            "pwd"
        ])
    
    @run_before('run')
    def configure_job(self):
        """Configure job submission and environment"""
        
        # Configure PBS to wait
        self.job.options = ['-Wblock=true']
        
        # Set poll interval
        self.job.poll_interval = 30

    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'Solution Validates:',
            self.stdout,
            msg='STREAM did not terminate normally'
        )
    
    @performance_function('MB/s')
    def copy_time(self):
        """Extract copy test time in seconds"""
        return sn.extractsingle(
            r'Copy:\s+(\S+)',
            self.stdout,
            1,
            float
        )