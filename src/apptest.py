#!/usr/bin/python
import sys, os
# Install the Python unittest2 package before you run this script.
import unittest2

# I kept getting waranings complaining that all modules
# imported by code in application folder are already in the path
# I'm not sure how to fix this, and this type of warning
# is not an error, so I just ignore them

import warnings
warnings.filterwarnings('ignore',category=UserWarning)

USAGE = """

$ apptest.py path/to/your/appengine/installation

Path to your sdk must be the first argument
   
"""

def main(sdk_path, test_path):
    sys.path.insert(0, sdk_path)
    import dev_appserver 
    dev_appserver.fix_sys_path()
    sys.path.insert(1, os.path.join(os.path.abspath('.'), 'lib')) 
    suite = unittest2.loader.TestLoader().discover(test_path)
    unittest2.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    #See: http://code.google.com/appengine/docs/python/tools/localunittesting.html
    #Path to the SDK installation
    SDK_PATH = sys.argv[1]#u"/home/pawel/py/plays/appengine/google_appengine/"
    #Path to tests folder
    TEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__name__)),'tests')
    main(SDK_PATH, TEST_PATH)
