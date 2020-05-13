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
    if CONFIG['run_mapper']:
        from system_mapper.provider_azure.azure_mapper import run_mapper
        run_mapper()
    if CONFIG['visualization_dev']:
        from system_mapper.visualization.dash.index import main_run
        main_run(debug=True)
    else:
        from system_mapper.visualization.dash.index import APP
        application = APP.server
        serve(
            application,
            threads=CONFIG['visualization_n_threads'],
            host=CONFIG['visualization_host'],
            port=CONFIG['visualization_port'])
