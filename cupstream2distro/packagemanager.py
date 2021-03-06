# -*- coding: utf-8 -*-
# Copyright (C) 2012-2014 Canonical
#
# Authors:
#  Didier Roche
#  Rodney Dawes
#  Łukasz 'sil2100' Zemczak
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
import fileinput
import logging
from operator import attrgetter
import os
import re
import shutil
import sys
import subprocess
import urllib
import socket

import launchpadmanager
import settings
from .utils import ignored
import silomanager


def sort_by_date_created(sources, all_packages=False):
    # we also filter out any non-published or not-pending packages by default
    if not all_packages:
        filtered_sources = filter(lambda x: x.status == "Published" or x.status == "Pending", sources)
    else:
        filtered_sources = sources
    return sorted(filtered_sources, key=attrgetter("date_created"), reverse=True)


def get_current_version_for_series(source_package_name, series_name, ppa_name=None, dest=None):
    '''Get current version for a package name in that series'''
    if not dest:
        if ppa_name:
            dest = launchpadmanager.get_ppa(ppa_name)
        else:
            dest = launchpadmanager.get_ubuntu_archive()
    series = launchpadmanager.get_series(series_name, dest.distribution.name)
    source_collection = dest.getPublishedSources(exact_match=True, source_name=source_package_name, distro_series=series)
    try:
        return sort_by_date_created(source_collection)[0].source_package_version
    # was never in the dest, set the lowest possible version
    except IndexError:
        return "0"


def is_version_for_series_in_dest(source_package_name, version, series, dest, pocket="Release"):
    '''Return if version for a package name in that series is in dest'''
    return dest.getPublishedSources(exact_match=True, source_name=source_package_name, version=version,
                                    distro_series=series, pocket=pocket).total_size > 0

def is_version_in_queue(source_package_name, version, dest_serie, queue):
    '''Return if version for a package name in that series is in dest'''
    return dest_serie.getPackageUploads(exact_match=True, name=source_package_name, version=version,
                                        status=queue).total_size > 0


