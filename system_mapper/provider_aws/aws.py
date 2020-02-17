# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
AWS infrastructure domain mapping.
"""

# Local imports
import system_mapper.graph as graph


class AWSGraphMapper(graph.BaseGraphMapper):
    """AWS implementation of a graph mapper."""

    PROVIDER_NAME = "AWS"

    def get_data(self):
        """Use Azure Resource Graph to get the data."""
        # TODO check cloudmapper to get data
        pass

    def map_data(self):
        """Use data a initialize the database model."""
        pass
