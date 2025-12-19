# ReFrame Configuration for NCAR's Casper, Derecho, and Gust

# Modify these to quickly change required submission parameters like project code and queue
access_project_casper = ['-A SCSG0001', '-q casper']
access_project_derecho = ['-A SCSG0001', '-q main']

# A collection of module stacks for easy updating of future stacks
# Format: <system>_<modules_type>_<compiler>_<mpi_version>
#
# Module types: 
#   currentmodules: The default modules that load with the current production software stack
#   lastmodules:    The default modules that loaded with the previous default production software stack
#   testmodules:    Modules to test a new software stack or variations on defaults
casper_currentmodules_default = ['ncarenv/24.12', 'intel/2024.2.1', 'openmpi/5.0.6', 'ncarcompilers/1.0.0', 'cuda/12.3.2', 'netcdf/4.9.2', 'hdf5/1.12.3', 'ucx/1.17.0']
casper_lastmodules_default = ['ncarenv/23.10', 'intel/2023.2.1', 'openmpi/4.1.6', 'ncarcompilers/1.0.0', 'cuda/12.2.1', 'netcdf/4.9.2', 'hdf5/1.12.2', 'ucx/1.14.1']
casper_devmodules_default = ['ncarenv/25.10', 'intel/2025.2.1', 'openmpi/5.0.8', 'ncarcompilers/1.1.0', 'cuda/12.9.0', 'netcdf/4.9.3', 'hdf5/1.14.6', 'ucx/1.19.0']

casper_currentmodules_intel = ['ncarenv/24.12', 'intel/2024.2.1', 'openmpi/5.0.6', 'ncarcompilers/1.0.0', 'cuda/12.3.2', 'netcdf/4.9.2', 'hdf5/1.12.3', 'ucx/1.17.0']
casper_currentmodules_gnu = ['ncarenv/24.12', 'gcc/12.4.0', 'openmpi/5.0.6', 'ncarcompilers/1.0.0', 'cuda/12.3.2', 'netcdf/4.9.2', 'hdf5/1.12.3', 'ucx/1.17.0']

# Archived stacks
#casper_2310_stack = []

site_configuration = {
    'systems': [
        {
            'name': 'casper',
            'descr': 'HPC Cluster',
            'hostnames': ['casper-login*'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'compute',
                    'descr': 'Compute nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': access_project_casper,
                    'environs': ['gnu', 'intel'],
                    'max_jobs': 100
                },
                                {
                    'name': 'compute-serial',
                    'descr': 'Compute nodes',
                    'scheduler': 'pbs',
                    'launcher': 'local',
                    'access': ['-A SCSG0001', '-q casper'],
                    'environs': ['gnu-serial'],
                    'max_jobs': 100
                },

                {
                    'name': 'gpu',
                    'descr': 'Single GPU, Single Node',
                    'scheduler': 'pbs',
                    'launcher': 'local',
                    'access': access_project_casper,
                    'environs': ['cuda', 'cuda-last', 'cuda-dev'],
                    'max_jobs': 10,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': [':ngpus={num_gpus}'],
                            'name': 'gpu_type',
                            'options': [':gpu_type={gpu_type}']
                        }
                    ]
                },
                {
                    'name': 'gpu-mpi',
                    'descr': 'Multi-GPU',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': access_project_casper,
                    'environs': ['cuda', 'cuda-last', 'cuda-dev'],
                    'max_jobs': 10,
                    'resources': [
                        {
                            'name': 'gpu',
                            'options': [':ngpus={num_gpus}'],
                            'name': 'gputype',
                            'options': [':gpu_type={gpu_type}']
                        }
                    ]
                }
            ]
        }
    ],
    'environments': [
        {
            'name': 'gnu',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_currentmodules_gnu
        },
        {
            'name': 'gnu-serial',
            'cc': 'gcc',
            'cxx': 'g++',
            'ftn': 'gfortran',
            'modules': ['gcc/12.4.0']
        },
        {
            'name': 'intel',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_currentmodules_intel
        },
        {
            'name': 'intel-last',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_lastmodules_default
        },
                {
            'name': 'intel-dev',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_devmodules_default
        },
        {
            'name': 'cuda',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_currentmodules_default
        },
        {
            'name': 'cuda-last',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_lastmodules_default
        },
        {
            'name': 'cuda-dev',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': casper_devmodules_default
        },
        {
            'name': 'default-current',
            'modules': casper_currentmodules_default
        },
        {
            'name': 'default-last',
            'modules': casper_lastmodules_default
        },
        {
            'name': 'default-dev',
            'modules': casper_devmodules_default
        }
    ],
    'logging': [
        {
            'level': 'debug',
            'handlers': [
                {
                    'type': 'file',
                    'name': 'reframe.log',
                    'level': 'debug',
                    'format': '[%(asctime)s] %(levelname)s: %(message)s',
                    'append': False
                },
                {
                    'type': 'stream',
                    'name': 'stdout',
                    'level': 'info',
                    'format': '%(message)s'
                }
            ]
        }
    ],
    'general': [
        {
            'check_search_path': ['${WORK}/tests/'],
            'check_search_recursive': True,
            #'stagedir': '/glade/derecho/scratch/bneuman/.tmp/reframe/stage',
            #'outputdir': '/glade/derecho/scratch/bneuman/.tmp/reframe/output',
            'report_file': 'reports/run-report-{sessionid}.json'
        }
    ]
}
