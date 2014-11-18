#!/usr/bin/env python
# encoding: utf-8
"""
generate_keys.py

Generate CSRF and Session keys, output to secret_keys.py file

Usage:
    generate_keys.py [-f]

Outputs secret_keys.py file in current folder

By default, an existing secret_keys file will not be replaced.
Use the '-f' flag to force the new keys to be written to the file


"""

import string
import os.path

from optparse import OptionParser
from random import choice
from string import Template


# File settings
file_name = 'secret_keys.py'
file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)

file_template = Template('''# CSRF- and Session keys

CSRF_SECRET_KEY = '$csrf_key'
SESSION_KEY = '$session_key'
''')


# Get options from command line
parser = OptionParser()
parser.add_option(
    "-f", "--force", dest="force",
    help="force overwrite of existing secret_keys file", action="store_true")
parser.add_option(
    "-r", "--randomness", dest="randomness",
    help="length (randomness) of generated key; default = 24", default=24)
(options, args) = parser.parse_args()


def generate_randomkey(length):
    """Generate random key, given a number of characters"""
    chars = string.letters + string.digits
    return ''.join([choice(chars) for i in range(length)])


def write_file(contents):
    with open(file_path, 'wb') as f:
        f.write(contents)


def generate_keyfile(csrf_key, session_key):
    """Generate random keys for CSRF- and session key"""
    output = file_template.safe_substitute(dict(
        csrf_key=csrf_key, session_key=session_key
    ))
    if os.path.exists(file_path):
        if options.force is None:
            print "Warning: secret_keys.py file exists.  Use 'generate_keys.py --force' to force overwrite."
        else:
            write_file(output)
    else:
        write_file(output)


def main():
    r = options.randomness
    csrf_key = generate_randomkey(r)
    session_key = generate_randomkey(r)
    generate_keyfile(csrf_key, session_key)


if __name__ == "__main__":
    main()
