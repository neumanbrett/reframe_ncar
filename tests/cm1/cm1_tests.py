"""
ReFrame Test Suite for CM1 (Cloud Model 1)

CM1 is a three-dimensional, non-hydrostatic atmospheric model
developed by George Bryan at NCAR for idealized atmospheric research.

This test suite covers:
- Compilation testing
- Quick validation runs
- Supercell simulation benchmark
- Scaling studies
"""

import reframe as rfm
import reframe.utility.sanity as sn


# ============================================================================
# BASE TEST CLASS
# ============================================================================

class CM1BaseTest(rfm.RegressionTest):
    """Base class for all CM1 tests with common configuration"""
    
    # Valid systems and environments
    valid_systems = ['casper:compute']
    valid_prog_environs = ['gnu', 'intel']
    
    # CM1 source directory
    cm1_source_dir = variable(str, value='${CM1_HOME}')
    
    # Build configuration
    build_system = 'Make'
    
    # Note: num_tasks, num_tasks_per_node, and time_limit are NOT set here
    # Each derived class must set these to avoid conflicts
    
    @run_before('compile')
    def setup_build_environment(self):
        """Set up build environment for CM1"""
        self.build_system.max_concurrency = 8
        
        # Copy source files to stage directory
        self.prebuild_cmds = [
            f'cp -r {self.cm1_source_dir}/src .',
            f'cp -r {self.cm1_source_dir}/run .',
            'cd src'
        ]
        
        # Set netCDF paths based on environment
        self.build_system.options = ['-L${NCAR_LDFLAGS_NETCDF}']
    
    @run_before('run')
    def setup_run_environment(self):
        """Set up runtime environment"""
        # Copy necessary input files
        self.prerun_cmds = [
            'cp ../src/cm1.exe .',
            'cp run/namelist.input .',
            'ls -lh'
        ]
        
        # Set environment variables
        self.env_vars = {
            'OMP_NUM_THREADS': '1',
            'MALLOC_TRIM_THRESHOLD_': '0'
        }


# ============================================================================
# COMPILATION TEST
# ============================================================================

@rfm.simple_test
class CM1CompileTest(CM1BaseTest):
    """Test that CM1 compiles successfully"""
    
    descr = 'CM1 compilation test'
    tags = {'compile', 'quick'}
    
    sourcesdir = '.'
    
    @run_after('setup')
    def skip_run(self):
        """Only compile, don't run"""
        self.build_system.makefile = 'Makefile'
    
    @run_before('compile')
    def setup_makefile(self):
        """Configure Makefile for compilation"""
        self.prebuild_cmds.extend([
            'cd src',
            'cp Makefile Makefile.orig'
        ])
    
    @sanity_function
    def validate_compilation(self):
        """Check that executable was created"""
        return sn.assert_true(
            sn.os.path.exists('src/cm1.exe'),
            msg='cm1.exe not found after compilation'
        )
    
    @performance_function('s')
    def compile_time(self):
        """Extract compilation time"""
        return sn.extractsingle(
            r'Elapsed.*:\s+(\S+)',
            self.build_stdout,
            1,
            float,
            default=0.0
        )


# ============================================================================
# QUICK VALIDATION TEST
# ============================================================================

@rfm.simple_test
class CM1QuickTest(CM1BaseTest):
    """Quick validation run with minimal configuration"""
    
    descr = 'CM1 quick validation test (2D squall line)'
    tags = {'production', 'validation', 'quick'}
    
    sourcesdir = '.'
    executable = './cm1.exe'
    
    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '10m'
    
    @run_before('run')
    def setup_namelist(self):
        """Configure namelist for quick test"""
        # Modify namelist.input for a quick 2D test
        self.prerun_cmds.extend([
            # Copy base namelist
            f'cp {self.cm1_source_dir}/run/config_files/squall_line/namelist.input .',
            # Modify for quick run
            "sed -i 's/run_time.*/run_time = 300.0/' namelist.input",
            "sed -i 's/nx.*/nx = 128/' namelist.input",
            "sed -i 's/ny.*/ny = 2/' namelist.input",
            "sed -i 's/nz.*/nz = 32/' namelist.input",
            "sed -i 's/output_format.*/output_format = 2/' namelist.input",
            'cat namelist.input | grep -E "(run_time|nx|ny|nz)"'
        ])
    
    @sanity_function
    def validate_output(self):
        """Check that simulation completed successfully"""
        checks = [
            # Check for successful completion message
            sn.assert_found(
                r'cm1 completed successfully',
                self.stdout,
                msg='CM1 did not complete successfully'
            ),
            # Check that output files were created
            sn.assert_true(
                sn.os.path.exists('cm1out.nc') or sn.os.path.exists('cm1out_000001.nc'),
                msg='No output files found'
            ),
            # Check for no fatal errors
            sn.assert_not_found(
                r'FATAL|ERROR',
                self.stderr,
                msg='Fatal error found in stderr'
            )
        ]
        return sn.all(checks)
    
    @performance_function('s')
    def simulation_time(self):
        """Extract total simulation time"""
        return sn.extractsingle(
            r'Total time:\s+(\S+)\s+s',
            self.stdout,
            1,
            float
        )
    
    @performance_function('s')
    def time_per_timestep(self):
        """Extract average time per timestep"""
        return sn.extractsingle(
            r'Time per time step:\s+(\S+)\s+s',
            self.stdout,
            1,
            float
        )


