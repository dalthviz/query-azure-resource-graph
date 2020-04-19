# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Main.
"""
from system_mapper.visualization.dash.index import main_run
from system_mapper.provider_azure.azure_mapper import run_mapper

if __name__ == '__main__':
    run_mapper()
    main_run()
