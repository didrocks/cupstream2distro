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
import shutil
import tempfile

root_dir = os.path.abspath('.')
data_dir = os.path.join(root_dir, 'tests', 'data')

dirs_to_remove = []


def create_temp_workdir():
    '''Create a temporary work directory and cd in it'''
    global dirs_to_remove
    tempdir = tempfile.mkdtemp()
    dirs_to_remove.append(tempdir)
    os.chdir(tempdir)


def _remove_temp_dirs():
    '''remove all temp dirs'''
    global dirs_to_remove
    for dir in dirs_to_remove:
        try:
            shutil.rmtree(dir)
        except OSError:
            pass
    dirs_to_remove = []


def do_cleanup():
    '''Should be called by all tearDown jobs'''
    os.chdir(root_dir)
    print(dirs_to_remove)
    _remove_temp_dirs()


def get_data_branch(target_branch):
    '''Return a temporary data branch directory from target_branch.

    This will perform the rename of 'bzr' dir in a .bzr one
    (can't do that in bzr itself for obvious reasons)
    The dir will be removed as part of tearDown.'''
    global dirs_to_remove
    tempdir = tempfile.mktemp()
    dirs_to_remove.append(tempdir)
    shutil.copytree(os.path.join(data_dir, 'branches', target_branch), tempdir)
    os.rename(os.path.join(tempdir, 'bzr'), os.path.join(tempdir, '.bzr'))
    return tempdir
