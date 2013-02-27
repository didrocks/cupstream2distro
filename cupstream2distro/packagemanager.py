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
import logging
import os
import re
import subprocess

try:
    from ubuntutools.lp.lpapicache import Launchpad
    from ubuntutools.archive import UbuntuSourcePackage
except ImportError:
    Launchpad = None
    UbuntuSourcePackage = None

from .launchpadmanager import get_launchpad, get_series, get_ubuntu_archive, get_ppa
from .settings import REV_STRING_FORMAT, BOT_DEBFULLNAME, BOT_DEBEMAIL, BOT_KEY, GNUPG_DIR, REPLACEME_TAG, ROOT_CU2D, NEW_CHANGELOG_PATTERN
from .tools import get_packaging_diff_filename


def get_current_version_for_series(source_package_name, series_name, ppa_name=None):
    '''Get current version for a package name in that series'''
    series = get_series(series_name)
    version = None
    if ppa_name:
        dest = get_ppa(ppa_name)
    else:
        dest = get_ubuntu_archive()
    for source in dest.getPublishedSources(status="Published", exact_match=True, source_name=source_package_name, distro_series=series):
        if version:
            if is_version1_higher_than_version2(source.source_package_version, version):
                version = source.source_package_version
        else:
            version = source.source_package_version
    # was never in the dest, set the lowest possible version
    if version is None:
        version = "0"
    return version


