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

from . import BaseUnitTestCase
import os

from cupstream2distro import branchhandling


class BranchHandlingTests(BaseUnitTestCase):

    def test_branching(self):
        '''Test that we correcly try to branch a branch'''
        source_branch = self.get_data_branch('basic')
        self.get_a_temp_workdir()
        branchhandling.get_branch(source_branch, 'test_branch')
        self.assertTrue(os.path.isdir('test_branch'))
        self.assertTrue(os.path.isdir('test_branch/.bzr'))
