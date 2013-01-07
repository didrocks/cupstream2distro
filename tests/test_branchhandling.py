# -*- coding: UTF8 -*-
# Copyright: (C) 2013 Canonical
#
# Authors:
#  Didier Roche
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import tools_for_tests
import os
import unittest

from cupstream2distro import branchhandling


class BranchHandlingTests(unittest.TestCase):

    def tearDown(self):
        tools_for_tests.do_cleanup()

    def test_branching(self):
        '''Branch a branch'''

        source_branch = tools_for_tests.get_data_branch('basic')
        tools_for_tests.create_temp_workdir()
        branchhandling.get_branch(source_branch, 'test_branch')
        self.assertTrue(os.path.isdir('test_branch'))
        self.assertTrue(os.path.isdir('test_branch/.bzr'))
