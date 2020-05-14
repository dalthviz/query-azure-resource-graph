# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Main.
"""
# Third-party dependencies
from waitress import serve

# Local dependencies
from system_mapper.config import CONFIG


if __name__ == "__main__":
    if 'run_mapper' in CONFIG:
        run_mapper_config = CONFIG['run_mapper']
        if run_mapper_config['run']:
            from system_mapper.provider_azure.azure_mapper import run_mapper
            run_mapper(
                reset=run_mapper_config['reset'],
                export_path=run_mapper_config['export_path'])

    if 'visualization' in CONFIG:
        visualization = CONFIG['visualization']
        if visualization['dev']:
            from system_mapper.visualization.dash.index import main_run
            main_run(debug=visualization['dev_debug'])
        else:
            from system_mapper.visualization.dash.index import APP
            application = APP.server
            serve(
                application,
                threads=visualization['n_threads'],
                host=visualization['host'],
                port=visualization['port'])
