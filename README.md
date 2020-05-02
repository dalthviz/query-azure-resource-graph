# System mapper

An utility to retrieve infrastructure and system information from a cloud provider (Azure for now) and store it in a graph database (Neo4j)

## Requirements

### Python

#### Requirements
* [Python 3.6](https://www.python.org/downloads/release/python-368/)
* [Microsoft Azure Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/master/sdk)
* [Microsoft Authentication Library (MSAL)](https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-v2-libraries)
* [Pandas](https://pandas.pydata.org/)
* [neomodel](https://github.com/neo4j-contrib/neomodel)


### Environment (database and IIS Administration API)

* [Neo4j >= 3.4 and supported by neomodel](https://neo4j.com/) (tested using kernel version `3.4.0`):
    * The compatible [APOC plugin](https://github.com/neo4j-contrib/neo4j-apoc-procedures) needs to be installed too (tested using `3.4.0.8`). Note: Some neo4j config is needed to run some queries using APOC. Please add at the end of your `neo4j.conf` file the following lines:
    ```ini
    #***********************************************************
    # APOC
    #***********************************************************
    dbms.security.procedures.unrestricted=apoc.*
    apoc.export.file.enabled=true
    apoc.import.file.use_neo4j_config=false
    ```
* Install, in the accesible VMs, [IIS Administration API](https://github.com/microsoft/iis.administration). More info about the [IIS API](https://docs.microsoft.com/en-us/IIS-Administration/). You should grant read access to the API to a user. [For that, the `appsettings.json` of the IIS Administration API needs to be change](https://docs.microsoft.com/en-us/IIS-Administration/configuration/appsettings.json) like (cors settings, files access settings and security settings)

## Setup

* Clone the repository.
* Install the required modules referenced above (`pip install -r requirements.txt`).
* Check that a Neo4j instance is running in the default port and has as user `neo4j` and password `ne@4j` and properly configured as stated above.
* Config the relavant options in the `config.json` file. For example a config that uses Azure and IIS Administration API to get the systems information:

```json

{
    "initial_rule": "RULE_0_MULTIPLE_RESOURCE_GROUPS",
    "rules": [
        "RULE_0_MULTIPLE_RESOURCE_GROUPS",
        "RULE_1_MULTIPLE_SUSCRIPTIONS",
        "RULE_2_ORPHAN_NODES",
        "RULE_3_MAX_DEPENDENCIES"],
    "rules_mapping": {
        "RULE_0_MULTIPLE_RESOURCE_GROUPS": [
            "MATCH (n)-[r]-(m) MATCH (n)-[rg1:ELEMENT_RESOURCE_GROUP]-(nrg1) MATCH (m)-[rg2:ELEMENT_RESOURCE_GROUP]-(nrg2) WHERE NOT nrg1 = nrg2 RETURN n, r, m ",
            "n,r,m"
            ],
        "RULE_1_MULTIPLE_SUSCRIPTIONS": [
            "MATCH (n)-[r]-(m) MATCH (n)-[]-(np:Property {key: 'subscriptionId'}) MATCH (m)-[]-(mp:Property {key: 'subscriptionId'}) WHERE NOT np.value = mp.value RETURN n, r, m, np, mp ",
            "n,r,m,np,mp"
            ],
        "RULE_2_ORPHAN_NODES": [
            "MATCH (n) WHERE NOT (n)-[]-() RETURN n",
            "n"
            ],
        "RULE_3_MAX_DEPENDENCIES": [
            "MATCH (n)-[]-(m) RETURN n, COLLECT(m) as others ORDER BY SIZE(others) DESC LIMIT 1",
            "n"
            ]
        },
    "neo4j_database_url": "bolt://neo4j:ne@4j@localhost:7687",
    "database_strings": ["database", "base de datos", "MicrosoftSQLServer"],
    "port": 55539,
    "app_container_url": "/api/webserver/websites/",
    "app_container_token": "some token to access the ISS API. More info: https://docs.microsoft.com/en-us/IIS-Administration/management-portal/connecting",
    "app_container_user": "<windows username>",
    "app_container_password": "<windows user password>",
    "visualization_port": "80",
    "visualization_n_threads": "100",
    "visualization_dev": false,
    "visualization_host": "0.0.0.0"
}
```
Some notes regarding the config file:

* `initial_rule` is the name of the initial rule to apply when checking the rule visualization.

* `rules` are the list of available rules (which need to match the `rules_mapping` dict)

* `rules_mapping` are custom cypher queries. Each entry has (1) the query, (2) the variables returned by the query

* The other values are related with:
    * `neo4j_database_url`: Connection string to connect to the Neo4j database
    * `database_strings`: Strings to find in the VM information to classify a Virtual Machine as a Database node
    * IIS related config:
        * `port`: Connection port for the IIS management API (the API needs to be enabled in the Virtual Machines)
        * `app_container_url`: relative url to use to start to get the INFO. For now THE ONLY SUPPORTED ONE.
        * `app_container_token`: token to use to authenticate the request made to the IIS Administration API.
        * `app_container_user`: windows user to use to authenticate via NTLM
        * `app_container_password`: windows user password to authenticate via NTLM
    * Visualization dashboard related config:
        * `visualization_port`: Port for the server to launch the dash app.
        * `visualization_n_threads`: Number of threads the server in prod mode will use.
        * `visualization_dev`: If the launched dash app is dev mode (run from Dash) or prod mode (waitress).
        * `visualization_host`: Host for the server.

# Run

From the root directory run:

```python
python -m system_mapper.main
```

