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

casper_devmodules_intel = ['ncarenv/25.10', 'intel/2025.2.1', 'openmpi/5.0.8', 'ncarcompilers/1.1.0', 'cuda/12.9.0', 'netcdf/4.9.3', 'hdf5/1.14.6', 'ucx/1.19.0']
casper_devmodules_gnu = ['ncarenv/25.10', 'gcc/14.3.0', 'openmpi/5.0.8', 'ncarcompilers/1.1.0', 'cuda/12.9.0', 'netcdf/4.9.3', 'hdf5/1.14.6', 'ucx/1.19.0']

casper_currentmodules_intel = ['ncarenv/24.12', 'intel/2024.2.1', 'openmpi/5.0.6', 'ncarcompilers/1.0.0', 'cuda/12.3.2', 'netcdf/4.9.2', 'hdf5/1.12.3', 'ucx/1.17.0']
casper_currentmodules_gnu = ['ncarenv/24.12', 'gcc/12.4.0', 'openmpi/5.0.6', 'ncarcompilers/1.0.0', 'cuda/12.3.2', 'netcdf/4.9.2', 'hdf5/1.12.3', 'ucx/1.17.0']

# Archived stacks
#casper_2310_stack = []