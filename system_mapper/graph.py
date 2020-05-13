# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Cloud application domain mapping.
"""
# Standard library imports
import sys
import logging

# Third-party imports
from neomodel import (
    clear_neo4j_database, config, db, JSONProperty, StructuredNode,
    StringProperty, Relationship)

from system_mapper.config import CONFIG


# ------------------------- Interface of a Graph mapper -----------------------
class BaseGraphMapper():
    """Base class to implement a graph mapper."""

    PROVIDER_NAME = None

    def __init__(
            self, database_url=CONFIG['neo4j_database_url'],
            logfile=None, logger=False):
        self.config = CONFIG
        self.database_url = database_url
        config.DATABASE_URL = self.database_url
        self.db = db
        if logger:
            self.create_logger(logfile=logfile)

    def add_property(
            self, element_properties, property_key='key', property_value=None):
        """Add property to the given element using the properties relation."""
        new_property = Property(key=property_key, value=property_value)
        new_property.save()
        element_properties.connect(new_property)

    def add_tag(self, element_tags, tag_key, tag_value):
        """Add tag to element using the tags relation."""
        new_tag = Tag(key=tag_key, value=tag_value)
        new_tag.save()
        element_tags.connect(new_tag)

    def add_tags(self, element_tags, tags):
        """Add mulitple tags to an element."""
        if isinstance(tags, dict):
            for key, value in tags.items():
                self.add_tag(element_tags, key, value)

    def add_properties(
            self, element_properties, properties, unwanted_properties=['key']):
        """Add multiple properties to an element."""
        for key, value in properties.items():
            if key not in unwanted_properties and value:
                self.add_property(
                    element_properties, property_key=key, property_value=value)

    def get_app_data(
            self,
            host,
            port=None,
            app_container_url=None,
            app_container_token=None,
            user=None,
            password=None):
        """Get the app data from the application container."""
        raise NotImplementedError

    def get_data(self):
        """Get the data from the provider."""
        raise NotImplementedError

    def map_data(self):
        """Persist data using the graph data base elements definitions."""
        raise NotImplementedError

    def clear_database(self):
        """Delete database."""
        clear_neo4j_database(self.db)

    def create_logger(self, logfile=None):
        """
        Create a logging mechanism.

        Create a logging handler that will write to stdout and optionally
        to a log file
        """
        stdout_handler = logging.StreamHandler(sys.stdout)
        if logfile is not None:
            file_handler = logging.FileHandler(filename=logfile)
            handlers = [file_handler, stdout_handler]
        else:
            handlers = [stdout_handler]

        # Configure logging mechanism
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )


# -------------------- Metamodel/Model definition ----------------------------
class Owner(StructuredNode):
    """Owner of an element."""

    uid = StringProperty(unique_index=True)
    regions = Relationship('Region', 'REGION')
    elements = Relationship('Element', 'OWNED_ELEMENT')
    properties = JSONProperty()
    object_tags = Relationship('Tag', 'OBJ_TAG')
    object_properties = Relationship('Property', 'OBJ_PROPERTY')
    resource_groups = Relationship('ResourceGroup', 'OWNED_RESOURCE_GROUP')


class Region(StructuredNode):
    """Region of an owner where the elements are available."""

    name = StringProperty()
    properties = JSONProperty()
    availability_zone = Relationship(
        'AvailabilityZone', 'AVAILABILITY_ZONE')


# --------------------------- Elements relationships
class AvailabilityZone(StructuredNode):
    """AV of a region where the elements are available."""

    name = StringProperty()
    properties = JSONProperty()
    elements = Relationship('Element', 'ELEMENT')
    resource_groups = Relationship('ResourceGroup', 'RESOURCE_GROUP')


class ResourceGroup(StructuredNode):
    """RG that groups elements on an AV."""

    name = StringProperty()
    subscription_id = StringProperty(unique_index=True)
    properties = JSONProperty()
    elements = Relationship('Element', 'ELEMENT_RESOURCE_GROUP')
    object_tags = Relationship('Tag', 'OBJ_TAG')
    object_properties = Relationship('Property', 'OBJ_PROPERTY')


class Property(StructuredNode):
    """Property of an element."""

    key = StringProperty()
    value = StringProperty()


class Tag(Property):
    """key-value tag property of an element."""

    pass


class Element(StructuredNode):
    """Base element type."""

    __abstrac__abstract_node__ = True
    uid = StringProperty(unique_index=True)
    name = StringProperty()
    properties = JSONProperty()
    object_properties = Relationship('Property', 'OBJ_PROPERTY')
    tags = JSONProperty()
    object_tags = Relationship('Tag', 'OBJ_TAG')


# ---------------------------- Elements
class VirtualMachine(Element):
    """Virtual Machine concept."""

    disks = Relationship('Disk', 'DISK')
    network_interfaces = Relationship(
        'NetworkInterface', 'NETWORK_INTERFACE')
    deployed_applications = Relationship(
        'DeployedApplication', 'DEPLOYED_APPLICATION')


class Database(VirtualMachine):
    """Database concept."""

    databases = Relationship('Database', 'DATA_SOURCE')


class DeployedApplication(Element):
    """Application deployed concept."""

    pass


class Disk(Element):
    """Disk concept."""

    pass


class LoadBalancer(Element):
    """Load Balancer concept."""

    network_interfaces = Relationship('NetworkInterface', 'VM_BACKEND_POOL')
    public_ip = Relationship('PublicIp', 'LB_PUBLIC_IP')
    inbound_rules = Relationship('InboundRule', 'INBOUND_RULE')
    outbound_rules = Relationship('OutboundRule', 'OUTBOUND_RULE')
    backend_pool_id = StringProperty()


class PublicIp(Element):
    """Public IP concept."""

    pass


class PrivateIp(Element):
    """Private IP concept."""

    pass


class InboundRule(Element):
    """Inbound rule concept."""

    pass


class OutboundRule(Element):
    """Outbound rule concept."""

    pass


class NetworkSecurityGroup(Element):
    """NSG concept."""

    inbound_rules = Relationship('InboundRule', 'INBOUND_RULE')
    outbound_rules = Relationship('OutboundRule', 'OUTBOUND_RULE')
    network_interfaces = Relationship(
        'NetworkInterface', 'NETWORK_SECURITY_GROUP')


class NetworkInterface(Element):
    """Network interface concept."""

    public_ip = Relationship('PublicIp', 'PUBLIC_IP')
    private_ip = Relationship('PrivateIp', 'PRIVATE_IP')
    subnet = Relationship('Subnet', 'SUBNET_NI')


class Subnet(Element):
    """Subnet concept."""

    pass


class Connection(Element):
    """Virtual network connection."""

    pass


class GatewaySubnet(Subnet):
    """Gateway subnet VPN concept."""

    connection = Relationship('Connection', 'CONNECTED_SUBNET')


class VirtualNetwork(Element):
    """Virtual Network concept."""

    subnets = Relationship('Subnet', 'SUBNET')
    network_interfaces = Relationship(
        'NetworkInterface', 'NETWORK_INTERFACE_VN')


class Service(Element):
    """Service concept."""

    service_name = StringProperty()
    elements = Relationship('Element', 'SERVICE_ELEMENTS')


class Storage(Element):
    """File storage element."""

    pass


if __name__ == '__main__':

    class TestGraphMapper(BaseGraphMapper):
        """Test graph mapper."""

        PROVIDER_NAME = "TEST"

        def get_data(self):
            """Create data dict for test."""
            return {
                'properties': {
                    'vm_name': 'TestVM',
                    'vm_size': 'Standard_B2s',
                    'os': 'Windows',
                    'os_image': '2016-Datacenter-WindowsServer',
                    'os_disk_size': '127'
                    },
                'disk': {'properties': {
                            'size': '200'
                        }
                    },
                'private_ip': '172.31.201.100',
                'network_interface': {
                    'properties': {
                        'ni_name': 'TestNI',
                        }
                    }
                }

        def map_data(self):
            """Map test data to the graph db."""
            data = self.get_data()
            virtual_machine = VirtualMachine(value='Virtual Machine').save()
            network_interface = NetworkInterface(
                value='Network Interface').save()
            virtual_machine.network_interfaces.connect(network_interface)
            for key, value in data['network_interface']['properties'].items():
                new_property = Property(key=key, value=value)
                new_property.save()
                network_interface.object_properties.connect(new_property)
            for key, value in data['properties'].items():
                new_property = Property(key=key, value=value)
                new_property.save()
                virtual_machine.object_properties.connect(new_property)
            if 'disk' in data:
                new_disk = Disk(value="Disk")
                new_disk.save()
                virtual_machine.disks.connect(new_disk)

    mapper = TestGraphMapper()
    mapper.map_data()
