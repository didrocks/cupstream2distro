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
from collections import defaultdict
import logging
import os
import re
import subprocess

from .settings import BRANCH_URL, IGNORECHANGELOG_COMMIT, PACKAGING_MERGE_COMMIT_MESSAGE, PROJECT_CONFIG_SUFFIX


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


def collect_author_commits(content_to_parse, bugs_to_skip):
    '''return a tuple of a dict with authors and commits message from the content to parse

    bugs_to_skip is a set of bugs we need to skip

    Form: ({Author: [commit_message]}, set(bugs))'''

    author_commit = defaultdict(list)
    all_bugs = set()

    current_authors = set()
    current_commit = ""
    current_bugs = set()
    commit_message_stenza = False
    for line in content_to_parse.splitlines():
        # new revision, collect what we have found
        if line.startswith("------------------------------------------------------------"):
            # try to decipher a special case: we have some commits which were already in bugs_to_skip,
            # so we eliminate them.
            # Also ignore when having IGNORECHANGELOG_COMMIT
            if (current_bugs and not (current_bugs - bugs_to_skip)) or IGNORECHANGELOG_COMMIT in current_commit:
                current_authors = set()
                current_commit = ""
                current_bugs = set()
                continue
            current_bugs -= bugs_to_skip
            commit_message = current_commit + _format_bugs(current_bugs)
            for author in current_authors:
                if not author.startswith("Launchpad "):
                    author_commit[author].append(commit_message)
            all_bugs = all_bugs.union(current_bugs)
            current_authors = set()
            current_commit = ""
            current_bugs = set()

        # we ignore this commit if we have a changelog provided as part of the diff
        if line.startswith("=== modified file 'debian/changelog'"):
            current_authors = set()
            current_commit = ""
            current_bugs = set()

        if line.startswith("author: "):
            current_authors = _extract_authors(line[8:])
        # if direct commit to trunk
        elif not current_authors and line.startswith("committer: "):
            current_authors = _extract_authors(line[11:])
        # file the commit message log
        elif commit_message_stenza:
            if line.startswith("diff:"):
                commit_message_stenza = False
                current_commit, current_bugs = _extract_commit_bugs(current_commit)
            else:
                line = line[2:] # Dedent the message provided by bzr
                if line[0:2] in ('* ', '- '): # paragraph line.
                    line = line[2:] # Remove bullet
                    if line[-1] != '.': # Grammar nazi...
                        line += '.' # ... or the lines will be merged.
                line = line + ' ' # Add a space to preserve lines
                current_commit += line
        elif line.startswith("message:"):
            commit_message_stenza = True
        elif line.startswith("fixes bug: "):
            current_bugs = current_bugs.union(_return_bugs(line[11:]))

    return (dict(author_commit), all_bugs)


def _format_bugs(bugs):
    '''Format a list of launchpad bugs.'''
    if bugs:
        msg = ' (LP: {})'.format(', '.join(['#{}'.format(b) for b in bugs]))
    else:
        msg = ''
    return msg


def _extract_commit_bugs(commit_message):
    '''extract relevant commit message part and bugs number from a commit message'''

    current_bugs = _return_bugs(commit_message)
    changelog_content = " ".join(commit_message.rsplit('Fixes: ')[0].rsplit('Approved by ')[0].split())

    return (changelog_content, current_bugs)


def _return_bugs(string):
    '''return a set of bugs from string'''

    # we are trying to match in the commit message:
    # bug #12345, bug#12345, bug12345, bug 12345
    # lp: #12345, lp:#12345, lp:12345, lp: 12345
    # lp #12345, lp#12345, lp12345, lp 12345,
    # Fix #12345, Fix 12345, Fix: 12345, Fix12345, Fix: #12345,
    # Fixes #12345, Fixes 12345, Fixes: 12345, Fixes:12345, Fixes: #12345
    # *launchpad.net/bugs/1234567890 and
    # #12345 (but not 12345 for false positive)
    # Support multiple bugs per commit
    bug_numbers = set()
    bug_regexp = re.compile("((lp|bug|fix(es)?)[: #]*|#|launchpad.net/bugs/)(\d{5,})", re.IGNORECASE)
    for match in bug_regexp.findall(string):
        logging.debug("Bug regexp match: {}".format(match[-1]))
        bug_numbers.add(int(match[-1]))
    return bug_numbers


