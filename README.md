# System mapper

An utility to retrieve infrastructure and system information from a cloud provider (Azure for now) and store it in a graph database (Neo4j)

## Requirements

### Python

#### Azure
* [Python 3.6](https://www.python.org/downloads/release/python-368/)
* [Microsoft Azure Python SDK](https://github.com/Azure/azure-sdk-for-python/tree/master/sdk)
* [Microsoft Authentication Library (MSAL)](https://docs.microsoft.com/en-us/azure/active-directory/develop/reference-v2-libraries)
* [Pandas](https://pandas.pydata.org/)
* [PyEcore](https://pyecore.readthedocs.io/en/latest/index.html)
* [neomodel](https://github.com/neo4j-contrib/neomodel)

#### AWS

* Cloudmapper and other tools are available

### Environment (database)

* [Neo4j <= 3.3 or supported by neomodel](https://neo4j.com/)

## Setup

* Clone the repository.
* Install the required modules referenced above (`pip install -r requirements.txt`).
* Run ---