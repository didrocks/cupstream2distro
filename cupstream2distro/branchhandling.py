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

import ConfigParser
import logging
import os
import re
import subprocess

from packagemanager import collect_bugs_until_latest_bzr_rev
from .settings import BRANCH_URL, PACKAGING_MERGE_COMMIT_MESSAGE, PROJECT_CONFIG_SUFFIX, REV_STRING_FORMAT
from .tools import get_packaging_diff_filename


def get_branch(branch_url, dest_dir):
    '''Grab a branch'''
    instance = subprocess.Popen(["bzr", "branch", branch_url, dest_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())


def get_tip_bzr_revision():
    '''Get latest revision in bzr'''
    instance = subprocess.Popen(["bzr", "log", "-c", "-1", "--line"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
    return (int(stdout.split(':')[0]))


def _packaging_changes_in_branch(starting_rev):
    '''Return if there has been a packaging change

    We ignore the changelog only changes'''
    bzrinstance = subprocess.Popen(['bzr', 'diff', 'debian/', '-r', str(starting_rev)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    filterinstance = subprocess.Popen(['filterdiff', '--clean', '-x', '*changelog'], stdin=bzrinstance.stdout, stdout=subprocess.PIPE)
    (change_in_debian, filter_err) = filterinstance.communicate()
    (bzrout, bzrerr) = bzrinstance.communicate()
    if bzrerr or filterinstance.returncode != 0:
        bzrerror = ""
        filterdifferror = ""
        if bzrerr:
            bzrerror = bzrerr.decode("utf-8").strip()
        if filter_err:
            filterdifferror = filter_err.decode("utf-8").strip()
        raise Exception("Error in bzr diff: {}\nfilterdiff:{}".format(bzrerror, filterdifferror))
    return(change_in_debian != "")


def generate_diff_in_branch(starting_rev, source_package_name, packaging_version):
    '''Generate a diff file in the parent directory if the branch has packaging branch

    The diff contains autotools files and cmakeries'''
    if _packaging_changes_in_branch(starting_rev):
        with open("../{}".format(get_packaging_diff_filename(source_package_name, packaging_version)), "w") as f:
            bzrinstance = subprocess.Popen(['bzr', 'diff', '-r', str(starting_rev)], stdout=subprocess.PIPE)
            (changes_to_publish, err) = subprocess.Popen(['filterdiff', '--clean', '-i', 'setup.py',
                                        '-i', '*Makefile.am', '-i', 'configure.*', '-i', 'debian/*',
                                        '-i', '*CMakeLists.txt'], stdin=bzrinstance.stdout, stdout=f).communicate()


def collect_author_bugs(starting_rev, source_package_name):
    '''Collect a dict with authors fixing bugs since last release

    Form: {Author: set(bug_number, )}'''

    content_to_parse = _return_log_diff(starting_rev)
    author_bugs = _get_all_bugs_from_content(content_to_parse)
    with open("debian/changelog") as f:
        alreadyfixed_bugs = collect_bugs_until_latest_bzr_rev(f, source_package_name)

    # Remove bugs already fixed, discaring author if needed
    authors_to_remove = set()
    for author in author_bugs:
        author_bugs[author] = author_bugs[author] - alreadyfixed_bugs
        if not author_bugs[author]:
            authors_to_remove.add(author)
    for author in authors_to_remove:
        author_bugs.pop(author)
    return author_bugs


def _return_log_diff(starting_rev):
    '''Return the relevant part of the cvs log since starting_rev'''

    instance = subprocess.Popen(["bzr", "log", "-r", "{}..".format(starting_rev), "--include-merged", "--forward"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
    return stdout


def _get_all_bugs_from_content(content):
    '''Collect all bugs from the content string into a dict

    Form: {Author: set(bug_number)}'''

    results = {}
    bug_numbers = set()
    author = None

    # we are trying to match in the commit message:
    # bug #12345, bug#12345, bug12345, bug 12345
    # lp: #12345, lp:#12345, lp:12345, lp: 12345
    # lp #12345, lp#12345, lp12345, lp 12345,
    # Fix #12345, Fix 12345, Fix: 12345, Fix12345, Fix: #12345,
    # Fixes #12345, Fixes 12345, Fixes: 12345, Fixes:12345, Fixes: #12345
    # *launchpad.net/bugs/1234567890 and
    # #12345 (but not 12345 for false positive)
    # Support multiple bugs per commit
    bug_regexp = re.compile("((lp|bug|fix(es)?)[: #]*|#|launchpad.net/bugs/)(\d{5,})", re.IGNORECASE)
    # see lp:autopilot, rev 76, Only a committer:Tarmac and right author, we need to get the author in that case
    author_regexp = re.compile("(author|committer): (.*) <.*>")
    merge_trunk_commit_regex = re.compile(REV_STRING_FORMAT + "(\d+)")
    # Ignore resync from trunk, with commit message having be done with debcommit (see rev 2892.5.19 in unity)
    # as it's listing every bugs already fixed.
    resync_trunk_commit = False
    for line in content.splitlines():
        logging.debug(line)
        matches = bug_regexp.findall(line)
        for match in matches:
            bug_numbers.add(match[-1])
            logging.debug("Bug regexp match: {}".format(match[-1]))
        matches = author_regexp.findall(line)
        for match in matches:
            author = match[-1]
        if merge_trunk_commit_regex.search(line):
            resync_trunk_commit = True
            logging.debug("Detected as resync trunk commit, need to ignore all bugs from this set")

        if "---------------------------------" in line:
            if not resync_trunk_commit and author and bug_numbers:
                results.setdefault(author, set())
                for bug in bug_numbers:
                    results[author].add(bug)
                logging.debug("Adding matched bug to global dict for {}".format(author))
            bug_numbers = set()
            author = None
            resync_trunk_commit = False

    # last one (no (-----------------))
    if author and bug_numbers:
        results.setdefault(author, set())
        for bug in bug_numbers:
            results[author].add(bug)
            logging.debug("Adding matched bug to global dict for {}".format(author))

    return results


def commit_release(new_package_version, tip_bzr_rev):
    '''Commit latest release'''
    if subprocess.call(["bzr", "commit", "-m", "Releasing {}, based on r{}".format(new_package_version, tip_bzr_rev)]) != 0:
        raise Exception("The above command returned an error.")


def _get_parent_branch(source_package_name):
    '''Get parent branch from config'''
    config = ConfigParser.RawConfigParser()
    config.read("{}.{}".format(source_package_name, PROJECT_CONFIG_SUFFIX))
    return config.get('Branch', 'branch')


def propose_branch_for_merging(source_package_name, version):
    '''Propose and commit a branch upstream'''

    parent_branch = _get_parent_branch(source_package_name)
    # suppress browser opening
    env = os.environ.copy()
    env["BROWSER"] = "echo"
    env["BZR_EDITOR"] = "echo"

    os.chdir(source_package_name)
    if subprocess.call(["bzr", "push", BRANCH_URL.format(source_package_name), "--overwrite"]) != 0:
        raise Exception("The above command returned an error.")
    mergeinstance = subprocess.Popen(["bzr", "lp-propose-merge", parent_branch, "-m", PACKAGING_MERGE_COMMIT_MESSAGE.format(version), "--approve"], stdin=subprocess.PIPE, env=env)
    mergeinstance.communicate(input="y")
    if mergeinstance.returncode != 0:
        raise Exception("The above command returned an error.")
    os.chdir('..')
