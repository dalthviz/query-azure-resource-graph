# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License

"""
Model mapper.

Use ecore metamodel to create a model with the given info
"""

# Third-party imports
from pyecore.resources import HttpURI, ResourceSet, URI
from pyecore.utils import DynamicEPackage


def get_infrastructure_model_access(ecore_uri='./infrastructure.ecore',
                                    http_uri=False):
    """Return handler to instanciate classes of a metamodel."""
    rset = ResourceSet()
    uri = URI(ecore_uri)
    if http_uri:
        uri = HttpURI(ecore_uri)

    resource = rset.get_resources(uri)
    mm_root = resource.contents[0]  # We get the root (an EPackage here)

    return DynamicEPackage(mm_root)


def save_model(model_root, filename='model.xmi'):
    """Save model to file."""
    rset = ResourceSet()
    resource = rset.create_resource(URI(filename))
    resource.append(model_root)
    resource.save()


def create_infrastructure_model(model_dataframe, ecore_uri, model_filename,
                                http_uri=False, save=True):
    """Instanciate a model using the provided data and save it."""
    # Get access to model classes
    model_access = get_infrastructure_model_access(
        ecore_uri=ecore_uri, http_uri=http_uri)

    # Initialize model
    regions = ["East US"]
    model_root = model_access.Region(name="East US")

    # Save model
    save_model(model_root, filename=model_filename)
