import os

import pep8
import unittest

traindir = os.path.join('..', 'citrain')

class Pep8ConformanceTestCase(unittest.TestCase):
    def test_pep8_conformance(self):
        pep8style = pep8.StyleGuide(show_source=True)
        #pep8style.input_dir('..') # FIXME: enable this later.
        for filename in os.listdir(traindir):
            filepath = os.path.join(traindir, filename)
            if os.path.isfile(filepath):
                pep8style.check_files([filepath])
        self.assertEqual(pep8style.options.report.total_errors, 0)