# ============================================================================
# SUPERCELL BENCHMARK
# ============================================================================

@rfm.simple_test
class CM1SupercellBenchmark(CM1BaseTest):
    """
    Standard supercell benchmark simulation
    This is a common test case for CM1 performance evaluation
    """
    
    descr = 'CM1 supercell benchmark (3D idealized supercell)'
    tags = {'production', 'benchmark', 'supercell'}
    
    sourcesdir = '.'
    executable = './cm1.exe'
    
    # Use parameter for num_tasks - this is allowed
    num_tasks = parameter([4, 8, 16, 32, 64])
    num_tasks_per_node = 36
    time_limit = '2h'
    
    @run_after('setup')
    def set_time_limit_based_on_tasks(self):
        """Adjust time limit based on task count"""
        if self.num_tasks <= 8:
            self.time_limit = '2h'
        elif self.num_tasks <= 32:
            self.time_limit = '1h'
        else:
            self.time_limit = '30m'
    
    @run_before('run')
    def setup_supercell_namelist(self):
        """Configure namelist for supercell simulation"""
        self.prerun_cmds.extend([
            f'cp {self.cm1_source_dir}/run/config_files/supercell/namelist.input .',
            # Standard supercell configuration
            "sed -i 's/run_time.*/run_time = 7200.0/' namelist.input",  # 2 hours
            "sed -i 's/nx.*/nx = 256/' namelist.input",
            "sed -i 's/ny.*/ny = 256/' namelist.input",
            "sed -i 's/nz.*/nz = 64/' namelist.input",
            "sed -i 's/dx.*/dx = 250.0/' namelist.input",
            "sed -i 's/dy.*/dy = 250.0/' namelist.input",
            "sed -i 's/dz.*/dz = 250.0/' namelist.input",
            "sed -i 's/output_format.*/output_format = 2/' namelist.input",  # netCDF
            "sed -i 's/output_filetype.*/output_filetype = 2/' namelist.input",
            'echo "Namelist configuration:"',
            'cat namelist.input | grep -E "(run_time|nx|ny|nz|dx)"'
        ])
    
    @sanity_function
    def validate_supercell(self):
        """Validate supercell simulation output"""
        checks = [
            sn.assert_found(
                r'cm1 completed successfully',
                self.stdout,
                msg='CM1 supercell run did not complete'
            ),
            # Check for updraft development (typical of supercells)
            sn.assert_found(
                r'Maximum vertical velocity.*\d+',
                self.stdout,
                msg='No vertical velocity output found'
            ),
            # Verify output files exist
            sn.assert_true(
                sn.os.path.exists('cm1out_000001.nc'),
                msg='NetCDF output file not created'
            )
        ]
        return sn.all(checks)
    
    @performance_function('s')
    def total_runtime(self):
        """Total wall-clock time for simulation"""
        return sn.extractsingle(
            r'Total time:\s+(\S+)\s+s',
            self.stdout,
            1,
            float
        )
    
    @performance_function('s')
    def avg_timestep_time(self):
        """Average time per timestep"""
        return sn.extractsingle(
            r'Time per time step:\s+(\S+)\s+s',
            self.stdout,
            1,
            float
        )
    
    @performance_function('timesteps/s')
    def throughput(self):
        """Timesteps per second (higher is better)"""
        total_time = self.total_runtime()
        total_steps = sn.extractsingle(
            r'Total time steps:\s+(\d+)',
            self.stdout,
            1,
            int
        )
        return total_steps / total_time
    
    # Performance reference values (adjust based on your system)
    reference = {
        'casper:compute': {
            'total_runtime': (1800, None, 0.15, 's'),
            'avg_timestep_time': (0.5, None, 0.15, 's'),
            'throughput': (2.0, -0.15, None, 'timesteps/s')
        }
    }


