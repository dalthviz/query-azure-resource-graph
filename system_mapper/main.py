# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Main.
"""
from waitress import serve

from system_mapper.visualization.dash.index import main_run, APP
from system_mapper.provider_azure.azure_mapper import run_mapper
from system_mapper.config import CONFIG

application = APP.server

if __name__ == "__main__":
    if CONFIG['run_mapper']:
        run_mapper()
    if CONFIG['visualization_dev']:
        main_run(debug=False)
    else:
        serve(
            application,
            threads=CONFIG['visualization_n_threads'],
            host=CONFIG['visualization_host'],
            port=CONFIG['visualization_port'])
