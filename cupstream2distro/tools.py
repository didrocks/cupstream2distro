# -*- coding: utf-8 -*-
# Copyright (C) 2012 Canonical
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

import ConfigParser
import os
import shutil
from xml.sax.saxutils import quoteattr, escape

from .settings import PROJECT_CONFIG_SUFFIX

WRAPPER_STRING = '''<testsuite errors="0" failures="{}" name="" tests="1" time="0.1">
  <testcase classname="MarkUnstable" name={} time="0.0">{}</testcase>
</testsuite>'''


def generate_xml_artefacts(test_name, details, filename):
    '''Generate a fake test name xml result for marking the build as unstable'''
    failure = ""
    errnum = 0
    for detail in details:
        errnum = 1
        failure += '    <failure type="exception">{}</failure>\n'.format(escape(detail))
    if failure:
        failure = '\n{}'.format(failure)

    with open(filename, 'w') as f:
        f.write(WRAPPER_STRING.format(errnum, quoteattr(test_name), failure))


def get_previous_distro_version_from_config(source_package_name):
    '''Get previous packaging version which was in bzr from the saved config'''
    config = ConfigParser.RawConfigParser()
    config.read("{}.{}".format(source_package_name, PROJECT_CONFIG_SUFFIX))
    return config.get('Package', 'dest_current_version')


def save_project_config(source_package_name, branch, revision, dest_current_version, current_packaging_version):
    '''Save branch and package configuration'''
    config = ConfigParser.RawConfigParser()
    config.add_section('Branch')
    config.set('Branch', 'branch', branch)
    config.set('Branch', 'rev', revision)
    config.add_section('Package')
    config.set('Package', 'dest_current_version', dest_current_version)
    config.set('Package', 'packaging_version', current_packaging_version)
    with open("{}.{}".format(source_package_name, PROJECT_CONFIG_SUFFIX), 'wb') as configfile:
        config.write(configfile)


def get_packaging_diff_filename(source_package_name, packaging_version):
    '''Return the packaging diff filename'''

    return "packaging_changes_{}_{}.diff".format(source_package_name, packaging_version)


def mark_project_as_published(source_package_name, packaging_version):
    '''Rename .project and eventual diff files so that if we do a partial rebuild, we don't try to republish them'''
    project_filename = "{}.{}".format(source_package_name, PROJECT_CONFIG_SUFFIX)
    os.rename(project_filename, "{}_{}".format(project_filename, packaging_version))
    diff_filename = get_packaging_diff_filename(source_package_name, packaging_version)
    if os.path.isfile(diff_filename):
        os.rename(diff_filename, "{}.published".format(diff_filename))


def clean_source(source):
    """clean all related source content from current silos"""
    with ignored(OSError):
        shutil.rmtree(source)
    with ignored(OSError):
        os.remove("{}.{}".format(source, PROJECT_CONFIG_SUFFIX))
    with ignored(OSError):
        shutil.rmtree("ubuntu/{}".format(source))
