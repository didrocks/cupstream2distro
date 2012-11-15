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
import os
import re
import subprocess

from . import packagemanager
from .settings import BRANCH_URL, PACKAGING_MERGE_COMMIT_MESSAGE


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


def get_packaging_diff_filename(source_package_name, packaging_version):
    '''Return the packaging diff filename'''

    return "packaging_changes_{}_{}.diff".format(source_package_name, packaging_version)


def _packaging_changes_in_branch(starting_rev):
    '''Return if there has been a packaging change

    We ignore the changelog only changes'''
    bzrinstance = subprocess.Popen(['bzr', 'diff', 'debian/', '-r', str(starting_rev)], stdout=subprocess.PIPE)
    (change_in_debian, err) = subprocess.Popen(['filterdiff', '--clean', '-x', '*changelog'], stdin=bzrinstance.stdout, stdout=subprocess.PIPE).communicate()
    return(change_in_debian != "")


def generate_diff_in_branch(starting_rev, source_package_name, packaging_version):
    '''Generate a diff file in the parent directory if the branch has packaging branch

    The diff contains autotools files and cmakeries'''
    if _packaging_changes_in_branch(starting_rev):
        with open("../{}".format(get_packaging_diff_filename(source_package_name, packaging_version)), "w") as f:
            bzrinstance = subprocess.Popen(['bzr', 'diff', '-r', str(starting_rev)], stdout=subprocess.PIPE)
            (changes_to_publish, err) = subprocess.Popen(['filterdiff', '--clean', '-x', '*changelog',
                                        '-i', '*Makefile.am', '-i', 'configure.*', '-i', 'debian/*',
                                        '-i', '*CMakeLists.txt'], stdin=bzrinstance.stdout, stdout=f).communicate()


def collect_author_bugs(starting_rev, source_package_name):
    '''Collect a dict with authors fixing bugs since last release

    Form: {Author: set(bug_number, )}'''
    author_bugs = _get_all_bugs_in_branch(starting_rev)
    with open("debian/changelog") as f:
        alreadyfixed_bugs = packagemanager.collect_bugs_until_latest_bzr_rev(f, source_package_name)

    # Remove bugs already fixed, discaring author if needed
    authors_to_remove = set()
    for author in author_bugs:
        author_bugs[author] = author_bugs[author] - alreadyfixed_bugs
        if not author_bugs[author]:
            authors_to_remove.add(author)
    for author in authors_to_remove:
        author_bugs.pop(author)
    return author_bugs


def _get_all_bugs_in_branch(starting_rev):
    '''Collect all bugs from the branchs since starting_rev into a dict

    Form: {Author: set(bug_number)}'''
    instance = subprocess.Popen(["bzr", "log", "-r", "{}..".format(starting_rev), "--include-merged", "--forward"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())

    results = {}
    bug_numbers = set()
    author = None

    # we are trying to match in the commit message:
    # bug #12345, bug#12345, bug12345, bug 12345
    # lp: #12345, lp:#12345, lp:12345, lp: 12345
    # lp #12345, lp#12345, lp12345, lp 12345,
    # https://launchpad.net/bugs/1234567890 and
    # #12345 (but not 12345 for false positive)
    # Support multiple bugs per commit
    bug_regexp = re.compile("((lp:?|bug)[ #]*|#|https://launchpad.net/bugs/)(\d{5,})", re.IGNORECASE)
    author_regexp = re.compile("committer: (.*) <.*>")
    for line in stdout.splitlines():
        matches = bug_regexp.findall(line)
        for match in matches:
            bug_numbers.add(match[-1])
        matches = author_regexp.findall(line)
        for match in matches:
            author = match

        if "---------------------------------" in line:
            if author and bug_numbers:
                results.setdefault(author, set())
                for bug in bug_numbers:
                    results[author].add(bug)
            bug_numbers = set()
            author = None

    # last one
    if author and bug_numbers:
        results.setdefault(author, set())
        for bug in bug_numbers:
            results[author].add(bug)

    return results


def commit_release(new_package_version, tip_bzr_rev):
    '''Commit latest release'''
    subprocess.call(["bzr", "commit", "-m", "Releasing {}, based on r{}".format(new_package_version, tip_bzr_rev)])


def save_branch_config(source_package_name, branch):
    '''Save branch configuration'''
    config = ConfigParser.RawConfigParser()
    config.add_section('Branch')
    config.set('Branch', 'branch', branch)
    with open("{}.config".format(source_package_name), 'wb') as configfile:
        config.write(configfile)


def _get_parent_branch(source_package_name):
    '''Get parent branch from config'''
    config = ConfigParser.RawConfigParser()
    config.read("{}.config".format(source_package_name))
    return config.get('Branch', 'branch')


def propose_branch_for_merging(source_package_name, version):
    '''Propose and commit a branch upstream'''

    parent_branch = _get_parent_branch(source_package_name)
    # suppress browser opening
    env = os.environ.copy()
    env["BROWSER"] = "echo"
    env["BZR_EDITOR"] = "echo"

    os.chdir(source_package_name)
    subprocess.call(["bzr", "push", BRANCH_URL.format(source_package_name), "--overwrite"])
    mergeinstance = subprocess.Popen(["bzr", "lp-propose-merge", parent_branch, "-m", PACKAGING_MERGE_COMMIT_MESSAGE.format(version), "--approve"], stdin=subprocess.PIPE, env=env)
    mergeinstance.communicate(input="y")
    os.chdir('..')