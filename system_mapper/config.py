# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Configuration management module.
"""

# Local imports
import json
import os

# Thrid-party imports
from dotenv import load_dotenv, find_dotenv

# Load dotenvfile by searching a .env file walking up the directory tree
load_dotenv(find_dotenv())


def read_config():
    """Read configuration file."""
    config_file = os.getenv('CONFIG_FILE_PATH')
    if not config_file:
        config_file = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'config.json')
    with open(config_file) as file:
        return json.load(file)


CONFIG = read_config()
