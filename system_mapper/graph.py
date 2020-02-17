# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Infrastructure domain mapping.
"""
# Standard library imports
import sys
import logging

# Third-party imports
from neomodel import (
    clear_neo4j_database, config, db, JSONProperty, StructuredNode,
    StringProperty, RelationshipTo, RelationshipFrom)


# ------------------------- Interface of a Graph mapper -----------------------
class BaseGraphMapper():
    """Base class to implement a graph mapper."""

    PROVIDER_NAME = None

    def __init__(
            self, database_url='bolt://neo4j:ne@4j@localhost:7687',
            logfile=None):
        self.database_url = database_url
        config.DATABASE_URL = self.database_url
        self.db = db
        self.create_logger(logfile=logfile)

    def add_property(
            self, element_properties, property_key='key', property_value=None):
        """Add property to the given element using the properties relation."""
        new_property = Property(key=property_key, value=property_value)
        new_property.save()
        element_properties.connect(new_property)

    def add_properties(
            self, element_properties, properties, unwanted_properties=['key']):
        """Add multiple properties to an element."""
        for key, value in properties.items():
            if key not in unwanted_properties and value:
                self.add_property(
                    element_properties, property_key=key, property_value=value)

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

    value = StringProperty()
    regions = RelationshipTo('Region', 'REGION')
    elements = RelationshipTo('Element', 'OWNED_ELEMENT')
    properties = JSONProperty()


class Region(StructuredNode):
    """Region of an owner where the elements are available."""

    name = StringProperty()
    properties = JSONProperty()
    region = RelationshipFrom('Owner', 'REGION')
    availability_zone = RelationshipTo(
        'AvailabilityZone', 'AVAILABILITY_ZONE')


# --------------------------- Elements relationships
class AvailabilityZone(StructuredNode):
    """AV of a region where the elements are available."""

    name = StringProperty()
    properties = JSONProperty()
    availability_zone = RelationshipFrom(
        'Region', 'AVAILABILITY_ZONE')
    elements = RelationshipTo('Element', 'ELEMENT')
    resource_groups = RelationshipTo('ResourceGroup', 'RESOURCE_GROUP')


class ResourceGroup(StructuredNode):
    """RG that groups elements on an AV."""

    name = StringProperty()
    properties = JSONProperty()
    availability_zone = RelationshipFrom(
        'AvailabilityZone', 'RESOURCE_GROUP')
    elements = RelationshipTo('Element', 'ELEMENT_RESOURCE_GROUP')


class Property(StructuredNode):
    """Property of an element."""

    key = StringProperty()
    value = StringProperty()
    element = RelationshipFrom('Element', 'OBJ_PROPERTY')


class Element(StructuredNode):
    """Base element type."""

    __abstrac__abstract_node__ = True
    uid = StringProperty(unique_index=True)
    name = StringProperty()
    properties = JSONProperty()
    object_properties = RelationshipTo('Property', 'OBJ_PROPERTY')
    tags = JSONProperty()
    availability_zone = RelationshipFrom(
        'AvailabilityZone', 'ELEMENT')
    resource_group = RelationshipFrom(
        'ResourceGroup', 'ELEMENT_RESOURCE_GROUP')
    owner = RelationshipFrom('Owner', 'OWNER_ELEMENT')


# ---------------------------- Elements
class VirtualMachine(Element):
    """Virtual Machine concept."""

    disks = RelationshipTo('Disk', 'DISK')
    network_interfaces = RelationshipTo(
        'NetworkInterface', 'NETWORK_INTERFACE')


class Disk(Element):
    """Disk concept."""

    virtual_machines = RelationshipFrom('VirtualMachine', 'DISK')


class LoadBalancer(VirtualMachine):
    """Load Balancer concept."""

    pass


class PublicIp(Element):
    """Public IP concept."""

    network_interface = RelationshipFrom('NetworkInterface', 'PUBLIC IP')


class PrivateIp(Element):
    """Private IP concept."""

    network_interface = RelationshipFrom('NetworkInterface', 'PRIVATE IP')


class InboundRule(Element):
    """Inbound rule concept."""

    network_security_group = RelationshipFrom(
        'NetworkSecurityGroup', 'INBOUND_RULE')


class OutboundRule(Element):
    """Outbound rule concept."""

    network_security_group = RelationshipFrom(
        'NetworkSecurityGroup', 'OUTBOUND_RULE')


class NetworkSecurityGroup(Element):
    """NSG concept."""

    network_interface = RelationshipFrom(
        'NetworkInterface', 'NETWORK_SECURITY_GROUP')
    inbound_rules = RelationshipTo('InboundRule', 'INBOUND_RULE')
    outbound_rules = RelationshipTo('OutboundRule', 'OUTBOUND_RULE')


class NetworkInterface(Element):
    """Network interface concept."""

    virtual_machine = RelationshipFrom('VirtualMachine', 'NETWORK_INTERFACE')
    public_ip = RelationshipTo('PublicIp', 'PUBLIC_IP')
    private_ip = RelationshipTo('PrivateIp', 'PRIVATE_IP')
    network_security_group = RelationshipTo(
        'NetworkSecurityGroup', 'NETWORK_SECURITY_GROUP')
    subnet = RelationshipTo('Subnet', 'SUBNET_NI')
    virtual_network = RelationshipFrom(
        'VirtualNetwork', 'NETWORK_INTERFACE_VN')


class Subnet(Element):
    """Subnet concept."""

    virtual_network = RelationshipFrom('VirtualNetwork', 'SUBNET')
    network_interfaces = RelationshipFrom('NetworkInterface', 'SUBNET_NI')


class Connection(Element):
    """Virtual network connection."""

    gateways = RelationshipFrom('GatewaySubnet', 'CONNECTED_SUBNET')


class GatewaySubnet(Subnet):
    """Gateway subnet VPN concept."""

    connection = RelationshipTo('Connection', 'CONNECTED_SUBNET')


class VirtualNetwork(Element):
    """Virtual Network concept."""

    subnets = RelationshipTo('Subnet', 'SUBNET')
    network_interfaces = RelationshipTo(
        'NetworkInterface', 'NETWORK_INTERFACE_VN')


class Service(Element):
    """Service concept."""

    elements = RelationshipTo('Element', 'SERVICE_ELEMENTS')


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
