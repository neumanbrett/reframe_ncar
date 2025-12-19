import reframe as rfm
import reframe.utility.sanity as sn

@rfm.simple_test
class HelloTest(rfm.RegressionTest):
    # Describe what the test does
    descr = 'Simple hello world test'
    
    # Valid systems and programming environments
    valid_systems = ['*']
    valid_prog_environs = ['*']
    
    # Source files to compile
    sourcepath = 'hello.c'
    
    # How to check if test passed
    @sanity_function
    def validate(self):
        return sn.assert_found(r'Hello, World!', self.stdout)