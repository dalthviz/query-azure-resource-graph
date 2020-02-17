# Microsoft Azure Resource Graph Query and model mapper
This Python script is used to interact with the [Microsoft Azure Resource Graph](https://docs.microsoft.com/en-us/azure/governance/resource-graph/) service to query [Azure Resource Manager](https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-overview) for information on Azure resources.  It is written using Python 3.6.

It also maps the returned information into a infrastructure graph persisted using Neo4j and Neomodel.

## What problem does this solve?
Retrieving information about Azure resources typically involves creating separate resource queries to each [resource provider](https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-manager-supported-services) such as storage, network, and compute.  By using the Microsoft Azure Resource Graph queries for properties of resources can be performed without having to make them individually to each resource provider.  The service also supports complex queries using the [Resource Graph query language](https://docs.microsoft.com/en-us/azure/governance/resource-graph/concepts/query-language).

## Resouces

* Based on the [query-azure-resource-graph](https://github.com/mattfeltonma/query-azure-resource-graph) script by @mattfeltonma
* Using the azure-cli and resource-graph extension

## Requirements

### Python

* [Python 3.6](https://www.python.org/downloads/release/python-368/)
* [Azure CLI](https://github.com/Azure/azure-cl)
    * [Resource Graph extension for Azure CLI](https://github.com/Azure/azure-cli-extensions/tree/master/src/resource-graph)
* [Pandas](https://pandas.pydata.org/)
* [neomodel](https://github.com/neo4j-contrib/neomodel)

### Environment

* [Neo4j <= 3.3 or supported by neomodel](https://neo4j.com/)