def is_version1_higher_than_version2(version1, version2):
    '''return if version1 is higher than version2'''
    return (subprocess.call(["dpkg", "--compare-versions", version1, 'gt', version2], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0)


def is_version_in_changelog(version, f):
    '''Return if the version is in the upstream changelog (released)'''

    if version == "0":
        return True

    desired_changelog_line = re.compile("\({}\) (?!UNRELEASED).*\; urgency=".format(version))
    for line in f:
        if desired_changelog_line.search(line):
            return True

    return False


def get_latest_upstream_bzr_rev(f):
    '''Report latest bzr rev in the file'''
    regex = re.compile(REV_STRING_FORMAT + "(\d+)")
    last_bzr_rev = None
    for line in f:
        rev = regex.findall(line)
        if rev:
            last_bzr_rev = int(rev[0])
        # end of current changelog stenza (doesn't have last_bzr_rev if cherry-pick from distro)
        if last_bzr_rev and line.startswith(" -- "):
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


def get_source_package_from_distro(source_package_name, distro_version, series):
    '''Download and return a path containing a checkout of the current distro version.

    None if this package was never published to distro'''

    if distro_version == "0":
        logging.info("This package was never released to the distro, don't return downloaded source")
        return None

    logging.info("Grab code for {} ({}) from {}".format(source_package_name, distro_version, series))
    source_package_download_dir = os.path.join('ubuntu', source_package_name)
    try:
        os.makedirs(source_package_download_dir)
    except OSError:
        pass
    os.chdir(source_package_download_dir)

    if not Launchpad or not UbuntuSourcePackage:
        raise Exception("Launchpad tool from ubuntutools doesn't seem to be installed, we won't be able to pull the source and complete the operation")
    Launchpad.login_existing(lp=get_launchpad())
    logging.info('Downloading %s version %s', source_package_name, distro_version)
    srcpkg = UbuntuSourcePackage(source_package_name, distro_version)
    srcpkg.pull()
    srcpkg.unpack()

    # check the dir exist
    splitted_version = distro_version.split(':')[-1].split('-')  # remove epoch is there is one
    # TODO: debian version (like -3) is not handled here.
    if "ubuntu" in splitted_version[-1]:  # don't remove last item for the case where we had a native version (-0.35.2) without ubuntu in it
        splitted_version = splitted_version[:-1]
    version_for_source_file = '-'.join(splitted_version)
    source_directory_name = "{}-{}".format(source_package_name, version_for_source_file)
    if not os.path.isdir(source_directory_name):
        raise Exception("We tried to download and check that the directory {} is present, but it's not the case".format(source_directory_name))
    os.chdir('../..')
    return (os.path.join('..', source_package_download_dir, source_directory_name))


def is_new_release_needed(tip_bzr_rev, last_upstream_rev, source_package_name, ubuntu_version_source):
    '''Return True if a new snapshot is needed

    ubuntu_version_source can be None if no released version was done before.

    This will assume that backported version in distro are in the current branch and that it's been backported
    in a single commit'''

    # Note we always at least have +1 revision from last_upstream_rev (automated merge of changelog)

    # we always released something not yet in ubuntu, no matter criterias are not met.
    if not ubuntu_version_source:
        return True

    num_uploads = 0
    regex = re.compile(REV_STRING_FORMAT + "(\d+)")
    new_changelog_regexp = re.compile(NEW_CHANGELOG_PATTERN.format(source_package_name))
    for line in open("debian/changelog"):
        if regex.search(line):
            break
        # end of a changelog stenza (without getting the automated tag) means a manual upload
        if new_changelog_regexp.match(line):
            num_uploads += 1

    # num_uploads will at least be 1 for the last automated release merge in changelog
    # + the number of manual uploads, relying on the fact that a manual upload backported
    # is done in one commit.
    if not tip_bzr_rev > last_upstream_rev + num_uploads:
        return False

    # now check the relevance of the committed changes compared to the version in the repository (if any)
    diffinstance = subprocess.Popen(['diff', '-Nrup', '.', ubuntu_version_source], stdout=subprocess.PIPE)
    filterinstance = subprocess.Popen(['filterdiff', '--clean', '-x', '*changelog', '-x', '*po', '-x', '*pot'], stdin=diffinstance.stdout, stdout=subprocess.PIPE)
    lsdiffinstance = subprocess.Popen(['lsdiff'], stdin=filterinstance.stdout, stdout=subprocess.PIPE)
    (relevant_changes, err) = subprocess.Popen(['grep', '-v', '.bzr'], stdin=lsdiffinstance.stdout, stdout=subprocess.PIPE).communicate()
    return (relevant_changes != '')


def create_new_packaging_version(previous_package_version):
    '''Deliver a new packaging version, based on simple rules:

    Version would be <upstream_version>daily<yy.mm.dd(.minor)>-0ubuntu1
    if we already have something delivered today, it will be .minor, then, .minor+1…'''

    today_version = datetime.date.today().strftime('%y.%m.%d')
    # bootstrapping mode or direct upload or UNRELEASED for bumping to a new series
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
    new_changelog_regexp = re.compile(NEW_CHANGELOG_PATTERN.format(source_package_name))
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


def update_changelog(new_package_version, series, tip_bzr_rev, authors_bugs_with_title):
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
    subprocess.call(["dch", "-r", "--distribution", series, "--force-distribution", ""], env=dch_env)


def build_package(series):
    '''Build the source package using the internal helper'''

    chroot_tool_dir = os.path.join(ROOT_CU2D, "chroot-tools")
    buildsource = os.path.join(chroot_tool_dir, "buildsource-chroot")
    cur_dir = os.path.abspath('.')
    cowbuilder_env = os.environ.copy()
    cowbuilder_env["HOME"] = chroot_tool_dir  # take the internal .pbuilderrc
    cowbuilder_env["DIST"] = series
    instance = subprocess.Popen(["sudo", "-E", "cowbuilder", "--execute", "--bindmounts", cur_dir, "--bindmounts", GNUPG_DIR,
                        "--", buildsource, cur_dir, "--gnupg-parentdir", GNUPG_DIR, "--uid", str(os.getuid()), "--gid", str(os.getgid()),
                                           "--gnupg-keyid", BOT_KEY], env=cowbuilder_env)
    instance.communicate()
    if instance.returncode != 0:
        raise Exception("The above command returned an error.")


def upload_package(source, version, ppa):
    '''Upload the new package to a ppa'''
    # remove epoch is there is one
    version_for_source_file = version.split(':')[-1]
    if subprocess.call(["dput", "ppa:{}".format(ppa), "{}_{}_source.changes".format(source, version_for_source_file)]) != 0:
        raise Exception("The above command returned an error.")


def refresh_symbol_files(packaging_version):
    '''Refresh the symbols file having REPLACEME_TAG with version of the day.

    Add a changelog entry if needed'''

    new_upstream_version = packaging_version.split("-")[0]
    if subprocess.call(['grep -qi {} debian/*symbols'.format(REPLACEME_TAG)], shell=True) == 0:  # shell=True for shell expansion
        if subprocess.call(["sed -i 's/{}\(.*\)/{}/i' debian/*symbols".format(REPLACEME_TAG, new_upstream_version)], shell=True) != 0:
            raise Exception("The above command returned an error.")
        dch_env = os.environ.copy()
        dch_env["DEBFULLNAME"] = BOT_DEBFULLNAME
        dch_env["DEBEMAIL"] = BOT_DEBEMAIL
        subprocess.Popen(["dch", "debian/*symbols: auto-update new symbols to released version"], env=dch_env).communicate()
        subprocess.call(["bzr", "commit", "-m", "Update symbols"])


def get_global_packaging_change_status(source_version_list):
    '''Return global package change status list

    source_version_list is a list of couples (source, version)'''

    packaging_change_status = []
    for (source, version) in source_version_list:
        if os.path.exists(get_packaging_diff_filename(source, version)):
            message = "Packaging change for {} ({}).".format(source, version)
            logging.warning(message)
            packaging_change_status.append(message)
    return packaging_change_status
