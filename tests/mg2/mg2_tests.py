"""
Simple mg2 Test Suite - Compilation and Quick Validation Only

This test suite contains these tests:
1. Mg2CompileTest - Verify mg2 compiles successfully
2. Mg2ProdTest - Quick validation compile and run of a 16 column run
Others in production
"""

import reframe as rfm
import reframe.utility.sanity as sn

# ============================================================================
# Parameter Example
# Pass ElemTypeParam 
# ============================================================================

# class ElemTypeParam(rfm.RegressionMixin):
#     elem_type = parameter(['float', 'double'])

# ============================================================================
# BASE TEST CLASS
# ============================================================================

class Mg2BaseTest(rfm.RegressionTest):
    """Base class for mg2 tests with common configuration"""
    
    # Valid systems and environments
    valid_systems = ['casper:compute']
    valid_prog_environs = ['intel', 'gnu']
    
    # mg2 source directory
    mg2_source_dir = variable(str, value='/glade/work/bneuman/reframe_apps/mg2')
    
    # Build configuration
    build_system = 'Make'
    
    num_tasks = 16
    num_tasks_per_node = 16
    time_limit = '10m'

    # Define the flags necessary for each environment type
    fflags = variable(dict, value={
        'intel': ['-O1 -ffp-contract=fast -ffree-form -ffree-line-length-none', '-D_MPI'],
        'gnu':   ['-g -O3 -fp-model fast -ftz', '-D_MPI']
    })

    @run_after('init')
    def setup_build_environment(self):
        
        # Copy source files to stage directory
        self.prebuild_cmds = [
            f'cp -r {self.mg2_source_dir} .',
            'cd mg2/v14',
            'make clean'
        ]

        # Load and link the mkl module
        self.modules = ['mkl']

    @run_before('compile')
    def set_compiler_flags(self):
        self.build_system.ldflags = ['${MKLROOT}/lib/intel64 -lmkl_rt']

        # Adding required values to make command
        self.build_system.options = [f'pcols={self.num_tasks}', f'COMPILER={self.current_environ.name}']
        self.build_system.fflags = self.fflags.get(self.current_environ.name, [])


    @run_before('run')
    def setup_run_environment(self):
        """Set up runtime environment"""
        self.prerun_cmds = [
            f'cd mg2/v14'
        ]

@rfm.simple_test
class Mg2CompileTest(rfm.CompileOnlyRegressionTest):
    """Test that mg2 compiles successfully"""
    
    descr = 'mg2 compilation test'
    tags = {'compile', 'quick', 'memory'}

    valid_systems = ['casper:compute']
    valid_prog_environs = ['intel', 'gnu']
    
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
    
    # @sanity_function
    # def validate_compilation(self):
    #     """Check that executable was created"""
    #     return sn.assert_true(
    #         sn.os.path.exists('mg2/stream_c.exe'),
    #         msg='stream_c.exe not found after compilation'
    #     )
    
# ============================================================================
# COMPILE ONLY VALIDATION TEST
# ============================================================================

# ============================================================================
# COMPILE+RUN VALIDATION TEST
# ============================================================================

@rfm.simple_test
class Mg2ProdTest(Mg2BaseTest):
    """Quick validation run with minimal configuration"""
    
    descr = 'mg2 validation test on production modules'
    tags = {'production', 'validation', 'quick'}

    valid_systems = ['casper:compute']
    valid_prog_environs = ['intel', 'gnu']
    
    sourcesdir = '.'
    executable = 'kernel.exe'
    
    # num_tasks = 16
    # num_tasks_per_node = 16
    # time_limit = '10m'
    
    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'CESM2_MG2: PASSED verification',
            self.stdout,
            msg='mg2 did not terminate normally'
        )
    
    @performance_function('columns/s')
    def columns_per_second(self):
        return sn.extractsingle(
            r'Average columns per sec :\s+(\S+)',
            self.stdout,
            1,
            float
        )

@rfm.simple_test
class Mg2ProdScalingTest(Mg2BaseTest):
    """Quick validation run with minimal configuration"""
    
    descr = 'mg2 validation test on production modules'
    tags = {'production', 'validation', 'quick'}

    valid_systems = ['casper:compute']
    valid_prog_environs = ['intel', 'gnu']
    
    sourcesdir = '.'
    executable = 'kernel.exe'
    
    # num_tasks = 16
    # num_tasks_per_node = 16
    # time_limit = '10m'
    
    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        return sn.assert_found(
            r'CESM2_MG2: PASSED verification',
            self.stdout,
            msg='mg2 did not terminate normally'
        )
    
    @performance_function('columns/s')
    def columns_per_second(self):
        return sn.extractsingle(
            r'Average columns per sec :\s+(\S+)',
            self.stdout,
            1,
            float
        )

@rfm.simple_test
class Mg2SWStackTest(Mg2BaseTest):
    """Quick validation run with minimal configuration"""
    
    descr = 'mg2 validation test'
    tags = {'production', 'validation', 'quick', 'memory'}

    valid_systems = ['casper:compute']
    valid_prog_environs = ['gnu-serial']
    
    sourcesdir = '.'
    executable = 'kernel.exe'
    
    @run_after('init')
    def set_dependencies(self):
        """Depend on compilation test"""
        self.depends_on('mg2CompileTest')

    @require_deps
    def setup_from_compile(self, mg2CompileTest):
        """Copy executable from compile test"""
        compile_dir = mg2CompileTest().stagedir
        """Configure namelist for quick test"""
        # Modify namelist.input for a quick 2D test
        self.prerun_cmds.extend([
            # Copy base namelist
            f'cp {compile_dir}/mg2/stream_c.exe .',
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
            msg='mg2 did not terminate normally'
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

# ============================================================================
# RUN ONLY VALIDATION TEST
# ============================================================================

# Runs the current environment with precompiled application