# ReFrame Configuration for NCAR's Casper, Derecho, and Gust
import swstack

# Modify these to quickly change required submission parameters like project code and queue
access_project_casper = ['-A SCSG0001', '-q casper']
access_project_derecho = ['-A SCSG0001', '-q main']

site_configuration = {
    'systems': [
        {
            'name': 'casper',
            'descr': 'HPC Cluster',
            'hostnames': ['crlogin*'],
            'modules_system': 'lmod',
            'partitions': [
                ######################
                ### CPU Partitions ###
                ######################
                {
                    # Any compute node without a GPU that uses MPI
                    'name': 'compute',
                    'descr': 'Compute nodes',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': access_project_casper,
                    'environs': ['gnu', 'intel'],
                    'max_jobs': 100,
                    'resources': [
                        {'name': 'cpu_type',       'options': ['cpu_type={cpu_type}']},
                        {'name': 'mpi_ranks',      'options': ['mpiprocs={mpiprocs}']},
                        {'name': 'openmp_threads', 'options': ['omp={openmp_threads}']},
                        {'name': 'mem',            'options': ['mem={mem}']},
                        {'name': 'host',           'options': ['host={hostname}']},
                    ]
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

                ######################
                ### GPU Partitions ###
                ######################
                {
                    # Single GPU
                    'name': 'gpu',
                    'descr': 'Single GPU, Single Node',
                    'scheduler': 'pbs',
                    'launcher': 'local',
                    'access': access_project_casper,
                    'environs': ['cuda', 'cuda-last', 'cuda-dev'],
                    'max_jobs': 10,
                    'resources': [
                        {'name': 'gpu_count',  'options': ['ngpus={num_gpus}']},
                        {'name': 'gpu_type',   'options': ['gpu_type={gpu_type}']},
                        {'name': 'mpi_ranks',  'options': ['mpiprocs={mpiprocs}']},
                        {'name': 'mem',        'options': ['mem={mem}']},
                    ]
                },

                # Multiple GPU with MPI
                {
                    'name': 'gpu-mpi',
                    'descr': 'Multi-GPU',
                    'scheduler': 'pbs',
                    'launcher': 'mpirun',
                    'access': access_project_casper,
                    'environs': ['cuda', 'cuda-last', 'cuda-dev'],
                    'max_jobs': 10,
                    'resources': [
                        {'name': 'gpu_count',  'options': ['ngpus={num_gpus}']},
                        {'name': 'gpu_type',   'options': ['gpu_type={gpu_type}']},
                        {'name': 'mpi_ranks',  'options': ['mpiprocs={mpiprocs}']},
                        {'name': 'mem',        'options': ['mem={mem}']},
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
            'modules': swstack.casper_devmodules_gnu
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
            'modules': swstack.casper_devmodules_intel
        },
        {
            'name': 'intel-last',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': swstack.casper_lastmodules_default
        },
                {
            'name': 'intel-dev',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': swstack.casper_devmodules_default
        },
        {
            'name': 'cuda',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': swstack.casper_currentmodules_default
        },
        {
            'name': 'cuda-last',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': swstack.casper_lastmodules_default
        },
        {
            'name': 'cuda-dev',
            'cc': 'mpicc',
            'cxx': 'mpicxx',
            'ftn': 'mpif90',
            'modules': swstack.casper_devmodules_default
        },
        {
            'name': 'default-current',
            'modules': swstack.casper_currentmodules_default
        },
        {
            'name': 'default-last',
            'modules': swstack.casper_lastmodules_default
        },
        {
            'name': 'default-dev',
            'modules': swstack.casper_devmodules_default
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
