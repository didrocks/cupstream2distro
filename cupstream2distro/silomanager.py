# -*- coding: utf-8 -*-
# Copyright (C) 2014 Canonical
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

import json
import logging
import os

from cupstream2distro.settings import SILO_CONFIG_FILENAME, SILO_NAME_LIST
from cupstream2distro.utils import ignored


def save_config(config, uri):
    """Save config in uri"""
    silo_config_path = os.path.join(uri, SILO_CONFIG_FILENAME)
    with ignored(OSError):
        os.makedirs(uri)
    try:
        json.dump(config, open(silo_config_path, 'w'))
    except TypeError as e:
        logging.error("Can't save configuration: " + e.message)
        os.remove(silo_config_path)
        return False
    return True

def load_config(uri=None):
    """return a loaded config

    If no uri, load in the current directory"""
    if not uri:
        uri = os.path.abspath('.')
    logging.debug("Reading configuration in {}".format(uri))
    try:
        return json.load(open(os.path.join(uri, SILO_CONFIG_FILENAME)))
    # if silo isn't configured
    except IOError:
        pass
    except ValueError as e:
        logging.warning("Can't load configuration: " + e.message)
    return None


def is_project_not_in_any_configs(project_name, series, dest, base_silo_uri):
    """Return true if the project for that serie in that dest is not in any configuration"""
    logging.info("Checking if {} is already configured for {} ({}) in another silo".format(project_name, dest.name, series.name))
    for silo_name in SILO_NAME_LIST:
        config = load_config(os.path.join(base_silo_uri, silo_name))
        if config:
            if (config["global"]["dest"] == dest.self_link and config["global"]["series"] == series.self_link and
                (project_name in config["mps"] or project_name in config["sources"])):
                logging.error("{} is already prepared for the same serie and destination in {}".format(project_name, silo_name))
                return False
    return True


def return_first_available_silo(base_silo_uri):
    """Check which silos are free and return the first one"""
    for silo_name in SILO_NAME_LIST:
        if not os.path.isfile(os.path.join(base_silo_uri, silo_name, SILO_CONFIG_FILENAME)):
            return silo_name
    return None