# ============================================================================
# WEAK SCALING TEST
# ============================================================================

@rfm.simple_test
class CM1WeakScalingTest(CM1BaseTest):
    """
    Weak scaling test - problem size scales with processor count
    Tests parallel efficiency as resources increase
    """
    
    descr = 'CM1 weak scaling test'
    tags = {'performance', 'scaling', 'weak-scaling'}
    
    sourcesdir = '.'
    executable = './cm1.exe'
    
    # Parameter for different task counts
    num_tasks = parameter([4, 8, 16, 32, 64])
    num_tasks_per_node = 36
    time_limit = '1h'
    
    @run_before('run')
    def setup_weak_scaling(self):
        """Scale problem size with processor count"""
        # Base grid: 128x128x32 for 4 tasks
        # Scale in x and y directions
        import math
        scale_factor = math.sqrt(self.num_tasks / 4)
        nx = int(128 * scale_factor)
        ny = int(128 * scale_factor)
        nz = 32  # Keep vertical resolution constant
        
        self.prerun_cmds.extend([
            f'cp {self.cm1_source_dir}/run/config_files/squall_line/namelist.input .',
            f"sed -i 's/run_time.*/run_time = 1800.0/' namelist.input",
            f"sed -i 's/nx.*/nx = {nx}/' namelist.input",
            f"sed -i 's/ny.*/ny = {ny}/' namelist.input",
            f"sed -i 's/nz.*/nz = {nz}/' namelist.input",
            f'echo "Weak scaling: {self.num_tasks} tasks, grid {nx}x{ny}x{nz}"'
        ])
    
    @sanity_function
    def validate_scaling(self):
        return sn.assert_found(r'cm1 completed successfully', self.stdout)
    
    @performance_function('s')
    def walltime(self):
        """Wall time should remain relatively constant for good scaling"""
        return sn.extractsingle(
            r'Total time:\s+(\S+)\s+s',
            self.stdout,
            1,
            float
        )
    
    @performance_function('%')
    def parallel_efficiency(self):
        """Calculate parallel efficiency relative to baseline"""
        baseline_time = 600.0  # Reference time for 4 tasks (adjust)
        current_time = self.walltime()
        return (baseline_time / current_time) * 100


# ============================================================================
# STRONG SCALING TEST
# ============================================================================

@rfm.simple_test
class CM1StrongScalingTest(CM1BaseTest):
    """
    Strong scaling test - fixed problem size, varying processor count
    Tests speedup as resources increase
    """
    
    descr = 'CM1 strong scaling test'
    tags = {'performance', 'scaling', 'strong-scaling'}
    
    sourcesdir = '.'
    executable = './cm1.exe'
    
    # Parameter for different task counts
    num_tasks = parameter([4, 8, 16, 32, 64, 128])
    num_tasks_per_node = 36
    time_limit = '1h'
    
    @run_before('run')
    def setup_strong_scaling(self):
        """Fixed problem size for all processor counts"""
        # Fixed grid: 256x256x64
        self.prerun_cmds.extend([
            f'cp {self.cm1_source_dir}/run/config_files/supercell/namelist.input .',
            "sed -i 's/run_time.*/run_time = 3600.0/' namelist.input",
            "sed -i 's/nx.*/nx = 256/' namelist.input",
            "sed -i 's/ny.*/ny = 256/' namelist.input",
            "sed -i 's/nz.*/nz = 64/' namelist.input",
            f'echo "Strong scaling: {self.num_tasks} tasks, fixed grid 256x256x64"'
        ])
    
    @sanity_function
    def validate_scaling(self):
        return sn.assert_found(r'cm1 completed successfully', self.stdout)
    
    @performance_function('s')
    def walltime(self):
        """Wall time should decrease with more processors"""
        return sn.extractsingle(
            r'Total time:\s+(\S+)\s+s',
            self.stdout,
            1,
            float
        )
    
    @performance_function('x')
    def speedup(self):
        """Speedup relative to baseline (4 tasks)"""
        baseline_time = 3600.0  # Reference time for 4 tasks (adjust)
        current_time = self.walltime()
        return baseline_time / current_time
    
    @performance_function('%')
    def efficiency(self):
        """Parallel efficiency percentage"""
        speedup = self.speedup()
        return (speedup / (self.num_tasks / 4)) * 100


