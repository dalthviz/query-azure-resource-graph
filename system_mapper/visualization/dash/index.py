# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Index of graph visualizations.
"""
# Third-party imports
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Local imports
from system_mapper.visualization.dash.visualization import (
    APP, FULL_MAP_VISUALIZATION, SUBSCRIPTION_QUERY_VISUALIZATION,
    RESOURCE_QUERY_VISUALIZATION, VM_QUERY_VISUALIZATION,
    RULES_QUERY_VISUALIZATION)

APP.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

VISUALIZATIONS = [
    FULL_MAP_VISUALIZATION, SUBSCRIPTION_QUERY_VISUALIZATION,
    RESOURCE_QUERY_VISUALIZATION, VM_QUERY_VISUALIZATION,
    RULES_QUERY_VISUALIZATION]

VISUALIZATIONS_MAP = {}

for visual in VISUALIZATIONS:
    VISUALIZATIONS_MAP[visual.name] = visual


@APP.server.route('/download/<path:path>')
def download_csv(path):
    """Download visualization current info as csv."""
    return VISUALIZATIONS_MAP[path].download_csv()


@APP.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    """Route to different visualizations."""
    if pathname == '/':
        return html.Div(
            children=[
                html.Div(
                    className='six columns center',
                    children=[
                        html.Img(
                            src='assets/images/full.PNG',
                            width='50%'),
                        html.Br(),
                        dcc.Link(
                            'Navigate the full mapping',
                            href='/apps/full_map')]),
                html.Div(
                    className='six columns center',
                    children=[
                        html.Img(
                            src='assets/images/subscription.svg',
                            width='50%'),
                        html.Br(),
                        dcc.Link(
                            'Navigate starting in a subscription',
                            href='/apps/owner_query_map'),
                        ]),
                html.Div(
                    className='six columns center',
                    children=[
                        html.Img(
                            src='assets/images/resource_group.svg',
                            width='50%'),
                        html.Br(),
                        dcc.Link(
                            'Navigate starting in a resource group',
                            href='/apps/resource_query_map'),
                        ]),
                html.Div(
                    className='six columns center',
                    children=[
                        html.Img(
                            src='assets/images/vmachine.svg',
                            width='50%'),
                        html.Br(),
                        dcc.Link(
                            'Navigate starting in a Virtual Machine',
                            href='/apps/vm_query_map')
                        ]),
                html.Br(),
                html.Div(
                    className='twelve columns center',
                    children=[
                        html.Img(
                            src='assets/images/filter.PNG',
                            width='50%'),
                        html.Br(),
                        dcc.Link(
                            'Navigate by an initial filter',
                            href='/apps/rules_query_map')
                        ])
                    ])
    if pathname == '/apps/full_map':
        return FULL_MAP_VISUALIZATION.setup_default_graph()
    elif pathname == '/apps/owner_query_map':
        return SUBSCRIPTION_QUERY_VISUALIZATION.setup_default_graph()
    elif pathname == '/apps/resource_query_map':
        return RESOURCE_QUERY_VISUALIZATION.setup_default_graph()
    elif pathname == '/apps/vm_query_map':
        return VM_QUERY_VISUALIZATION.setup_default_graph()
    elif pathname == '/apps/rules_query_map':
        return RULES_QUERY_VISUALIZATION.setup_default_graph()
    else:
        return '404'


def main_run(*args, **kwargs):
    """Run dash index."""
    APP.run_server(*args, **kwargs)
