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
from neomodel import DoesNotExist
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests_ntlm import HttpNtlmAuth
import xmltodict

# Local imports
from system_mapper.provider_azure.azhelper import (
    az_cli, az_login, az_resource_graph, SUCCESS_CODE)
from system_mapper.graph import (
        DeployedApplication, BaseGraphMapper, Database, Disk, NetworkInterface,
        NetworkSecurityGroup, ResourceGroup, Subnet, VirtualNetwork,
        VirtualMachine, LoadBalancer, PublicIp, PrivateIp, Service, Storage)


# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class AzureGraphMapper(BaseGraphMapper):
    """Azure implementation of a graph mapper."""

    PROVIDER_NAME = 'AZURE'

    def get_app_data(
            self,
            host):
        """
        Get deployed application data from IIS.
        """
        port = self.config['port']
        app_container_url = self.config['app_container_url']
        app_container_token = self.config['app_container_token']
        user = self.config['app_container_user']
        password = self.config['app_container_password']
        try:
            response = []
            # Check a way to search file
            headers = {
                'Access-Token': 'Bearer {token}'.format(
                    token=app_container_token),
                'Accept': 'application/hal+json'
                }
            # TODO: Setup cert file of the IIS server
            base_url = 'https://{host}:{port}'.format(host=host, port=port)
            base_info = requests.get(
                base_url + app_container_url,
                headers=headers,
                verify=False,
                auth=HttpNtlmAuth(user, password))
            applications_status = base_info.status_code
            applications_content = base_info.text
            if applications_status == requests.codes.ok:
                applications = json.loads(applications_content)
                if 'websites' in applications:
                    for application in applications['websites']:
                        app_info_url = application['_links']['self']['href']
                        app_info = requests.get(
                            base_url + app_info_url,
                            headers=headers,
                            verify=False,
                            auth=HttpNtlmAuth(user, password))
                        app_info_status = app_info.status_code
                        app_info_content = json.loads(
                            app_info.text)
                        if app_info_status == requests.codes.ok:
                            dir_files_url = app_info_content[
                                '_links']['files']['href']
                            web_config = {}
                            dir_files_info = requests.get(
                                base_url + dir_files_url,
                                headers=headers,
                                verify=False,
                                auth=HttpNtlmAuth(user, password))
                            dir_files_info_content = json.loads(
                                dir_files_info.text)
                            files_info_url = dir_files_info_content[
                                '_links']['files']['href']
                            files_info = json.loads(requests.get(
                                base_url + files_info_url,
                                headers=headers,
                                verify=False,
                                auth=HttpNtlmAuth(user, password)).text)

                            for file in files_info['files']:
                                if file['name'] == "web.config":
                                    file_url = file['_links']['self']['href']
                                    file_info = requests.get(
                                        base_url + file_url,
                                        headers=headers,
                                        verify=False,
                                        auth=HttpNtlmAuth(user, password))
                                    file_info_content_url = json.loads(
                                        file_info.text)['file_info'][
                                            '_links']['self']['href']
                                    file_content = requests.get(
                                        base_url +
                                        file_info_content_url.replace(
                                            '/api/files',
                                            '/api/files/content'),
                                        headers=headers,
                                        verify=False,
                                        auth=HttpNtlmAuth(user, password)).text
                                    web_config = dict(
                                            xmltodict.parse(
                                                file_content,
                                                process_namespaces=True))
                                    app_info_content['web_config'] = web_config
                        response.append(app_info_content)
            return response
        except Exception as e:
            logging.error(e)
            return {}

    def get_data(self):
        """Use Azure Resource Graph to get the data."""
        data = {}
        try:
            code, login = az_login()
            logging.info('Available subscriptions:')
            logging.info(code)
            logging.info(login)
            if code == SUCCESS_CODE:
                # Refresh accounts lists
                logging.info(az_cli(["account", "list", "--refresh"]))

                # Get resource groups
                rg_query = (
                    'resourcecontainers '
                    '| where type == '
                    '"microsoft.resources/subscriptions/resourcegroups"')
                code, data['resource_groups'] = az_resource_graph(
                    query=rg_query)

                # Get App service instances
                app_service_query = (
                    'resources '
                    '| where type == "microsoft.web/sites"')
                code, data['app_services'] = az_resource_graph(
                    query=app_service_query)

                # Get server farms
                app_services_plans_query = (
                    'resources '
                    '| where type == "microsoft.web/serverfarms"')
                code, data['app_services_plans'] = az_resource_graph(
                    query=app_services_plans_query)

                # Get Storage accounts
                storage_accounts_query = (
                    'resources '
                    '| where type == '
                    '"microsoft.storage/storageaccounts"')
                code, data['storage_accounts'] = az_resource_graph(
                    query=storage_accounts_query)

                # Get Network interfaces
                ni_query = (
                    'resources '
                    '| where type == "microsoft.network/networkinterfaces"')
                code, data['network_interfaces'] = az_resource_graph(
                    query=ni_query)

                # Get Public IPs
                public_ips_query = (
                    'resources '
                    '| where type == "microsoft.network/publicipaddresses"')
                code, data['public_ips'] = az_resource_graph(
                    query=public_ips_query)

                # Get VMs
                vm_query = ("""
resources
 | where type =~ 'microsoft.compute/virtualmachines'
 | extend nics=array_length(properties.networkProfile.networkInterfaces)
 | mv-expand nic=properties.networkProfile.networkInterfaces
 | where nics == 1 or nic.properties.primary =~ 'true' or isempty(nic)
 | project id, name, size=tostring(properties.hardwareProfile.vmSize),
 nicId = tostring(nic.id), type, properties = tostring(properties),
 resourceGroup = resourceGroup, tostring(tags), subscriptionId, tenantId
 | join kind=leftouter (
    Resources
    | where type =~ 'microsoft.network/networkinterfaces'
     | extend ipConfigsCount=array_length(properties.ipConfigurations)
     | mv-expand ipconfig=properties.ipConfigurations
     | where ipConfigsCount == 1 or ipconfig.properties.primary =~ 'true'
    | project nicId = id,
     publicIpId = tostring(ipconfig.properties.publicIPAddress.id),
     privateIpAddress = tostring(ipconfig.properties.privateIPAddress))
 on nicId
 | project-away nicId1
 | summarize by id, name, size, nicId, type, properties, resourceGroup, tags,
 subscriptionId, tenantId, publicIpId, privateIpAddress
 | join kind=leftouter (
    Resources
    | where type =~ 'microsoft.network/publicipaddresses'
    | project publicIpId = id, publicIpAddress = properties.ipAddress)
 on publicIpId
 | project-away publicIpId1
""")
                code, data['raw_virtual_machines'] = az_resource_graph(
                    query=vm_query)

                # Get application data and parse properties:
                data['applications'] = []
                data['virtual_machines'] = []
                for vm in data['raw_virtual_machines']:
                    vm['properties'] = json.loads(vm['properties'])
                    data['virtual_machines'].append(vm)
                    if (not self.is_db_virtual_machine(vm) and
                            self.config['get_app_container_info']):
                        # Get application data using public ip
                        vm_ip = (
                            vm['publicIpAddress']
                            if 'publicIpAddress' in vm and vm['publicIpAddress']
                            else vm['privateIpAddress'])
                        app_data = {}
                        app_data['virtual_machine_id'] = vm['id']
                        app_data['applications'] = self.get_app_data(vm_ip)
                        apps = data['applications']
                        apps.append(app_data)
                        data['applications'] = apps

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
                # Get databases
                dbs_query = (
                    'resources'
                    ' | where type == "microsoft.sql/servers/databases"')
                code, data['databases'] = az_resource_graph(
                    query=dbs_query)

            # data = data.replace('null', 'None')
            logging.info('Data:')
            logging.info(json.dumps(data))
            return data
        except Exception as e:
            logging.error("Execution error", exc_info=True)
            raise e
            # return data

    def is_db_virtual_machine(self, data):
        """
        Check if the data corresponds to a virtual machine used as a database.
        """
        is_db_vm = False
        properties = data['properties']
        if 'storageProfile' in properties:
            storage_profile = properties['storageProfile']
            if 'imageReference' in storage_profile:
                publisher = storage_profile['imageReference']['publisher']
                is_db_vm = publisher in self.config['database_strings']
        return is_db_vm

    def map_data(self, reset=False):
        """Use data a initialize the database model."""
        if reset:
            self.clear_database()
        data = self.get_data()

        # Resource group
        resource_groups = data['resource_groups']
        for rg in resource_groups:
            # TODO: location, zones
            resource_group = ResourceGroup(
                uid=rg['id'],
                subscription_id=rg['subscriptionId'],
                name=rg['resourceGroup'], properties=rg['properties'])
            resource_group.save()

            # Map properties
            obj_properties = resource_group.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties, rg, unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = resource_group.object_tags
            self.add_tags(obj_tags, rg['tags'])

        # Public IP
        public_ips = data['public_ips']
        for pip in public_ips:
            p_ip = PublicIp(
                uid=pip['id'], name=pip['name'],
                properties=pip['properties'],
                tags=pip['tags'])
            p_ip.save()

            # Map properties
            obj_properties = p_ip.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties, pip, unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = p_ip.object_tags
            self.add_tags(obj_tags, pip['tags'])

            # Connect public ip with resource groups
            public_ip_resource_group = pip['resourceGroup']
            ResourceGroup.nodes.get(
                name=public_ip_resource_group,
                subscription_id=pip['subscriptionId']).elements.connect(
                p_ip)

        # App Services Plan
        app_services_plans = data['app_services_plans']
        for app_service_plan in app_services_plans:
            service_plan = Service(
                uid=app_service_plan['id'].lower(),
                name=app_service_plan['name'],
                service_name='AppServicePlan',
                properties=app_service_plan['properties'],
                tags=app_service_plan['tags'])
            service_plan.save()

            # Map properties
            obj_properties = service_plan.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties,
                app_service_plan,
                unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = service_plan.object_tags
            self.add_tags(obj_tags, app_service_plan['tags'])

            # Connect public ip with resource groups
            app_resource_group = app_service_plan['resourceGroup']
            ResourceGroup.nodes.get(
                name=app_resource_group,
                subscription_id=app_service_plan['subscriptionId']
                ).elements.connect(
                    service_plan)

        # App Services
        app_services = data['app_services']
        for app_service in app_services:
            service = Service(
                uid=app_service['id'],
                name=app_service['name'],
                service_name='AppService',
                properties=app_service['properties'],
                tags=app_service['tags'])
            service.save()

            # Map properties
            obj_properties = service.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties,
                app_service,
                unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = service.object_tags
            self.add_tags(obj_tags, app_service['tags'])

            # Connect public ip with resource groups
            app_resource_group = app_service['resourceGroup']
            ResourceGroup.nodes.get(
                name=app_resource_group,
                subscription_id=app_service['subscriptionId']
                ).elements.connect(service)

            # Connect to server farm (AppServicePlan)
            app_service_plan_id = app_service['properties']['serverFarmId']
            Service.nodes.get(
                uid=app_service_plan_id.lower()).elements.connect(service)

        # Storage Account
        storage_accounts = data['storage_accounts']
        for storage_account in storage_accounts:
            storage = Storage(
                uid=storage_account['id'],
                name=storage_account['name'],
                properties=storage_account['properties'],
                tags=storage_account['tags'])
            storage.save()

            # Map properties
            obj_properties = storage.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties,
                storage_account,
                unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = storage.object_tags
            self.add_tags(obj_tags, storage_account['tags'])

            # Connect public ip with resource groups
            storage_resource_group = storage_account['resourceGroup']
            ResourceGroup.nodes.get(
                name=storage_resource_group,
                subscription_id=storage_account['subscriptionId']
                ).elements.connect(
                    storage)

        # Load balancers
        load_balancers = data['load_balancers']
        for lb in load_balancers:
            lbalancer = LoadBalancer(
                uid=lb['id'], name=lb['name'],
                properties=lb['properties'],
                tags=lb['tags'],
                backend_pool_id=lb['properties'][
                        'backendAddressPools'][0]['id'])
            lbalancer.save()

            # Map properties
            obj_properties = lbalancer.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties, lb, unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = lbalancer.object_tags
            self.add_tags(obj_tags, lb['tags'])

            # Connect load balancer with resource groups
            lb_resource_group = lb['resourceGroup']
            ResourceGroup.nodes.get(
                name=lb_resource_group,
                subscription_id=lb['subscriptionId']).elements.connect(
                    lbalancer)

            # Map public Ip address
            lb_public_id = lb['properties']['frontendIPConfigurations'][0][
                'properties']['publicIPAddress']['id']
            lbalancer.public_ip.connect(PublicIp.nodes.get(uid=lb_public_id))

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

            # Map tags
            obj_tags = virtual_network.object_tags
            self.add_tags(obj_tags, vn['tags'])

            # Connect ni with resource groups
            vn_resource_group = vn['resourceGroup']
            ResourceGroup.nodes.get(
                name=vn_resource_group,
                subscription_id=vn['subscriptionId']).elements.connect(
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

            # Map tags
            obj_tags = network_interface.object_tags
            self.add_tags(obj_tags, ni['tags'])

            # Connect ni with resource groups
            ni_resource_group = ni['resourceGroup']
            ResourceGroup.nodes.get(
                name=ni_resource_group,
                subscription_id=ni['subscriptionId']).elements.connect(
                    network_interface)

            ip_configs = ni['properties']['ipConfigurations']
            for ipc in ip_configs:
                # Subnet assingment
                ni_subnet = ipc['properties']['subnet']['id']
                network_interface.subnet.connect(Subnet.nodes.get(
                    uid=ni_subnet))

                # Private Ip address
                ni_subnet = ipc['properties']['subnet']['id']
                private_ip = PrivateIp(
                    name=ipc['properties']['privateIPAddress'])
                private_ip.save()
                network_interface.private_ip.connect(private_ip)

                # Connect with public ip address
                if 'publicIPAddress' in ipc['properties']:
                    ni_subnet = ipc['properties']['publicIPAddress']['id']
                    network_interface.public_ip.connect(PublicIp.nodes.get(
                        uid=ni_subnet))

                # Connect with load balancer
                if 'loadBalancerBackendAddressPools' in ipc['properties']:
                    backend_pool_id = ipc['properties'][
                        'loadBalancerBackendAddressPools'][0]['id']
                    try:
                        LoadBalancer.nodes.get(
                            backend_pool_id=backend_pool_id
                            ).network_interfaces.connect(network_interface)
                    except DoesNotExist as e:
                        logging.info(
                            "Error connecting Load balancer "
                            "to netwoerk interface")
                        logging.info(e)

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

            # Map tags
            obj_tags = ns_group.object_tags
            self.add_tags(obj_tags, nsg['tags'])

            # Connect network security group with resource groups
            d_resource_group = nsg['resourceGroup']
            ResourceGroup.nodes.get(
                name=d_resource_group,
                subscription_id=nsg['subscriptionId']).elements.connect(
                    ns_group)

            # Connect NSG with interfaces
            if 'networkInterfaces' in nsg['properties']:
                for ni in nsg['properties']['networkInterfaces']:
                    ni_id = ni['id']
                    ns_group.network_interfaces.connect(
                        NetworkInterface.nodes.get(uid=ni_id))

        # Virtual Machines
        virtual_machines = data['virtual_machines']
        for vm in virtual_machines:
            if self.is_db_virtual_machine(vm):
                virtual_machine = Database(
                    uid=vm['id'],
                    name=vm['name'],
                    properties=vm['properties'],
                    tags=vm['tags'])
                virtual_machine.save()
            else:
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

            # Map tags
            obj_tags = virtual_machine.object_tags
            self.add_tags(obj_tags, vm['tags'])

            # Connect virtual machines with resource groups
            vm_resource_group = vm['resourceGroup']
            ResourceGroup.nodes.get(
                name=vm_resource_group,
                subscription_id=vm['subscriptionId']).elements.connect(
                    virtual_machine)

            # Connect vm with net_interfaces
            nis = vm['properties']['networkProfile']['networkInterfaces']
            for ni in nis:
                net_interface_id = ni['id']
            virtual_machine.network_interfaces.connect(
                    NetworkInterface.nodes.get(uid=net_interface_id))

        # Map databases
        databases = data['databases']
        for db in databases:
            database = Database(
                    uid=db['id'],
                    name=db['name'],
                    properties=db['properties'],
                    tags=db['tags'])
            database.save()

            # Map properties
            obj_properties = database.object_properties
            unwanted_props = [
                'properties', 'resourceGroup', 'tags', 'id', 'name']
            self.add_properties(
                obj_properties, db, unwanted_properties=unwanted_props)

            # Map tags
            obj_tags = database.object_tags
            self.add_tags(obj_tags, db['tags'])

            # Connect virtual machines with resource groups
            db_resource_group = db['resourceGroup']
            ResourceGroup.nodes.get(
                name=db_resource_group,
                subscription_id=db['subscriptionId']).elements.connect(
                    database)

        # Map to IIS data
        applications = data['applications']
        for vm_app_data in applications:
            for app_data in vm_app_data['applications']:
                application = DeployedApplication(
                    uid=app_data['id'],
                    name=app_data['name'],
                    properties=app_data)
                application.save()

                # Map properties
                unwanted_properties = ['name', 'id']
                self.add_properties(
                    application.object_properties,
                    app_data,
                    unwanted_properties=unwanted_properties)

                # Map deployed app to virtual_machine
                VirtualMachine.nodes.get(
                    uid=vm_app_data['virtual_machine_id']
                    ).deployed_applications.connect(application)

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

            # Map tags
            obj_tags = disk.object_tags
            self.add_tags(obj_tags, d['tags'])

            # Connect disk with resource groups
            d_resource_group = d['resourceGroup']
            ResourceGroup.nodes.get(
                name=d_resource_group,
                subscription_id=d['subscriptionId']).elements.connect(
                disk)
            try:
                # Connect disk with vm
                d_virtual_machine = d['managedBy']

                VirtualMachine.nodes.get(
                    uid=d_virtual_machine).disks.connect(disk)
            except (DoesNotExist, KeyError) as e:
                logging.error(
                    "Error while connecting disk with virtual machine")
                logging.error(e)

        # TODO
        # Network Peerings
            # Using GatewaySubnets

    def export_data(data, filename='export_data.csv'):
        """Export data using Pandas."""
        df_data = DataFrame.from_dict(data)
        logging.info(df_data)
        df_data.to_csv(filename)
        return df_data


def run_mapper(reset=True):
    """Run mapper script to add populate database."""
    az_mapper = AzureGraphMapper()
    az_mapper.map_data(reset=reset)
