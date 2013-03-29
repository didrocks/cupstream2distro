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

import os
import re
import shutil
import unittest
import tempfile


class BaseTestCase(unittest.TestCase):
    '''Module for basetest case adding handy
    functions and keeping track of temporary direct'''

    @classmethod
    def setUpClass(cls):
        cls.root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        cls.data_dir = os.path.join(cls.root_dir, 'data')
        cls.result_dir = os.path.join(cls.data_dir, 'results')
        cls.project_file_dir = os.path.join(cls.data_dir, 'project_files')

    @classmethod
    def addToPath(cls, path):
        '''Prepend some data to path, if path is relative, root_dir is used'''
        if not os.path.isabs(path):
            path = os.path.join(cls.root_dir, path)
        os.environ['PATH'] = "{}:{}".format(path, os.environ["PATH"])

    @classmethod
    def removeFromPath(cls, path):
        '''Remove some path from the PATH environment variables. If path is relative, root_dir is used'''
        if not os.path.isabs(path):
            path = os.path.join(cls.root_dir, path)
        elems = []
        for path_elem in os.environ['PATH'].split(':'):
            if path_elem != path:
                elems.append(path_elem)
        os.environ['PATH'] = ':'.join(elems)

    def setUp(self):
        self._dirs_to_remove = []
        os.environ['MOCK_MODE'] = "0"

    def tearDown(self):
        '''remove all temp dirs and return to root test dir'''
        os.chdir(self.root_dir)
        for dir in self._dirs_to_remove:
            try:
                shutil.rmtree(dir)
            except OSError:
                pass

    def create_temp_workdir(self, cd_in_dir=True):
        '''Create a temporary work directory and cd in it if cd_in_dir is True.'''
        tempdir = tempfile.mkdtemp()
        self._dirs_to_remove.append(tempdir)
        if cd_in_dir:
            os.chdir(tempdir)
        return tempdir

    def get_origin_branch_path(self, target_branch_name):
        '''Return the branch url in the data directory, don't make any other change'''
        return os.path.join(self.data_dir, 'branches', target_branch_name)

    def get_data_branch(self, target_branch_name, cd_in_branch=True):
        '''Return data branch directory from target_branch_name created in the current dir.

        This will perform the rename of 'bzr' dir in a .bzr one
        (can't do that in bzr itself for obvious reasons)
        The dir will be removed as part of tearDown.

        We can optionally cd into the dest branch'''
        dest_branch_path = os.path.abspath(target_branch_name)
        shutil.copytree(self.get_origin_branch_path(target_branch_name), dest_branch_path)
        os.rename(os.path.join(target_branch_name, 'bzr'), os.path.join(dest_branch_path, '.bzr'))
        if cd_in_branch:
            os.chdir(dest_branch_path)
        self._dirs_to_remove.append(dest_branch_path)
        return dest_branch_path

    def get_ubuntu_source_content_path(self, package_name):
        '''Return the ubuntu source package path for package_name'''
        return os.path.join(self.data_dir, 'ubuntu_source_packages', package_name)

    def are_files_identicals(self, filename1, filename2):
        '''Return true if filename1 and filename2 are equals'''
        return self.are_content_indenticals(open(filename1).read(), open(filename2).read())

    def are_content_indenticals(self, content1, content2):
        '''Return true if content1 and 2 are identicals'''
        return (content1 == content2)

    def assertFilesAreIdenticals(self, filename1, filename2):
        '''assert if the files content are identical'''
        self.assertEquals(open(filename1).read().strip(), open(filename2).read().strip())

    def assertChangesFilesAreIdenticals(self, filename1, filename2):
        '''assert if changes files content are identical, filtering the shasums and number of bytes which can differs with the same content'''
        remove_checksums_regexp = ' .* [0-9]+ (.*(gz|dsc))'
        content1 = re.sub(remove_checksums_regexp, r" \1", open(filename1).read().strip())
        content2 = re.sub(remove_checksums_regexp, r" \1", open(filename2).read().strip())
        self.assertEquals(content1, content2)

    def assertChangelogFilesAreIdenticals(self, filename1, filename2):
        '''assert that the changelog files are identicals, removing days/hours'''
        file2 = open(filename2)
        for linefile1 in open(filename1).readlines():
            linefile2 = file2.readline()
            if linefile1.startswith(" -- "):
                linefile1 = linefile1.split(">  ")[0]
                linefile2 = linefile2.split(">  ")[0]
            self.assertEquals(linefile1, linefile2)
