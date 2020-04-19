# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Main scrip.

Connect with Azure via Resource Graph, query infrastructure and populate model
"""

# Standard library imports
import sys
import json
import logging
from argparse import ArgumentParser

# Third-party imports
import msal
import pandas
import azure.mgmt.resourcegraph
from msrestazure.azure_active_directory import AADTokenCredentials

# Local imports
from .model_mapper import create_infrastructure_model


def create_logger(logfile=None):
    """
    Create a logging mechanism.

    Create a logging handler that will write to stdout and optionally
    to a log file
    """
    stdout_handler = logging.StreamHandler(sys.stdout)
    if logfile is not None:
        file_handler = logging.FileHandler(filename=logfile)
        handlers = [file_handler, stdout_handler]
    else:
        handlers = [stdout_handler]

    # Configure logging mechanism
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def obtain_access_token(tenantname, scope, client_id, client_secret):
    """
    Return an access token.

    Obtain access token using client credentials flow.
    """
    logging.info("Attempting to obtain an access token...")
    result = None
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority='https://login.microsoftonline.com/' + tenantname
    )
    result = app.acquire_token_for_client(scope)

    if "access_token" in result:
        logging.info('Access token successfully obtained')
        return result
    else:
        logging.error('Authentication failure')
        logging.error('Error was: {0}'.format(result['error']))
        logging.error('Error description was: {0}'.format(
            result['error_description']))
        logging.error('Error correlation_id was: {0}'.format(
            result['correlation_id']))
        raise Exception("Unable to obtain access token")


def resource_request(subscription_ids, query, page_token=None):
    """Create Resource Graph request."""
    logging.info("Creating query option and query request...")

    # Configure query options
    queryoption = azure.mgmt.resourcegraph.models.QueryRequestOptions(
        skip_token=page_token
    )

    # Configure query request
    queryrequest = azure.mgmt.resourcegraph.models.QueryRequest(
        subscriptions=subscription_ids,
        query=query,
        options=queryoption
    )
    return queryrequest


def export_data(data):
    """Export data using Pandas."""
    # Create a list of column names
    column_names = []

    for column in data['columns']:
        column_names.append(column['name'])

    # Create a DataFrame using the Pandas module and export it as JSON
    dfobj = pandas.DataFrame(data['rows'], columns=column_names)
    return dfobj


def main():
    """Run main script."""
    try:

        # Process parameters file
        parser = ArgumentParser()
        parser.add_argument(
            '--parameterfile', type=str, help='JSON file with parameters')
        parser.add_argument(
            '--exportfile', type=str, default='azure_resources.json',
            help='Name of export file (default: azure_resources.json')
        parser.add_argument(
            '--logfile', type=str, default=None,
            help='Specify an optional log file')
        args = parser.parse_args()

        with open(args.parameterfile) as json_data:
            config = json.load(json_data)

        # Setup a logger
        if args.logfile is not None:
            create_logger(args.logfile)
        else:
            create_logger()

        # Obtain an access token and convert it to a credential
        token = obtain_access_token(
            tenantname=config['tenantname'],
            scope=config['scope'],
            client_id=config['client_id'],
            client_secret=config['client_secret']
        )
        credential = AADTokenCredentials(token=token, client_id=None)

        # Setup the Resource Graph connection and issue the query
        client = azure.mgmt.resourcegraph.ResourceGraphClient(credential)

        logging.info("Issuing request to resource graph...")
        result = client.resources(
            query=resource_request(subscription_ids=config['subscription_ids'],
                                   query=config['query']),
        )
        df_results = export_data(result.data)

        # Check for paged results
        while result.skip_token is not None:
            logging.info("Retrieving " + str(result.count) + " paged records")
            result = client.resources(
                query=resource_request(
                    subscription_ids=config['subscription_ids'],
                    query=config['query'],
                    page_token=result.skip_token)
            )
            # Append new records to DataFrame
            df_results = df_results.append(export_data(result.data))

        # Export query results to file
        df_results.to_json(path_or_buf=args.exportfile, orient='records')

        # Create model using data from query
        ecore_uri = config['ecore_uri']
        model_filename = config['model_filename']
        create_infrastructure_model(df_results, ecore_uri, model_filename)

    except Exception:
        logging.error("Execution error", exc_info=True)


if __name__ == "__main__":
    main()
