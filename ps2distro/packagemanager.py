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

import os
import re
import subprocess

from .launchpadmanager import get_launchpad
from .settings import REV_STRING_FORMAT, BOT_DEBFULLNAME, BOT_DEBEMAIL


def get_current_version_for_serie(source_package_name, serie_name):
    '''Get current version for a package name in that serie'''
    ubuntu = get_launchpad().distributions['ubuntu']
    serie = ubuntu.getSeries(name_or_version=serie_name)
    version = None
    for source in ubuntu.main_archive.getPublishedSources(status="Published", exact_match=True, source_name=source_package_name, distro_series=serie):
        if version:
            if is_version1_higher_than_version2(source.source_package_version, version):
                version = source.source_package_version
        else:
            version = source.source_package_version
    return version


def is_version1_higher_than_version2(version1, version2):
    '''return if version1 is higher than version2'''
    return (subprocess.call(["dpkg", "--compare-versions", version1, 'gt', version2], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0)


def get_latest_upstream_bzr_rev(f):
    '''Report latest bzr rev in the file'''
    regex = re.compile(REV_STRING_FORMAT + "(\d+)")
    for line in f:
        rev = regex.findall(line)
        if rev:
            return int(rev[0])

    raise Exception("Didn't find any string in debian/changelog of the form: \"{}\". Bootstrapping issue?".format(regex.pattern))


def get_packaging_version():
    '''Get current packaging rev'''
    instance = subprocess.Popen(["dpkg-parsechangelog"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8")[:-1])  # remove last \n
    expr = re.compile("Version: (.*)")
    for line in stdout.splitlines():
        packaging_version = expr.findall(line)
        if packaging_version:
            return packaging_version[0]

    raise Exception("Didn't find any Version in the package: {}".format(stdout))


def get_packaging_sourcename():
    '''Get current packaging source name'''
    instance = subprocess.Popen(["dpkg-parsechangelog"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8")[:-1])  # remove last \n
    expr = re.compile("Source: (.*)")
    for line in stdout.splitlines():
        source_name = expr.findall(line)
        if source_name:
            return source_name[0]

    raise Exception("Didn't find any source name in the package: {}".format(stdout))


def collect_bugs_until_latest_bzr_rev(f, source_package_name):
    '''Collect all bugs until latest bzr rev in the file'''
    bugs = set()
    temporary_bugs_set = set()
    # matching only bug format that launchpad accepts
    bug_regexp = re.compile("lp: ?#(\d{5,})", re.IGNORECASE)
    end_regexp = re.compile(REV_STRING_FORMAT + "(\d+)")
    new_changelog_regexp = re.compile("^{} \(".format(source_package_name))
    for line in f:
        bug_list = bug_regexp.findall(line)
        for bug in bug_list:
            temporary_bugs_set.add(bug)
        # new cherry-pick upload, put the temporary set in the final bugs set
        if new_changelog_regexp.match(line) and temporary_bugs_set:
            bugs = bugs.union(temporary_bugs_set)
            temporary_bugs_set = set()
        if end_regexp.findall(line):
            # don't add the last temporary_bugs_set as it's all the bugs part of the previous automated upload
            # (the REV_STRING_FORMAT is not assured to be the first line):
            # those bugs maybe weren't completely fixed after all and a new fix was needed.
            return bugs

    raise Exception("Didn't find any string in debian/changelog of the form: \"{}\". Bootstrapping issue?".format(end_regexp.pattern))


def update_changelog(new_package_version, serie, tip_bzr_rev, authors_bugs_with_title):
    '''Update the changelog for the incoming upload'''

    dch_env = os.environ.copy()
    for author in authors_bugs_with_title:
        dch_env["DEBFULLNAME"] = author
        for bug_desc in authors_bugs_with_title[author]:
            subprocess.Popen(["dch", bug_desc], env=dch_env).communicate()

    dch_env["DEBFULLNAME"] = BOT_DEBFULLNAME
    dch_env["DEBEMAIL"] = BOT_DEBEMAIL
    subprocess.Popen(["dch", "-v{}".format(new_package_version), "{}{}".format(REV_STRING_FORMAT, tip_bzr_rev)],
                      env=dch_env).communicate()
    subprocess.call(["dch", "-r", "--distribution", serie, ""], env=dch_env)

