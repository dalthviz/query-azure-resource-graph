# -*- coding: utf-8 -*-
"""Helper to use azure CLI programatically."""

# Standard library imports
from datetime import date, datetime
import json
import logging

# Third-party imports
from azure.cli.core import get_default_cli
import tempfile

# Logging config
logging.basicConfig(level=logging.INFO)


SUCCESS_CODE = 0


def az_cli(args):
    """
    Call azure CLI using the given arguments.

    For example "vm list". When having extension installed they are
    also callable, for example "query -q 'Resources'"
    """
    temp = tempfile.TemporaryFile(mode="r+")
    code = get_default_cli().invoke(args, out_file=temp)
    temp.seek(0)
    data = temp.read().strip()
    temp.close()

    return code, json.loads(data.replace('null', '""'))


def az_status():
    """Return if the token credentials are usable."""
    code, expiration_date = az_cli(
        ['account', 'get-access-token', '--query', 'expiresOn'])
    if code == SUCCESS_CODE:
        expiration_date = datetime.strptime(
            expiration_date, '%Y-%m-%d %H:%M:%S.%f')
        today_date = datetime.combine(date.today(), datetime.min.time())
        return expiration_date > today_date
    return False


def az_login():
    """Authenticate with azure CLI."""
    if not az_status():
        return az_cli(['login'])
    else:
        return az_cli(['account', 'list'])


def az_resource_graph(query):
    """Use resource graph to query available resources."""
    command = ['graph', 'query', '-q', query, '--debug']
    command_str = ' '.join(command)
    logging.info('Running command: az {command}'.format(command=command_str))
    return az_cli(command)


if __name__ == "__main__":
    """Test CLI programatically execution."""
    login = az_login()
    vm_list = az_cli(['vm', 'list'])
    rg_query = az_resource_graph(
        query="Resources | project name, type | order by name asc | limit 5")
