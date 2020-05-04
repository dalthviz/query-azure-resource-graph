# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Deployed application graph visualization dashboard.
"""

# Standard library imports
import os
import json

# Local imports
import system_mapper.visualization.dash.reusable_components as drc
from system_mapper.config import CONFIG

# Third-party imports
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
import dash_treeview_antd

# Neomodel database URL
from neomodel import config, db
from neobolt.exceptions import CypherError
config.DATABASE_URL = CONFIG['neo4j_database_url']


ELEMENT_TYPES = [
    'ResourceGroup', 'VirtualMachine', 'Database', 'Disk', 'NetworkInterface',
    'Subnet', 'VirtualNetwork', 'NetworkSecurityGroup', 'LoadBalancer',
    'PublicIp', 'PrivateIp', 'Property', 'Tag', 'DeployedApplication',
    'Service', 'Storage', 'Custom']


RULES = CONFIG['rules']


RULES_MAPPING = CONFIG['rules_mapping']


RULE = CONFIG['initial_rule']


RULE_QUERY = RULES_MAPPING[RULE]


ALL_QUERY = """
CALL apoc.export.json.all("{save_path}",{{useTypes:true}})
YIELD data
RETURN data
"""


ELEMENT_QUERY = """
CALL apoc.export.json.query(
"MATCH (nod:{element_type}) RETURN nod",
"{save_path}", null)
"""

CUSTOM_QUERY = """CALL apoc.export.json.query(
"{custom_query}",
"{save_path}", null)"""


DEFAULT_STYLESHEET = [
    {
        "selector": '.warning',
        'style': {
            'z-index': 9999,
            'content': 'data(label)',
            'color': '#ff9966',
            'line-color': '#ff9966',
            "border-width": 3,
            'background-color': '#ff9966',
            "border-color": "#ff9966",
        }
    },
    {
        "selector": 'node',
        'style': {
            "opacity": 0.65,
            'z-index': 9999,
            'content': 'data(label)'
        }
    },
    {
        "selector": 'edge',
        'style': {
            "curve-style": "unbundled-bezier",
            "opacity": 0.45,
            'z-index': 5000,
            'content': 'data(label)'
        }
    },
    {
        "selector": '.OBJ_PROPERTY',
        'style': {
            "curve-style": "unbundled-bezier",
            "line-style": "dashed",
            "opacity": 0.45,
            'z-index': 5000,
            'content': 'data(label)'
        }
    },
    {
        "selector": '.OBJ_TAG',
        'style': {
            "curve-style": "unbundled-bezier",
            "line-style": "dashed",
            "opacity": 0.45,
            'z-index': 5000,
            'content': 'data(label)'
        }
    },
    {
        "selector": '.ELEMENT_RESOURCE_GROUP',
        'style': {
            "curve-style": "unbundled-bezier",
            "line-style": "dashed",
            "opacity": 0.45,
            'z-index': 5000,
            'content': 'data(label)'
        }
    },
    {
        'selector': '.ResourceGroup',
        'style': {
            'height': 100,
            'width': 100,
            'background-fit': 'cover',
            'background-color': 'grey',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/azure-resource-group-blue.svg'
        }
    },
    {
        'selector': '.Property',
        'style': {
            'height': 50,
            'width': 50,
            'background-fit': 'cover',
            'background-color': 'grey'
        }
    },
    {
        'selector': '.Tag',
        'style': {
            'height': 50,
            'width': 50,
            'background-fit': 'cover',
            'background-color': 'blue',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/price-tag.svg'
        }
    },
    {
        'selector': '.VirtualMachine',
        'style': {
            'height': 80,
            'width': 80,
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/prebuilt-machine.svg',
            'background-color': '#0074D9',
        }
    },
    {
        'selector': '.VirtualMachine.Database',
        'style': {
            'height': 80,
            'width': 80,
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/database01.svg',
            'background-color': '#77a8d4',
        }
    },
    {
        'selector': '.Disk',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'yellow',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/disks.svg'
        }
    },
    {
        'selector': '.VirtualNetwork',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'green',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/connect.svg'
        }
    },
    {
        'selector': '.NetworkSecurityGroup',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'black',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/security-alt.svg'
        }
    },
    {
        'selector': '.Subnet',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'red',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/networking.svg'
        }
    },
    {
        'selector': '.NetworkInterface',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'black',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/connect.svg'
        }
    },
    {
        'selector': '.DeployedApplication',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'gray',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/devops-deploy-cloud.svg'
        }
    },
    {
        'selector': '.LoadBalancer',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'gray',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/app-service-logic.svg'
        }
    },
    {
        'selector': '.PublicIp',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'gray',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/advanced-functionality.svg'
        }
    },
    {
        'selector': '.Service',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'gray',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/cloud-services-blue.svg'
        }
    },
    {
        'selector': '.Service.AppService',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'gray',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/app-service-web.svg'
        }
    },
    {
        'selector': '.Storage',
        'style': {
            'height': 80,
            'width': 80,
            'background-color': 'gray',
            'background-fit': 'cover',
            'background-image': 'https://code.benco.io/icon-collection/'
            'azure-patterns/storage-files.svg'
        }
    },
    {
        'selector': '.followerEdge',
        "style": {
            "mid-target-arrow-color": "blue",
            "mid-target-arrow-shape": "vee",
            "line-color": "#0074D9"
        }
    },
    {
        'selector': '.followingNode',
        'style': {
            'background-color': '#FF4136'
        }
    },
    {
        'selector': '.followingEdge',
        "style": {
            "mid-target-arrow-color": "red",
            "mid-target-arrow-shape": "vee",
            "line-color": "#FF4136",
        }
    },
    {
        "selector": '.genesis',
        "style": {
            'background-color': '#B10DC9',
            "border-width": 2,
            "border-color": "purple",
            "border-opacity": 1,
            "opacity": 1,

            "label": "data(label)",
            "color": "#B10DC9",
            "text-opacity": 1,
            "font-size": 12,
            'z-index': 9999
        }
    },
    {
        'selector': ':selected',
        "style": {
            "border-width": 2,
            "border-color": "black",
            "border-opacity": 1,
            "opacity": 1,
            "label": "data(label)",
            "color": "black",
            "font-size": 12,
            'z-index': 9999
        }
    }
]

STYLES = {
    'json-output': {
        'overflowY': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {'height': 'calc(98vh - 80px)'},
    'inputs': {'display': 'none'},
    'text-inputs': {'width': '100%'},
    'search': {'width': '100%'},
    'reset': {'width': '100%'}
}

# Load extra layouts
cyto.load_extra_layouts()

asset_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'assets'
)

APP = dash.Dash(__name__, assets_folder=asset_path)
APP.config.suppress_callback_exceptions = True


class GraphVisualization():
    """Create graph plot."""

    TEMPLATE_PATH = 'file:///{file_path}/{filename}'

    def __init__(
            self, initial_query, name,
            initial_filename='data.json',
            initial_element_type=None, initial_variables=[],
            expand_enable=True, rules_enable=False,
            initial_custom_query=False,
            expand_properties=False,
            element_types=ELEMENT_TYPES):
        self.app = APP
        self.name = name
        self.nodes = []
        self.relations = []
        self.data = []
        self.filename = name + initial_filename
        self.expand_enable = expand_enable
        self.rules_enable = rules_enable
        self.initial_rules_enable = rules_enable
        self.expand_properties = expand_properties
        self.initial_expand_properties = expand_properties
        self.element_types = element_types
        self.selected_rule = None
        self.n_clicks = 0
        self.n_clicks_reset = 0
        self.element_data = None

        self.initial_query = initial_query
        self.initial_element_type = initial_element_type
        self.initial_variables = initial_variables
        self.initial_custom_query = initial_custom_query
        self.query_data(
            self.initial_query,
            filename=self.filename,
            element_type=self.initial_element_type,
            variables=self.initial_variables,
            custom=self.initial_custom_query)
        self.setup_default_graph()
        self.setup_callbacks()

    def _treeify(self, data, key=None):
        """
        Format JSON follwoing {title:str, children:[{}, ..]} tree spec.

        Spec used by: https://ant.design/components/tree/

        { title: Element data,
          children: [
              {
                  title: children1,
                  children: [{ title: value1}]
              },
              {
                  title: childrenlist2,
                  children: [
                      {
                          title: children21
                          children: [{ title: valuechildre21 }]
                      },
                      {
                          title: children22
                          children: [{ title: valuechildre22 }]
                      }]
             }]
          }
        """
        if isinstance(data, dict) and not key:
            return {
                   'title': 'Element data',
                   'children': [
                       self._treeify(children, key=key)
                       for key, children in data.items()]
                   }
        elif isinstance(data, dict) and key:
            return {
                   'title': key,
                   'children': [
                       self._treeify(children, key=key)
                       for key, children in data.items()]
                   }
        elif isinstance(data, list):
            return {
               'title': key,
               'children': [
                   self._treeify(children)
                   for idx, children in enumerate(data, start=1)]
               }
        elif key:
            return {'title': key, 'children': [self._treeify(data)]}
        else:  # leave node, no recursion
            return {'title': data}

    def _reset_data(self):
        """Reset data re-doing initial query."""
        self.query_data(
            self.initial_query,
            filename=self.filename,
            element_type=self.initial_element_type,
            variables=self.initial_variables,
            custom=self.initial_custom_query)
        self.expand_properties = self.initial_expand_properties

    def setup_callbacks(self):
        """Set-up Dash app callbacks."""
        app = self.app

        @app.callback(
            Output('hover-element-json-output' + self.name, 'data'),
            [Input('cytoscape' + self.name, 'mouseoverNodeData'),
             Input('cytoscape' + self.name, 'mouseoverEdgeData')])
        def display_hover_element(node_data, edge_data):
            data = self.element_data
            if node_data and node_data != self.element_data:
                data = node_data
            elif edge_data and edge_data != self.element_data:
                data = edge_data
            self.element_data = data
            parse_data = 'Hover a node or edge to see its properties here'
            if data:
                parse_data = self._treeify(data)
            return parse_data

        @app.callback(Output('cytoscape' + self.name, 'layout'),
                      [Input('dropdown-layout' + self.name, 'value')])
        def update_cytoscape_layout(layout):
            return {'name': layout}

        @app.callback(Output('custom' + self.name, 'style'),
                      [Input('dropdown-expand' + self.name, 'value')])
        def display_custom_expansion(expansion_mode):
            if expansion_mode == 'Custom':
                return {'display': 'block'}
            else:
                return {'display': 'none'}

        @app.callback(Output('search' + self.name, 'value'),
                      [Input('dropdown-expand' + self.name, 'value'),
                       Input('cytoscape' + self.name, 'tapNodeData')])
        def clear_search(value, nodeData):
            """Clear input search."""
            return ''

        def _generate_elements(
                nodeData=None, n_clicks=None, n_click_reset=None, search=None,
                rule=None, expansion_mode=None, custom_query=None,
                custom_query_var=None):
            """Update items displayed in graph following an expansion type."""
            elements = self.data

            if n_click_reset > self.n_clicks_reset:
                elements = self.data = []
                self.n_clicks_reset += 1
                self._reset_data()

            if n_clicks > self.n_clicks and search:
                elements = self.data = []
                self.n_clicks += 1
                variables = search.split('RETURN')[-1].strip()
                variables = [var.strip() for var in variables.split(',')]
                self.query_data(
                        search,
                        filename=self.filename,
                        custom=True,
                        variables=variables)

            if rule and self.selected_rule != rule:
                elements = self.data = []
                self.selected_rule = rule
                self.query_data(
                        RULES_MAPPING[rule][0],
                        filename=self.filename,
                        custom=True,
                        variables=RULES_MAPPING[rule][1].split(','))
                return elements

            if not nodeData:
                return elements

            if self.expand_enable:
                # TODO: If the node has already been expanded, we don't expand
                # it again
                # if nodeData.get('expanded'):
                #     return elements

                # This retrieves the currently selected element,
                # and tag it as expanded
                for element in elements:
                    if nodeData['id'] == element.get('data').get('id'):
                        element['data']['expanded'] = True
                        break

                if (expansion_mode in ELEMENT_TYPES and
                        expansion_mode != 'Custom'):
                    query = (
                        "MATCH (nod)-[rels]-(nods:{element_type}) "
                        "WHERE ID(nod) = {id} return nod, rels, nods").format(
                                 element_type=expansion_mode,
                                 id=nodeData['id'])
                    self.query_data(
                        query,
                        filename=self.filename,
                        custom=True,
                        variables=['rels', 'nods'])
                elif expansion_mode == 'Custom':
                    # NEED PARSER TO CHECK CUSTOM QUERY BY USER
                    query = custom_query.format(id=nodeData['id'])
                    self.query_data(
                        query,
                        filename=self.filename,
                        custom=True,
                        variables=[var.strip()
                                   for var in custom_query_var.split(',')])

            return elements

        if self.rules_enable:
            @app.callback(
                Output('cytoscape' + self.name, 'elements'),
                [Input('cytoscape' + self.name, 'tapNodeData'),
                 Input('search-submit' + self.name, 'n_clicks'),
                 Input('reset-submit' + self.name, 'n_clicks'),
                 Input('dropdown-rules' + self.name, 'value')],
                [State('search' + self.name, 'value'),
                 State('dropdown-expand' + self.name, 'value'),
                 State('custom-query' + self.name, 'value'),
                 State('custom-query-variables' + self.name, 'value')])
            def generate_elements_with_rules(
                    nodeData=None, n_clicks=None, n_click_reset=None,
                    rule=None, search=None, expansion_mode=None,
                    custom_query=None, custom_query_var=None):
                return _generate_elements(
                    nodeData=nodeData, n_clicks=n_clicks,
                    n_click_reset=n_click_reset, search=search, rule=rule,
                    expansion_mode=expansion_mode, custom_query=custom_query,
                    custom_query_var=custom_query_var)
        else:
            @app.callback(
                Output('cytoscape' + self.name, 'elements'),
                [Input('cytoscape' + self.name, 'tapNodeData'),
                 Input('search-submit' + self.name, 'n_clicks'),
                 Input('reset-submit' + self.name, 'n_clicks')],
                [State('search' + self.name, 'value'),
                 State('dropdown-expand' + self.name, 'value'),
                 State('custom-query' + self.name, 'value'),
                 State('custom-query-variables' + self.name, 'value')])
            def generate_elements(
                    nodeData=None, n_clicks=None, n_click_reset=None,
                    search=None, expansion_mode=None, custom_query=None,
                    custom_query_var=None):
                return _generate_elements(
                    nodeData=nodeData, n_clicks=n_clicks,
                    n_click_reset=n_click_reset,
                    rule=None, search=search, expansion_mode=expansion_mode,
                    custom_query=custom_query,
                    custom_query_var=custom_query_var)

    def query_data(
            self, query, filename='data.json', element_type=None,
            custom=False, variables=None):
        """Query data and store it in a file."""
        file_path = os.path.dirname(__file__)
        template_path = self.TEMPLATE_PATH
        full_path = template_path.format(
            file_path=file_path, filename=filename)
        if os.name == 'nt':
            full_path = full_path.replace('\\', '/')
        if element_type is not None:
            query = query.format(
                save_path=full_path,
                element_type=element_type)
        elif custom:
            query = CUSTOM_QUERY.format(
                custom_query=query, save_path=full_path)
        else:
            query = query.format(save_path=full_path)
        print(query)
        try:
            db.cypher_query(query)
            self.format_data(filename, variables)
        except CypherError:
            pass

    def _format_data(self, line_data, warning_style=False):
        """Format data and add it."""
        if ('properties' in line_data and
                'properties' in line_data['properties']):
            line_data['properties']['properties'] = json.loads(
                line_data['properties']['properties'])

        if line_data['type'] == 'node':
            line_data = {'data': line_data}
            line_data['classes'] = ' '.join(
                line_data['data']['labels'])
            if ('Property' in line_data['data']['labels']
                    and not self.expand_properties):
                return
            if warning_style:
                line_data['classes'] += ' warning'
            if ('Property' in line_data['data']['labels']):
                line_data['data']['label'] = (
                    line_data['data']['properties']['key'])
            if 'name' in line_data['data']['properties']:
                line_data['data']['label'] = (
                    line_data['data']['properties']['name'])
            if line_data not in self.nodes:
                self.nodes.append(line_data)
        else:
            if (('OBJ_PROPERTY' in line_data['label']
                    or 'OBJ_TAG' in line_data['label'])
                    and not self.expand_properties):
                return
            if 'start' in line_data:
                line_data['source'] = line_data['start']['id']
                del line_data['id']
            if 'end' in line_data:
                line_data['target'] = line_data['end']['id']
            line_data = {'data': line_data}
            line_data['classes'] = ' ' + line_data['data']['label']
            if warning_style:
                line_data['classes'] += ' warning'
            if line_data not in self.relations:
                self.relations.append(line_data)
        self.data.append(line_data)

    def format_data(self, neo4j_data_path, variables=[]):
        """
        Format data from neo4j result to cytoscape.

        Conversion to the form:
            [
            {'data': {'id': 'one', 'label': 'Node 3'},
             'position': {'x': 50, 'y': 50},
             'classes': 'css_class'},
            {'data': {'id': 'two', 'label': 'Node 2'},
             'position': {'x': 200, 'y': 200}},
            {'data': {'source': 'one', 'target': 'two',
                      'label': 'Node 1 to 2'}}
            ]
        """
        # import time
        # TODO: Fix use of relative paths
        neo4j_data_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), neo4j_data_path)

        warning_style = (
            self.rules_enable and self.initial_rules_enable
            and len(self.data) == 0)

        with open(neo4j_data_path, 'r') as data:
            for line in data:
                line_data = json.loads(line)
                if variables:
                    original = json.loads(line)
                    for var in variables:
                        line_data = original[var]
                        self._format_data(
                            line_data, warning_style=warning_style)
                else:
                    self._format_data(line_data)
        self.expand_properties = True

    def setup_default_graph(self):
        """General graph with all the nodes available."""
        # Set layout
        layout = html.Div([
            html.Div(className='eight columns', children=[
                dcc.Loading(
                    id='loading-1',
                    type='default',
                    children=cyto.Cytoscape(
                        id='cytoscape' + self.name,
                        elements=self.data,
                        stylesheet=DEFAULT_STYLESHEET,
                        style={
                            'height': '100vh',
                            'width': '100%'
                        })
                )
            ]),
            html.Div(className='four columns', children=[
                html.Div(
                        className='center',
                        children=[
                            html.Img(
                                src='../assets/images/convention.png'
                                )]),
                dcc.Tabs(id='tabs' + self.name, children=[
                    dcc.Tab(label='Control Panel', children=[
                        html.Div(
                            id='search-box' + self.name,
                            children=[
                                dcc.Input(
                                    style=STYLES['text-inputs'],
                                    id='search' + self.name,
                                    type='text', value='',
                                    placeholder='Search query'),
                                html.Button(
                                    children='Search',
                                    id='search-submit' + self.name,
                                    type='submit',
                                    n_clicks=0),
                                ],
                            style=STYLES['search'],
                            ),
                        html.Div(
                            id='rules-box' + self.name,
                            children=[
                                drc.NamedDropdown(
                                    name='Filters',
                                    id='dropdown-rules' + self.name,
                                    options=drc.DropdownOptionsList(
                                        *RULES
                                    ),
                                    value=RULE,
                                    clearable=False
                                )],
                            style=STYLES['search'],
                            ) if self.rules_enable else '',
                        drc.NamedDropdown(
                            name='Layout',
                            id='dropdown-layout' + self.name,
                            options=drc.DropdownOptionsList(
                                'random',
                                'grid',
                                'circle',
                                'concentric',
                                'breadthfirst',
                                'cose',
                                'cose-bilkent',
                                'dagre',
                                'cola',
                                'klay',
                                'spread',
                                'euler'
                            ),
                            value='random',
                            clearable=False
                        ),
                        drc.NamedDropdown(
                            name='Expand by',
                            id='dropdown-expand' + self.name,
                            options=drc.DropdownOptionsList(
                                *self.element_types
                            ),
                            value=self.element_types[0],
                            clearable=False
                        ) if self.expand_enable else '',
                        html.Div(
                            id='custom' + self.name,
                            style=STYLES['inputs'], children=[
                                drc.NamedInput(
                                    style=STYLES['text-inputs'],
                                    name='Custom Query',
                                    id='custom-query' + self.name,
                                    value='',
                                    placeholder=(
                                        'MATCH (n)-[r]-(m) WHERE ID(n) = {id} '
                                        'RETURN n, r, m')),
                                drc.NamedInput(
                                    style=STYLES['text-inputs'],
                                    name='Custom Query Variables',
                                    id='custom-query-variables' + self.name,
                                    value='',
                                    placeholder='n, r, m')]
                            ) if self.expand_enable else '',
                        html.Div(
                            id='search-box' + self.name,
                            children=[
                                html.Button(
                                    children='Reset',
                                    id='reset-submit' + self.name,
                                    type='submit',
                                    n_clicks=0),
                                ],
                            style=STYLES['reset'],
                            ),
                    ]),
                    dcc.Tab(label='Elements Properties', children=[
                        html.Div(
                            children=[
                                html.P('Element Object JSON:'),
                                dash_treeview_antd.TreeView(
                                    id='hover-element-json-output' + self.name,
                                    multiple=False,
                                    checkable=False,
                                    selected=[],
                                    expanded=['root'],
                                    data={})
                                ])
                    ])
                ]),
            ])
        ])

        return layout

    def run(self, debug=False):
        """Launch visualization."""
        if self.app.layout is None:
            self.app.layout = self.setup_default_graph()
        self.app.run_server(debug=debug)


# Initialize base visualizations
FULL_MAP_VISUALIZATION = GraphVisualization(
    ALL_QUERY,
    "FULL",
    element_types=['Property', 'Tag', 'Custom'])
RESOURCE_QUERY_VISUALIZATION = GraphVisualization(
    ELEMENT_QUERY, "RESOURCE_QUERY",
    initial_element_type='ResourceGroup',
    initial_variables=['nod'],
    expand_enable=True,
    expand_properties=True)
VM_QUERY_VISUALIZATION = GraphVisualization(
    ELEMENT_QUERY, "VM_QUERY",
    initial_element_type='VirtualMachine',
    initial_variables=['nod'],
    expand_enable=True,
    expand_properties=True)
RULES_QUERY_VISUALIZATION = GraphVisualization(
    RULE_QUERY[0], "RULE_QUERY",
    initial_variables=RULE_QUERY[1].split(','),
    expand_enable=True,
    rules_enable=True,
    initial_custom_query=True,
    expand_properties=True)

if __name__ == '__main__':
    # Example run of a visualization
    RESOURCE_QUERY_VISUALIZATION.run()
