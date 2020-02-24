# -*- coding: utf-8 -*-
# Licensed under the terms of the MIT License
"""
Azure infrastructure domain mapping.
"""
# Standard library imports
import json
import logging

# Third-party imports
from pandas import DataFrame
import neomodel
from neomodel import DoesNotExist

# Local imports
from azhelper import az_cli, az_login, az_resource_graph, SUCCESS_CODE
from system_mapper.graph import (
    BaseGraphMapper, Disk, NetworkInterface, NetworkSecurityGroup,
    ResourceGroup, Subnet, VirtualNetwork, VirtualMachine)


class AzureGraphMapper(BaseGraphMapper):
    """Azure implementation of a graph mapper."""

    PROVIDER_NAME = 'AZURE'

    def get_data(self):
        """Use Azure Resource Graph to get the data."""
        data = {}
        try:
            code, login = az_login()
            logging.info('Available subscriptions:')
            logging.info(code)
            logging.info(login)
            if code == SUCCESS_CODE:
                # Get resource groups
                rg_query = (
                    'resourcecontainers '
                    '| where type == '
                    '"microsoft.resources/subscriptions/resourcegroups"')
                code, data['resource_groups'] = az_resource_graph(
                    query=rg_query)
                # Get VMs
                vm_query = (
                    'resources '
                    '| where type == "microsoft.compute/virtualmachines"')
                code, data['virtual_machines'] = az_resource_graph(
                    query=vm_query)
                # Get Network interfaces
                ni_query = (
                    'resources '
                    '| where type == "microsoft.network/networkinterfaces"')
                code, data['network_interfaces'] = az_resource_graph(
                    query=ni_query)
                # Get Networks security groups
                nsg_query = (
                    'resources '
                    ' | where type == '
                    '"microsoft.network/networksecuritygroups"')
                code, data['network_security_groups'] = az_resource_graph(
                    query=nsg_query)
                # Get Networks
                v_networks_query = (
                    'resources '
                    '| where type == "microsoft.network/virtualnetworks"')
                code, data['virtual_networks'] = az_resource_graph(
                    query=v_networks_query)
                # Get Public IPs
                public_ips_query = (
                    'resources '
                    '| where type == "microsoft.network/publicipaddresses"')
                code, data['public_ips'] = az_resource_graph(
                    query=public_ips_query)
                # Get disks
                disks_query = (
                    'resources '
                    '| where type == "microsoft.compute/disks"')
                code, data['disks'] = az_resource_graph(
                    query=disks_query)
                # Get load balancers data
                lbs_query = (
                    'resources '
                    '| where type == "microsoft.network/loadbalancers"')
                code, data['load_balancers'] = az_resource_graph(
                    query=lbs_query)
            data = data.replace('null', 'None')
            logging.info('Data:')
            logging.info(json.dumps(data))
            return data
        except Exception:
            logging.error("Execution error", exc_info=True)
            return data

    def map_data(self):
        """Use data a initialize the database model."""
        self.clear_database()
        data = self.get_data()

        # Resource group
        resource_groups = data['resource_groups']
        for rg in resource_groups:
            # TODO: location, zones
            resource_group = ResourceGroup(
                name=rg['resourceGroup'], properties=rg['properties'])
            resource_group.save()

        # Virtual Networks
        virtual_networks = data['virtual_networks']
        for vn in virtual_networks:
            virtual_network = VirtualNetwork(
                uid=vn['id'], name=vn['name'],
                properties=vn['properties'],
                tags=vn['tags'])
            virtual_network.save()
            # Map properties
            obj_properties = virtual_network.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties, vn, unwanted_properties=unwanted_props)
            # Connect ni with resource groups
            vn_resource_group = vn['resourceGroup']
            ResourceGroup.nodes.get(
                name=vn_resource_group).elements.connect(
                virtual_network)
            # Subnets
            vn_subnets = vn['properties']['subnets']
            # TODO: Divide subnets from gateway subnets
            for sn in vn_subnets:
                subnet = Subnet(
                    uid=sn['id'], name=sn['name'], properties=sn['properties'])
                subnet.save()
                virtual_network.subnets.connect(subnet)

        # Network Interfaces
        network_interfaces = data['network_interfaces']
        for ni in network_interfaces:
            network_interface = NetworkInterface(
                uid=ni['id'], name=ni['name'], properties=ni['properties'],
                tags=ni['tags'])
            network_interface.save()
            # Map properties
            obj_properties = network_interface.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id']
            self.add_properties(
                obj_properties, ni, unwanted_properties=unwanted_props)
            # Connect ni with resource groups
            ni_resource_group = ni['resourceGroup']
            ResourceGroup.nodes.get(
                name=ni_resource_group).elements.connect(
                network_interface)
            # Subnet assingment
            ip_configs = ni['properties']['ipConfigurations']
            for ipc in ip_configs:
                ni_subnet = ipc['properties']['subnet']['id']
                network_interface.subnet.connect(Subnet.nodes.get(
                    uid=ni_subnet))

        # Virtual Machines
        virtual_machines = data['virtual_machines']
        for vm in virtual_machines:
            virtual_machine = VirtualMachine(
                uid=vm['id'],
                name=vm['name'],
                properties=vm['properties'],
                tags=vm['tags'])
            virtual_machine.save()
            # Map properties
            obj_properties = virtual_machine.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties, vm, unwanted_properties=unwanted_props)
            # Connect virtual machines with resource groups
            vm_resource_group = vm['resourceGroup']
            ResourceGroup.nodes.get(
                name=vm_resource_group).elements.connect(
                virtual_machine)
            # Connect vm with net_interfaces
            nis = vm['properties']['networkProfile']['networkInterfaces']
            for ni in nis:
                net_interface_id = ni['id']
            virtual_machine.network_interfaces.connect(
                    NetworkInterface.nodes.get(uid=net_interface_id))

        # Disks
        disks = data['disks']
        for d in disks:
            disk = Disk(
                uid=d['id'], name=d['name'], properties=d['properties'],
                tags=d['tags'])
            disk.save()
            # Map properties
            obj_properties = disk.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'managedBy', 'id']
            self.add_properties(
                obj_properties, d, unwanted_properties=unwanted_props)
            # Connect disk with resource groups
            d_resource_group = d['resourceGroup']
            ResourceGroup.nodes.get(
                name=d_resource_group).elements.connect(
                disk)
            try:
                # Connect disk with vm
                d_virtual_machine = d['managedBy']

                VirtualMachine.nodes.get(
                    uid=d_virtual_machine).disks.connect(disk)
            except (DoesNotExist, KeyError) as e:
                logging.info(
                    "Error while connecting disk with virtual machine")
                logging.info(e)
                pass

        # Network Security Group
        ns_groups = data['network_security_groups']
        for nsg in ns_groups:
            ns_group = NetworkSecurityGroup(
                uid=nsg['id'], name=nsg['name'],
                properties=nsg['properties'],
                tags=nsg['tags'])
            ns_group.save()
            # Map properties
            obj_properties = ns_group.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'managedBy', 'id',
                'name']
            self.add_properties(
                obj_properties, nsg, unwanted_properties=unwanted_props)
            # Connect disk with resource groups
            d_resource_group = nsg['resourceGroup']
            ResourceGroup.nodes.get(
                name=d_resource_group).elements.connect(
                ns_group)

        # Network Peerings
            # Using GatewaySubnets

        # Public IP

    def export_data(data):
        """Export data using Pandas."""
        df_data = DataFrame.from_dict(data)
        logging.info(df_data)
        return df_data


if __name__ == '__main__':
    """Test AzureMapper."""
    az_mapper = AzureGraphMapper()
    az_mapper.map_data()
    logging.info(az_cli(['account', 'list']))