def is_version1_higher_than_version2(version1, version2):
    '''return if version1 is higher than version2'''
    return (subprocess.call(["dpkg", "--compare-versions", version1, 'gt', version2], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0)


def is_version_in_changelog(version, f):
    '''Return if the version is in the upstream changelog (released)'''

    if version == "0":
        return True

    desired_changelog_line = re.compile("\({}\) (?!UNRELEASED).*\; urgency=".format(version.replace('+', '\+')))
    for line in f.readlines():
        if desired_changelog_line.search(line):
            return True

    return False


def get_latest_upstream_bzr_rev(f, dest_ppa=None):
    '''Report latest bzr rev in the file

    If dest_ppa, first try to fetch the dest ppa tag. Otherwise, fallback to first distro version'''
    distro_regex = re.compile("{} (\d+)".format(settings.REV_STRING_FORMAT))
    destppa_regexp = re.compile("{} (\d+) \(ppa:{}\)".format(settings.REV_STRING_FORMAT, dest_ppa))
    distro_rev = None
    candidate_destppa_rev = None
    candidate_distro_rev = None
    destppa_element_found = False

    # handle marker spread on two lines
    end_of_line_regexp = re.compile(" *(.*\))")
    previous_line = None

    for line in f:
        line = line[:-1]

        if previous_line:
            try:
                line = previous_line + end_of_line_regexp.findall(line)[0]
            except IndexError:
                None
            previous_line = None

        if dest_ppa:
            try:
                candidate_destppa_rev = int(destppa_regexp.findall(line)[0])
                destppa_element_found = True
            except IndexError:
                destppa_element_found = False
        if not distro_rev and not destppa_element_found and not "(ppa:" in line:
            try:
                candidate_distro_rev = int(distro_regex.findall(line)[0])
                distro_element_found = True
            except IndexError:
                distro_element_found = False

        # try to catchup next line if we have a marker start without anything found
        if settings.REV_STRING_FORMAT in line and (dest_ppa and not destppa_element_found) and not distro_element_found:
            previous_line = line

        if line.startswith(" -- "):
            # first grab the dest ppa
            if candidate_destppa_rev:
                return candidate_destppa_rev
            if not distro_rev and candidate_distro_rev:
                distro_rev = candidate_distro_rev
            if not dest_ppa and distro_rev:
                return distro_rev

    # we didn't find any dest ppa result but there is a distro_rev one
    if dest_ppa and distro_rev:
        return distro_rev

    # we force a bootstrap commit for new components
    return 0


def list_packages_info_in_str(packages_set):
    '''Return the packages info in a string'''

    results = []
    for package in packages_set:
        results.append("{} ({})".format(package.source_name, package.version))
    return " ".join(results)


def get_packaging_version():
    '''Get current packaging version'''
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

def get_upstream_version(version, remove_epoch=True):
    """Return upstream version"""

    if remove_epoch:
        version = version.split(':')[-1]  # remove epoch is there is one
    splitted_version = version.split('-')
    if len(splitted_version) > 1:
        splitted_version = splitted_version[:-1]  # we don't want the ubuntu or debian version (it's not in the source package name)
    return '-'.join(splitted_version)


def get_source_package_from_dest(source_package_name, dest_archive, dest_current_version, series_name, download_dir='ubuntu'):
    '''Download and return a path containing a checkout of the current dest version.

    None if this package was never published to dest archive'''

    if dest_current_version == "0":
        logging.info("This package was never released to the destination archive, don't return downloaded source")
        return None

    logging.info("Grab code for {} ({}) from {} to the '{}' directory".format(source_package_name, dest_current_version, series_name, download_dir))
    source_package_download_dir = os.path.join(download_dir, source_package_name)
    series = launchpadmanager.get_series(series_name, dest_archive.distribution.name)
    with ignored(OSError):
        os.makedirs(source_package_download_dir)
    os.chdir(source_package_download_dir)

    try:
        sourcepkg = sort_by_date_created(dest_archive.getPublishedSources(exact_match=True, source_name=source_package_name, distro_series=series, version=dest_current_version), True)[0]
    except IndexError:
        raise Exception("Couldn't get in the destination the expected version")
    logging.info('Downloading %s version %s', source_package_name, dest_current_version)
    for url in sourcepkg.sourceFileUrls():
        urllib.urlretrieve(url, urllib.unquote(url.split('/')[-1]))
    instance = subprocess.Popen("dpkg-source -x *dsc", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())

    # check the dir exist
    splitted_version = dest_current_version.split(':')[-1].split('-')  # remove epoch is there is one
    if len(splitted_version) > 1:
        splitted_version = splitted_version[:-1]  # we don't want the ubuntu or debian version (it's not in the source package name)
    version_for_source_file = '-'.join(splitted_version)
    source_directory_name = "{}-{}".format(source_package_name, version_for_source_file)
    if not os.path.isdir(source_directory_name):
        raise Exception("We tried to download and check that the directory {} is present, but it's not the case".format(source_directory_name))
    os.chdir('../..')
    return (os.path.join(source_package_download_dir, source_directory_name))


def is_new_content_relevant_since_old_published_source(dest_version_source):
    '''Return True if a new snapshot is needed

    dest_version_source can be None if no released version was done before.'''

    # we always released something not yet in ubuntu, no matter criterias are not met.
    if not dest_version_source:
        return True

    # now check the relevance of the committed changes compared to the version in the repository (if any)
    diffinstance = subprocess.Popen(['diff', '-Nrup', '.', dest_version_source], stdout=subprocess.PIPE)
    filterinstance = subprocess.Popen(['filterdiff', '--clean', '-x', '*po', '-x', '*pot', '-x', '*local-options'], stdin=diffinstance.stdout, stdout=subprocess.PIPE)
    lsdiffinstance = subprocess.Popen(['lsdiff'], stdin=filterinstance.stdout, stdout=subprocess.PIPE)
    (relevant_changes, err) = subprocess.Popen(['grep', '-Ev', '.bzr|.pc'], stdin=lsdiffinstance.stdout, stdout=subprocess.PIPE).communicate()

    # detect if the only change is a Vcs* target changes (with or without changelog edit). We won't release in that case
    number_of_changed_files = relevant_changes.count("\n")
    if ((number_of_changed_files == 1 and "debian/control" in relevant_changes) or
       (number_of_changed_files == 2 and "debian/control" in relevant_changes and "debian/changelog" in relevant_changes)):
        (results, err) = subprocess.Popen(['diff', os.path.join('debian', 'control'), os.path.join(dest_version_source, "debian", "control")], stdout=subprocess.PIPE).communicate()
        for diff_line in results.split('\n'):
            if diff_line.startswith("< ") or diff_line.startswith("> "):
                if not diff_line[2:].startswith("Vcs-") and not diff_line[2:].startswith("#"):
                    return True
        return False

    logging.debug("Relevant changes are:")
    logging.debug(relevant_changes)

    return (relevant_changes != '')


def is_relevant(newdsc_path, dest_version_source):
    '''Extract and check if the generated source diff different from previous one'''

    with ignored(OSError):
        os.makedirs("generated")
    extracted_generated_source = os.path.join("generated", newdsc_path.split('_')[0])
    with ignored(OSError):
        shutil.rmtree(extracted_generated_source)

    # remove epoch is there is one
    if subprocess.call(["dpkg-source", "-x", newdsc_path, extracted_generated_source]) != 0:
        raise Exception("dpkg-source command returned an error.")

    # now check the relevance of the committed changes compared to the version in the repository (if any)
    diffinstance = subprocess.Popen(['diff', '-Nrup', extracted_generated_source, dest_version_source], stdout=subprocess.PIPE)
    (diff, err) = subprocess.Popen(['filterdiff', '--clean', '-x', '*po', '-x', '*pot', '-x', '*local-options'], stdin=diffinstance.stdout, stdout=subprocess.PIPE).communicate()

    # there is no important diff if the diff only contains 12 lines, corresponding to "Automatic daily release" marker in debian/changelog
    if (diff.count('\n') <= 12):
        return False
    return True


def _packaging_changes_between_dsc(oldsource_dsc, newsource_dsc):
    '''Return if there has been a packaging change between two dsc files

    We ignore the changelog only changes'''
    if not oldsource_dsc:
        return True
    if not os.path.isfile(oldsource_dsc) or not os.path.isfile(newsource_dsc):
        raise Exception("{} or {} doesn't not exist, can't create a diff".format(oldsource_dsc, newsource_dsc))
    diffinstance = subprocess.Popen(['debdiff', oldsource_dsc, newsource_dsc], stdout=subprocess.PIPE)
    filterinstance = subprocess.Popen(['filterdiff', '--clean', '-i', '*debian/*', '-x', '*changelog'], stdin=diffinstance.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (change_in_debian, filter_err) = filterinstance.communicate()
    # we can't rely on diffinstance returncode as the signature key is maybe not present and it will exit with 1
    if filterinstance.returncode != 0:
        raise Exception("Error in diff: {}".format(filter_err.decode("utf-8").strip()))
    return(change_in_debian != "")


def generate_diff_between_dsc(diff_filepath, oldsource_dsc, newsource_dsc):
    '''Generate a diff file in diff_filepath if there is a relevant packaging diff between 2 sources

    The diff contains autotools files and cmakeries'''
    if _packaging_changes_between_dsc(oldsource_dsc, newsource_dsc):
        with open(diff_filepath, "a") as f:
            if not oldsource_dsc:
                f.writelines("This source is a new package, if the destination is ubuntu, please ensure it has been preNEWed by an archive admin before publishing that stack.")
                return
            f.write("/!\ Remember that this diff only represents packaging changes and build tools diff, not the whole content diff!\n\n")
            diffinstance = subprocess.Popen(['debdiff', oldsource_dsc, newsource_dsc], stdout=subprocess.PIPE)
            (changes_to_publish, err) = subprocess.Popen(['filterdiff', '--remove-timestamps', '--clean', '-i', '*setup.py',
                                                          '-i', '*Makefile.am', '-i', '*configure.*', '-i', '*debian/*',
                                                          '-i', '*CMakeLists.txt'], stdin=diffinstance.stdout, stdout=subprocess.PIPE).communicate()

            # look for any modifications that might mean a new binary package has appeared
            # TODO: make better, considering only changes for debian/control
            split_diff = changes_to_publish.split('\n')
            re_replace = re.compile('\+Package: *(.*)')
            new_binary_packages = []

            logging.debug("Looking for new binary packages in the diff")
            for line in split_diff:
                if line.startswith('+Package:'):
                    logging.debug("Found a new binary package")
                    reverse = '-' + line[1:]
                    if reverse in split_diff:
                        logging.debug("It seems to be a move, ignoring")
                        continue
                    new_binary_packages.append(re.sub(re_replace, '\\1', line))
            if new_binary_packages:
                f.write("(!) Warning! This package seems to add new binary packages ({}). Please consult an archive admin before proceeding!\n\n".format(', '.join(new_binary_packages)))

            f.write(changes_to_publish)


def check_if_packages_require_twin_upload(sources):
    '''This is an ugly method used for actually 'protecting' us from forgetting uploading the so-called twin packages of certain projects

    The most well known ones are the -gles counterparts for some Qt/UITK related packages'''
    twin_packages = { "qtbase-opensource-src": "qtbase-opensource-src-gles", "qtdeclarative-opensource-src": "qtdeclarative-opensource-src-gles",
        "qt3d-opensource-src": "qt3d-opensource-src-gles", "qtlocation-opensource-src": "qtlocation-opensource-src-gles",
        "qtubuntu": "qtubuntu-gles", "ubuntu-ui-toolkit": "ubuntu-ui-toolkit-gles", "qtmultimedia-opensource-src": "qtmultimedia-opensource-src-gles",
        "qtmir": "qtmir-gles" }

    missing = []
    for source in sources:
        if source in twin_packages:
            # Check if the twin package has been also uploaded
            if twin_packages[source] not in sources:
                missing.append(twin_packages[source])

    return missing


def create_new_packaging_version(base_package_version, series_version, destppa=''):
    '''Deliver a new packaging version, based on simple rules:

    Version would be <upstream_version>.<series>.<yyyymmdd(.minor)>-0ubuntu1
    if we already have something delivered today, it will be .minor, then, .minor+1…

    We append the destination ppa name if we target a dest ppa and not distro'''
    # to keep track of whether the package is native or not
    native_pkg = False

    # handle the special case of RTM
    special_tag = ""
    if series_version == "14.09":
        special_tag = "~rtm"
        series_version = "14.10" # XXX: we agreed that to keep the versioning sane, we need to stick to versioning as per the main archive

    today_version = datetime.date.today().strftime('%Y%m%d')
    destppa = destppa.replace("-", '.').replace("_", ".").replace("/", ".")
    # bootstrapping mode or direct upload or UNRELEASED for bumping to a new series
    # TRANSITION
    if not ("daily" in base_package_version or "+" in base_package_version):
        # support both 42, 42-0ubuntu1
        upstream_version = base_package_version.split('-')[0]
        # if we have 42ubuntu1 like a wrong native version
        if "ubuntu" in upstream_version:
            upstream_version = upstream_version.split('ubuntu')[0]
    elif not "-" in base_package_version and "+" in base_package_version:
        # extract the day of previous daily upload and bump if already uploaded
        regexp = re.compile("(.*)\+([\d\.]{5})\.(\d{8})\.?([\d]*).*")
        try:
            previous_day = regexp.findall(base_package_version)[0]
            upstream_version = previous_day[0]
            native_pkg = True
            if (previous_day[1] == series_version and
                previous_day[2] == today_version):
                minor = 1
                if previous_day[3]:  # second upload of the day
                    minor = int(previous_day[3]) + 1
                today_version = "{}.{}".format(today_version, minor)
        except IndexError:
            raise Exception(
                "Unable to get previous day from native version: %s"
                % base_package_version)
    else:
        # extract the day of previous daily upload and bump if already uploaded today
        regexp = re.compile("(.*)\+([\d\.]{5})\.(\d{8})\.?([\d]*).*-.*")
        try:
            previous_day = regexp.findall(base_package_version)[0]
            logging.debug('Value of previous_day: ' + ','.join(previous_day))
        except IndexError:
            # TRANSITION FALLBACK
            try:
                regexp = re.compile("(.*)(daily)([\d\.]{8})\.?([\d]*).*-.*")
                previous_day = regexp.findall(base_package_version)[0]
                # make the version compatible with the new version
                previous_day = (previous_day[0], previous_day[1], "20" + previous_day[2].replace(".", ""), previous_day[3])
                logging.debug('Value of previous_day: ' + ','.join(previous_day))
            except IndexError:
                raise Exception("Didn't find a correct versioning in the current package: {}".format(base_package_version))
        upstream_version = previous_day[0]
        upstream_version = upstream_version.split('+')[0]
        logging.debug('Value of upstream_version: ' + upstream_version)
        logging.debug('Value of previous_day[1]: ' + previous_day[1])
        logging.debug('Value of series_version: ' + series_version)
        logging.debug('Value of previous_day[2]: ' + previous_day[2])
        logging.debug('Value of today_version: ' + today_version)
        if previous_day[1] == series_version and previous_day[2] == today_version:
            minor = 1
            if previous_day[3]:  # second upload of the day
                minor = int(previous_day[3]) + 1
            today_version = "{}.{}".format(today_version, minor)
            logging.debug('Value of today_version after increment: ' + today_version)

    new_upstream_version = "{upstream}+{series}.{date}{destppa}{special}".format(
        upstream=upstream_version, series=series_version,
        date=today_version, destppa=destppa, special=special_tag)
    if native_pkg is not True:
        new_upstream_version = "{}-0ubuntu1".format(new_upstream_version)

    logging.debug('Returning new_upstream_version: ' + new_upstream_version)
    return new_upstream_version


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


def collect_bugs(f, source_package_name):
    '''Collect all bugs in the changelog until latest snapshot'''
    bugs = set()
    # matching only bug format that launchpad accepts
    group_bugs_regexp = re.compile("lp: ?(.*\d{5,})", re.IGNORECASE)
    bug_decipher_regexp = re.compile("(#\d{5,})+")
    new_upload_changelog_regexp = re.compile(settings.NEW_CHANGELOG_PATTERN.format(source_package_name))
    for line in f:
        grouped_bugs_list = group_bugs_regexp.findall(line)
        for grouped_bugs in grouped_bugs_list:
            for bug in map(lambda bug_with_hash: bug_with_hash.replace('#', ''), bug_decipher_regexp.findall(grouped_bugs)):
                bugs.add(bug)
        #  a released upload to distro (automated or manual)n exit as bugs before were already covered
        if new_upload_changelog_regexp.match(line):
            return bugs

    return bugs


def update_changelog(new_package_version, series, tip_bzr_rev, authors_commits, dest_ppa=None):
    '''Update the changelog for the incoming upload'''

    dch_env = os.environ.copy()
    for author in authors_commits:
        dch_env["DEBFULLNAME"] = author
        for bug_desc in authors_commits[author]:
            if bug_desc.startswith('-'):
                # Remove leading '-' or dch thinks (rightly) that it's an option
                bug_desc = bug_desc[1:]
            if bug_desc.startswith(' '):
                # Remove leading spaces, there are useless and the result is
                # prettier without them anyway ;)
                bug_desc = bug_desc.strip()
            cmd = ["dch", "--multimaint-merge", "--release-heuristic", "changelog",
                   "-v{}".format(new_package_version), bug_desc]
            subprocess.Popen(cmd, env=dch_env).communicate()

    if tip_bzr_rev != None:
        commit_message = "{} {}".format(settings.REV_STRING_FORMAT, tip_bzr_rev)
        if dest_ppa:
            commit_message += " ({})".format(dest_ppa)
    else:
        commit_message = ""

    dch_env["DEBFULLNAME"] = settings.BOT_DEBFULLNAME
    dch_env["DEBEMAIL"] = settings.BOT_DEBEMAIL
    instance = subprocess.Popen(["dch", "--release-heuristic", "changelog",
                                 "-v{}".format(new_package_version), commit_message],
                                stderr=subprocess.PIPE, env=dch_env)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
    subprocess.call(["dch", "-r", "--distribution", series, "--force-distribution", ""], env=dch_env)

    # in the case of no commit_message and no symbols file change, we have an addition [ DEBFULLNAME ] follow by an empty line
    # better to remove both lines
    subprocess.call(["sed", "-i", "/ \[ " + settings.BOT_DEBFULLNAME + " \]/{$q; N; /\\n$/d;}", "debian/changelog"])


def build_source_package(series, distro_version, ppa=None):
    '''Build the source package using the internal helper

    Add the additional ppa inside the chroot if requested.'''

    chroot_tool_dir = os.path.join(settings.ROOT_CU2D, "chroot-tools")
    buildsource = os.path.join(chroot_tool_dir, "buildsource-chroot")
    branch_dir = os.path.abspath('.')
    parent_dir = os.path.abspath(os.path.dirname(branch_dir))
    cowbuilder_env = os.environ.copy()
    cowbuilder_env["HOME"] = chroot_tool_dir  # take the internal .pbuilderrc
    cowbuilder_env["DIST"] = series
    cmd = ["sudo", "-E", "cowbuilder", "--execute",
           "--bindmounts", parent_dir,
           "--bindmounts", settings.GNUPG_DIR,
           "--", buildsource, branch_dir,
           "--gnupg-parentdir", settings.GNUPG_DIR,
           "--uid", str(os.getuid()), "--gid", str(os.getgid()),
           "--gnupg-keyid", settings.BOT_KEY,
           "--distro-version", distro_version]
    if ppa:
        cmd.extend(["--ppa", ppa])
    instance = subprocess.Popen(cmd, env=cowbuilder_env)
    instance.communicate()
    if instance.returncode != 0:
        raise Exception("%r returned: %s." % (cmd, instance.returncode))


def upload_package(source, version, ppa, path="."):
    '''Upload the new package to a ppa'''
    # remove epoch is there is one
    version_for_source_file = version.split(':')[-1]
    cmd = ["dput", "ppa:{}".format(ppa),
           "{}/{}_{}_source.changes".format(path, source, version_for_source_file)]
    if subprocess.call(cmd) != 0:
        raise Exception("%r returned an error." % (cmd,))


def refresh_symbol_files(packaging_version):
    '''Refresh the symbols file having REPLACEME_TAG with version of the day.

    Add a changelog entry if needed'''

    new_upstream_version = packaging_version.split("-")[0]
    files_replaced = set()
    for filename in os.listdir("debian"):
        path = os.path.join('debian', filename)
        if not os.path.isfile(path) or os.path.islink(path):
            continue
        for line in fileinput.input(path, inplace=1):
            if settings.REPLACEME_TAG in line:
                files_replaced.add(filename)
                line = line.replace(settings.REPLACEME_TAG, new_upstream_version)
            sys.stdout.write(line)

    if files_replaced:
        dch_env = os.environ.copy()
        dch_env["DEBFULLNAME"] = settings.BOT_DEBFULLNAME
        dch_env["DEBEMAIL"] = settings.BOT_DEBEMAIL
        for filename in files_replaced:
            subprocess.Popen(["dch", "--release-heuristic", "changelog",
                "debian/{}: auto-update to released version".format(filename)],
                env=dch_env).communicate()
        subprocess.call(["bzr", "commit", "-m", "Replaced 0replaceme with real versions."])


def has_dont_change_version_flag():
    '''Return true if debian/control has a "don't change versionning" flag'''
    for line in open("debian/control").readlines():
        if line.startswith(settings.AUTOUPLOAD_CONTROL_TAG):
            if settings.NO_REWRITE_VERSION_TAG in line:
                return True
    return False


def check_package_reached_destination(silo_config, packages_in_dest, ignoremissingprojects, ignorepackagesnotindest, for_merge_and_clean=False):
    '''Return (True, "All packages in destination") if all packages have reached the destination. Otherwise, return (False, message)'''

    all_silo_projects = silomanager.get_all_projects(silo_config)

    # check that all package sources were in the silo configuration
    logging.info("Check that all package sources were in the silo configuration")
    if "source_sync_from_silo" not in silo_config:
        for source in packages_in_dest:
            try:
                all_silo_projects.remove(source)
            except ValueError:
                message = "{} wasn't in the initiale configuration. You have messed with the file system directly.\nUnknown state. Please resolve the silo manually and then free it.".format(source)
                logging.error(message)
                return (False, "Can't check migration: " + message)
    else:
        logging.info("Sync request from silo, checking all uploaded projects.")

    # additional check for merge and clean, we want all projects in silo configuration to be built and published
    if for_merge_and_clean and all_silo_projects:
        message = "Some projects ({}) that were in the silo configuration list were not built and published. ".format(", ".join(all_silo_projects))
        if ignoremissingprojects:
            logging.info(message + "The ignore missing projects flag was set. We won't merged the associated MPs of those.")
            # remove them as we are not going to merge their content.
            for remaining_project in all_silo_projects:
                with ignored(KeyError):
                    silo_config["mps"].pop(remaining_project)
                with ignored(ValueError):
                    silo_config["sources"].remove(remaining_project)
        else:
            logging.error(message + "Prepare either prepare the latest missing projects or use the ignore missing projects flag which will release the lock on them.")
            return (False, "Can't merge: " + message)

    logging.info("Check that all package sources are published in destination")
    one_package_not_in_dest = False
    dest_link = silo_config['global']['dest']
    dest = launchpadmanager.get_resource_from_token(dest_link)
    series = launchpadmanager.get_resource_from_token(silo_config['global']['series'])
    additional_messages = ""
    for source in packages_in_dest:
        if (not is_version_for_series_in_dest(source, packages_in_dest[source], series, dest) and
            not is_version_for_series_in_dest(source, packages_in_dest[source], series, dest, pocket="Updates")):
            logging.warning("{} ({}) is not published yet in {} (Release pocket).".format(source, packages_in_dest[source], dest.name))
            one_package_not_in_dest = True

            # if destination is the archive, try to check if it's in proposed or in any queue
            if launchpadmanager.is_dest_distro_archive(dest_link):
                if is_version_for_series_in_dest(source, packages_in_dest[source], series, dest, pocket="Proposed"):
                    in_proposed_msg = "{} ({}) is in the proposed pocket. ".format(source, packages_in_dest[source])
                    logging.warning(in_proposed_msg + "You run that job either too quickly or it's stuck there. More information available at https://wiki.ubuntu.com/ProposedMigration.")
                    additional_messages += in_proposed_msg
                elif is_version_in_queue(source, packages_in_dest[source], series, "New"):
                    in_new_msg = "{} ({}) is in the NEW queue. ".format(source, packages_in_dest[source])
                    logging.warning(in_new_msg + "You need an archive admin to review a NEW this package.")
                    additional_messages += in_new_msg
                elif is_version_in_queue(source, packages_in_dest[source], series, "Unapproved"):
                    in_unapproved_msg = "{} ({}) is in the UNAPPROVED queue. ".format(source, packages_in_dest[source])
                    logging.warning(in_unapproved_msg + "You need a release team member to review an approve it. We are probably in a freeze period.")
                    additional_messages += in_unapproved_msg
                else:
                    in_unknown_msg = "{} ({}) is in no known space (and time). ".format(source, packages_in_dest[source])
                    logging.warning(in_unknown_msg + "We didn't find it anywhere. It could have been rejected, or you run it too quickly and it's not published in proposed yet, or a network issue happened. If this persistent some time after the publication, you need to ping a landing team member to get more informations.")
                    additional_messages += in_unknown_msg

    if one_package_not_in_dest:
        if for_merge_and_clean and ignorepackagesnotindest:
            logging.info("The ignore flag is set.")
        else:
            # this is an error for merge and clean, just a warning for automated check
            message = "One package at least is not available at the destination. "
            if for_merge_and_clean:
                logging.error(message + "See above. You can use the ignore package not in dest flag. The eventual merge will still be proceeded.")
                return (False, "Can't merge: " + message + additional_messages)
            else:
                logging.warning(message + "See above. You can use the ignore package not in dest flag in \"merge and clean\". The eventual merge will still be proceeded.")
                return (False, message + additional_messages)
    return (True, "All packages are in destination. You can Merge and Clean now.")
