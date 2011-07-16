#!/usr/bin/python
import os
import optparse
import sys
import unittest2

USAGE = """%prog SDK_PATH TEST_PATH
Run unit tests for App Engine apps.

SDK_PATH    Path to the SDK installation"""


def main(sdk_path, test_path):
    #Fix sys path for App Engine SDK
    sys.path.insert(0, sdk_path)
    import dev_appserver
    dev_appserver.fix_sys_path()

    #Fix sys path for Flask application
    sys.path.insert(0, "src")
    import main

    suite = unittest2.loader.TestLoader().discover(test_path)
    unittest2.TextTestRunner(verbosity=2).run(suite)


if __name__ == '__main__':
    parser = optparse.OptionParser(USAGE)
    options, args = parser.parse_args()
    if len(args) != 1:
        print 'Error: Exactly 1 argument required.'
        parser.print_help()
        sys.exit(1)
    SDK_PATH = args[0]
    TEST_PATH = os.path.join("src", "tests")
    main(SDK_PATH, TEST_PATH)
