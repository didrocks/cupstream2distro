# -*- coding: UTF8 -*-
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

import datetime
import os
import re
import subprocess

from .launchpadmanager import get_serie, get_ubuntu_archive
from .settings import REV_STRING_FORMAT, BOT_DEBFULLNAME, BOT_DEBEMAIL, BOT_KEY, GNUPG_DIR, REPLACEME_TAG


def get_current_version_for_serie(source_package_name, serie_name):
    '''Get current version for a package name in that serie'''
    serie = get_serie(serie_name)
    version = None
    for source in get_ubuntu_archive().getPublishedSources(status="Published", exact_match=True, source_name=source_package_name, distro_series=serie):
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
    last_bzr_rev = None
    for line in f:
        rev = regex.findall(line)
        if rev:
            last_bzr_rev = int(rev[0])
        # end of current changelog stenza
        if line.startswith(" -- "):
            break

    # we are taking the last added one to the changelog for bootstrapping: we have two rev in the case on the first upload and we just want the last one
    if last_bzr_rev:
        return last_bzr_rev

    raise Exception("Didn't find any string in debian/changelog of the form: \"{}\". Bootstrapping issue?".format(regex.pattern))


def list_packages_info_in_str(packages_set):
    '''Return the packages info in a string'''

    results = []
    for package in packages_set:
        results.append("{} ({})".format(package.source_name, package.version))
    return " ".join(results)


def get_packaging_version():
    '''Get current packaging rev'''
    instance = subprocess.Popen(["dpkg-parsechangelog"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
    expr = re.compile("Version: (.*)")
    for line in stdout.splitlines():
        packaging_version = expr.findall(line)
        if packaging_version:
            return packaging_version[0]

    raise Exception("Didn't find any Version in the package: {}".format(stdout))


def create_new_packaging_version(previous_package_version):
    '''Deliver a new packaging version, based on simple rules:

    Version would be <upstream_version>daily<yy.mm.dd(.minor)>-0ubuntu1
    if we already have something delivered today, it will be .minor, then, .minor+1…'''

    today_version = datetime.date.today().strftime('%y.%m.%d')
    # bootstrapping mode or direct upload or UNRELEASED for bumping to a new serie
    if not "daily" in previous_package_version:
        upstream_version = previous_package_version.split('-')[0]
    else:
        # extract the day of previous daily upload and bump if already uploaded today
        regexp = re.compile("(.*)daily([\d\.]{8})([.\d]*)-.*")
        previous_day = regexp.findall(previous_package_version)
        if not previous_day:
            raise Exception("Didn't find a correct versioning in the current package: {}".format(previous_package_version))
        previous_day = previous_day[0]
        upstream_version = previous_day[0]
        if previous_day[1] == today_version:
            minor = 1
            if previous_day[2]:  # second upload of the day
                minor = int(previous_day[2][1:]) + 1
            today_version = "{}.{}".format(today_version, minor)

    return "{}daily{}-0ubuntu1".format(upstream_version, today_version)


def get_packaging_sourcename():
    '''Get current packaging source name'''
    instance = subprocess.Popen(["dpkg-parsechangelog"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
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
    instance = subprocess.Popen(["dch", "-v{}".format(new_package_version), "{}{}".format(REV_STRING_FORMAT, tip_bzr_rev)],
                                stderr=subprocess.PIPE, env=dch_env)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
    subprocess.call(["dch", "-r", "--distribution", serie, ""], env=dch_env)


def build_package(serie):
    '''Build the source package using the internal helper'''

    chroot_tool_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "chroot-tools")
    buildsource = os.path.join(chroot_tool_dir, "buildsource-chroot")
    cur_dir = os.path.abspath('.')
    cowbuilder_env = os.environ.copy()
    cowbuilder_env["HOME"] = chroot_tool_dir  # take the internal .pbuilderrc
    cowbuilder_env["DIST"] = serie
    instance = subprocess.Popen(["sudo", "-E", "cowbuilder", "--execute", "--bindmounts", cur_dir, "--bindmounts", GNUPG_DIR,
                        "--", buildsource, cur_dir, "--gnupg-parentdir", GNUPG_DIR, "--uid", str(os.getuid()), "--gid", str(os.getgid()),
                                           "--gnupg-keyid", BOT_KEY], env=cowbuilder_env)
    instance.communicate()
    if instance.returncode != 0:
        raise Exception("The above command returned an error.")


def upload_package(source, version, ppa):
    '''Upload the new package to a ppa'''
    if subprocess.call(["dput", "ppa:{}".format(ppa), "{}_{}_source.changes".format(source, version)]) != 0:
        raise Exception("The above command returned an error.")


def refresh_symbol_files(packaging_version):
    '''Refresh the symbols file having REPLACEME_TAG with version of the day.

    Add a changelog entry if needed'''

    new_upstream_version = packaging_version.split("-")[0]
    if subprocess.call(['grep -qi {} debian/*symbols'.format(REPLACEME_TAG)], shell=True) == 0:  # shell=True for shell expansion
        subprocess.call(["sed -i 's/{}\(.*\)/{}/i' debian/*symbols".format(REPLACEME_TAG, new_upstream_version)], shell=True)
        dch_env = os.environ.copy()
        dch_env["DEBFULLNAME"] = BOT_DEBFULLNAME
        dch_env["DEBEMAIL"] = BOT_DEBEMAIL
        subprocess.Popen(["dch", "debian/*symbols: auto-update new symbols to released version"], env=dch_env).communicate()
        subprocess.call(["bzr", "commit", "-m", "Update symbols"])
