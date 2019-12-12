'''
Logger class to enable printing execution flow output if mitm_verbose
environment variable is set
'''
import os


# pylint: disable=too-few-public-methods
class ProxyLogger:
    ''' Proxy logger class to enable verbose output only when needed '''
    def __init__(self):
        self.mitm_logs = os.getenv('mitm_verbose', 'false').lower() == 'true'

    def log_output(self, output):
        ''' Prints MITM logs from this library to output if mitm_verbose is set '''
        if self.mitm_logs:
            print(output)