def _extract_authors(string):
    '''return a authors set from string, ignoring emails'''

    authors = set()
    for author_with_mail in string.split(", "):
        author = author_with_mail.rsplit(' <')[0]
        logging.debug("Found {} as author".format(author))
        authors.add(author)
    return authors


def return_log_diff(starting_rev):
    '''Return the relevant part of the cvs log since starting_rev'''

    instance = subprocess.Popen(["bzr", "log", "-r", "{}..".format(starting_rev), "--show-diff", "--forward"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = instance.communicate()
    if instance.returncode != 0:
        raise Exception(stderr.decode("utf-8").strip())
    return stdout


def commit_release(new_package_version, tip_bzr_rev=None):
    '''Commit latest release'''
    if tip_bzr_rev:
        message = "Releasing {}".format(new_package_version)
    else:
        message = "Releasing {}, based on r{}".format(new_package_version, tip_bzr_rev)
    if subprocess.call(["bzr", "commit", "-m", message]) != 0:
        raise Exception("The above command returned an error.")


def _get_parent_branch(source_package_name):
    '''Get parent branch from config'''
    config = ConfigParser.RawConfigParser()
    config.read("{}.{}".format(source_package_name, PROJECT_CONFIG_SUFFIX))
    return config.get('Branch', 'branch')


def propose_branch_for_merging(source_package_name, version, tip_rev, branch):
    '''Propose and commit a branch upstream'''

    parent_branch = _get_parent_branch(source_package_name)
    # suppress browser opening
    env = os.environ.copy()
    env["BROWSER"] = "echo"
    env["BZR_EDITOR"] = "echo"

    os.chdir(source_package_name)
    if subprocess.call(["bzr", "push", BRANCH_URL.format(source_package_name, version.replace("~", "").replace(":", "")), "--overwrite"]) != 0:
        raise Exception("The push command returned an error.")
    mergeinstance = subprocess.Popen(["bzr", "lp-propose-merge", parent_branch, "-m", PACKAGING_MERGE_COMMIT_MESSAGE.format(version, tip_rev, branch), "--approve"], stdin=subprocess.PIPE, env=env)
    mergeinstance.communicate(input="y")
    if mergeinstance.returncode != 0:
        raise Exception("The lp-propose command returned an error.")
    os.chdir('..')


def merge_branch_with_parent_into(local_branch_uri, lp_parent_branch, dest_uri, commit_message, revision):
    """Merge local branch into lp_parent_branch at revision"""
    success = False
    cur_dir = os.path.abspath('.')
    subprocess.call(["bzr", "branch", "-r", str(revision), lp_parent_branch, dest_uri])
    os.chdir(dest_uri)
    if subprocess.call(["bzr", "merge", local_branch_uri]) == 0:
        subprocess.call(["bzr", "commit", "-m", commit_message])
        success = True
    os.chdir(cur_dir)
    return success


def reconcile_with_branch(uri_to_merge, lp_parent_branch):
    """Resync with targeted branch if possible"""
    success = False
    cur_dir = os.path.abspath('.')
    os.chdir(uri_to_merge)
    if subprocess.call(["bzr", "merge", lp_parent_branch]) == 0:
        subprocess.call(["bzr", "commit", "-m", "Resync trunk", "--unchanged"])
        success = True
    os.chdir(cur_dir)
    return success

def push_to_branch(source_uri, lp_parent_branch, overwrite=False):
    """Push source to parent branch"""
    success = False
    os.chdir(source_uri)
    lp_parent_branch = lp_parent_branch.replace("https://code.launchpad.net/", "lp:")
    command = ["bzr", "push", lp_parent_branch]
    if overwrite:
        command.append("--overwrite")
    if subprocess.call(command) == 0:
        success = True
    os.chdir("..")
    return success
