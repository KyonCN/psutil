#!/usr/bin/env python

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Run unit tests. This is invoked by:

$ python -m psutil.tests
"""

import contextlib
import optparse
import os
import ssl
import sys
import tempfile
try:
    from urllib.request import urlopen  # py3
except ImportError:
    from urllib2 import urlopen

from psutil.tests import unittest
from psutil.tests import VERBOSITY


HERE = os.path.abspath(os.path.dirname(__file__))
PYTHON = os.path.basename(sys.executable)
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
TEST_DEPS = []
if sys.version_info[:2] == (2, 6):
    TEST_DEPS.extend(["ipaddress", "unittest2", "argparse", "mock==1.0.1"])
elif sys.version_info[:2] == (2, 7) or sys.version_info[:2] <= (3, 2):
    TEST_DEPS.extend(["ipaddress", "mock"])
elif sys.version_info[:2] == (3, 3):
    TEST_DEPS.extend(["ipaddress"])


def install_pip():
    try:
        import pip  # NOQA
    except ImportError:
        f = tempfile.NamedTemporaryFile(suffix='.py')
        with contextlib.closing(f):
            print("downloading %s to %s" % (GET_PIP_URL, f.name))
            if hasattr(ssl, '_create_unverified_context'):
                ctx = ssl._create_unverified_context()
            else:
                ctx = None
            kwargs = dict(context=ctx) if ctx else {}
            req = urlopen(GET_PIP_URL, **kwargs)
            data = req.read()
            f.write(data)
            f.flush()

            print("installing pip")
            code = os.system('%s %s --user' % (sys.executable, f.name))
            return code


def install_test_deps(deps=None):
    """Install test dependencies via pip."""
    if deps is None:
        deps = TEST_DEPS
    deps = set(deps)
    if deps:
        is_venv = hasattr(sys, 'real_prefix')
        opts = "--user" if not is_venv else ""
        install_pip()
        code = os.system('%s -m pip install %s --upgrade %s' % (
            sys.executable, opts, " ".join(deps)))
        return code


def get_suite():
    testmodules = [os.path.splitext(x)[0] for x in os.listdir(HERE)
                   if x.endswith('.py') and x.startswith('test_') and not
                   x.startswith('test_memory_leaks')]
    suite = unittest.TestSuite()
    for tm in testmodules:
        # ...so that the full test paths are printed on screen
        tm = "psutil.tests.%s" % tm
        suite.addTest(unittest.defaultTestLoader.loadTestsFromName(tm))
    return suite


def run_suite():
    result = unittest.TextTestRunner(verbosity=VERBOSITY).run(get_suite())
    success = result.wasSuccessful()
    sys.exit(0 if success else 1)


def main():
    usage = "%s -m psutil.tests [opts]" % PYTHON
    parser = optparse.OptionParser(usage=usage, description="run unit tests")
    parser.add_option("-i", "--install-deps",
                      action="store_true", default=False,
                      help="don't print status messages to stdout")

    opts, args = parser.parse_args()
    if opts.install_deps:
        install_pip()
        install_test_deps()
    else:
        for dep in TEST_DEPS:
            try:
                __import__(dep.split("==")[0])
            except ImportError:
                sys.exit("%r lib is not installed; run:\n"
                         "%s -m psutil.tests --install-deps" % (dep, PYTHON))
        run_suite()


main()
