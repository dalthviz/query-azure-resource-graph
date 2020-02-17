# System mapper

An utility to retrieve infrastructure and system information from a cloud provider (Azure for now) and store it in a graph database (Neo4j)

## Requirements

### Python

#### Azure
* [Python 3.6](https://www.python.org/downloads/release/python-368/)
* [Microsoft Azure Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/master/sdk)
* [Microsoft Authentication Library (MSAL)](https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-v2-libraries)
* [Pandas](https://pandas.pydata.org/)
* [neomodel](https://github.com/neo4j-contrib/neomodel)

#### AWS

* [Tools like Cloudmapper are available (at least for infrastructure mapping)](https://github.com/duo-labs/cloudmapper)

### Environment (database)

* [Neo4j <= 3.3 or supported by neomodel](https://neo4j.com/)

## Setup

* Clone the repository.
* Install the required modules referenced above (`pip install -r requirements.txt`).
* Check that a Neo4j instance is running in the default port and has as user `neo4j` and password `ne@4j`