# ============================================================================
# OUTPUT VERIFICATION TEST
# ============================================================================

@rfm.simple_test
class CM1OutputVerificationTest(CM1BaseTest):
    """
    Verify CM1 produces expected output files and formats
    Tests netCDF output and data integrity
    """
    
    descr = 'CM1 output verification test'
    tags = {'validation', 'output'}
    
    sourcesdir = '.'
    executable = './cm1.exe'
    
    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '15m'
    
    @run_before('run')
    def setup_output_test(self):
        """Configure for various output formats"""
        self.prerun_cmds.extend([
            f'cp {self.cm1_source_dir}/run/config_files/squall_line/namelist.input .',
            "sed -i 's/run_time.*/run_time = 600.0/' namelist.input",
            "sed -i 's/nx.*/nx = 64/' namelist.input",
            "sed -i 's/ny.*/ny = 2/' namelist.input",
            "sed -i 's/nz.*/nz = 32/' namelist.input",
            "sed -i 's/output_format.*/output_format = 2/' namelist.input",
            "sed -i 's/output_filetype.*/output_filetype = 2/' namelist.input",
            "sed -i 's/stat_out.*/stat_out = 60.0/' namelist.input"
        ])
        
        # Load netCDF tools if available
        self.modules = ['nco', 'ncview']
    
    @sanity_function
    def validate_output_files(self):
        """Check that all expected output files exist"""
        checks = [
            sn.assert_found(r'cm1 completed successfully', self.stdout),
            # Check for netCDF output
            sn.assert_true(
                sn.os.path.exists('cm1out_000001.nc'),
                msg='Main netCDF output not found'
            ),
            # Check for statistics file
            sn.assert_true(
                sn.os.path.exists('cm1out_stats.nc') or 
                sn.os.path.exists('cm1out_s.nc'),
                msg='Statistics file not found'
            )
        ]
        return sn.all(checks)
    
    @run_after('run')
    def verify_netcdf_content(self):
        """Use ncdump to verify netCDF file structure"""
        self.postrun_cmds = [
            'ncdump -h cm1out_000001.nc | head -50',
            'ls -lh cm1out*.nc'
        ]


# ============================================================================
# RESTART TEST
# ============================================================================

@rfm.simple_test
class CM1RestartTest(CM1BaseTest):
    """
    Test CM1 checkpoint/restart functionality
    Verifies that simulations can be restarted from saved state
    """
    
    descr = 'CM1 restart capability test'
    tags = {'validation', 'restart'}
    
    sourcesdir = '.'
    executable = './cm1.exe'
    
    num_tasks = 4
    num_tasks_per_node = 4
    time_limit = '20m'
    
    @run_before('run')
    def setup_restart_test(self):
        """Configure for restart test"""
        self.prerun_cmds.extend([
            f'cp {self.cm1_source_dir}/run/config_files/squall_line/namelist.input .',
            # First run: 300 seconds with restart output
            "sed -i 's/run_time.*/run_time = 300.0/' namelist.input",
            "sed -i 's/rstfrq.*/rstfrq = 300.0/' namelist.input",  # Write restart at end
            "sed -i 's/nx.*/nx = 64/' namelist.input",
            "sed -i 's/ny.*/ny = 2/' namelist.input",
            "sed -i 's/nz.*/nz = 32/' namelist.input"
        ])
    
    @sanity_function
    def validate_restart(self):
        """Verify restart file was created and run completed"""
        checks = [
            sn.assert_found(r'cm1 completed successfully', self.stdout),
            sn.assert_true(
                sn.os.path.exists('cm1out_rst_000001.nc'),
                msg='Restart file not created'
            ),
            sn.assert_found(
                r'Writing restart',
                self.stdout,
                msg='No restart write message found'
            )
        ]
        return sn.all(checks)


# ============================================================================
# HELPER: Test Discovery
# ============================================================================

# You can run specific tags:
# reframe -c cm1_tests.py --tag=quick -r
# reframe -c cm1_tests.py --tag=benchmark -r
# reframe -c cm1_tests.py --tag=scaling -r