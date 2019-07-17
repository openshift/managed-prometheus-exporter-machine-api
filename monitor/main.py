#!/usr/bin/env python

from sets import Set

import logging
import os
import time

from prometheus_client import start_http_server, Gauge
from kubernetes import client, config
from kubernetes.client import ApiClient, Configuration
from openshift.dynamic import DynamicClient

MACHINE_STATUS = Gauge('machine_api_status',"Status of Machine CRs", labelnames=['machine_name','node_name','instance_state','instance_id'])
MACHINE_INFO = Gauge('machine_api_info',"Information about Machine CRs", labelnames=['machine_name', 'region', 'availability_zone', 'instance_type', 'machine_creation_time', 'image_id'])

# A list (implemented as a Set) of all active Machines
ACTIVE_MACHINES = Set([])

def get_machines(dynamic_client,namespace):
    """Gets all of the Machine objects from the cluster from the specified namespace.
    """
    machines = dynamic_client.resources.get(kind='Machine')
    return machines.get(namespace=namespace).items

def collect(dynamic_client, namespace):
    """
    Collect the current data from the AWS API.
    """

    # List of volumes that we've actually had data back for the API
    seen_machines = Set([])
    machines = get_machines(dynamic_client, namespace)
    for machine in machines:
        seen_machines.add(machine['metadata']['name'])
        ACTIVE_MACHINES.add(machine['metadata']['name'])

        node_name = ""
        instanceid = ""
        instance_state = "not-created"
        value = 1
        if 'nodeRef' in machine['status'].keys():
            node_name = machine['status']['nodeRef']['name']
        else:
            value = 0

        if 'providerStatus' in machine['status'].keys():
            if 'instanceId' in machine['status']['providerStatus'].keys():
                instanceid = machine['status']['providerStatus']['instanceId']
            else:
                value = 0
            if 'instanceState' in machine['status']['providerStatus'].keys():
                instance_state = machine['status']['providerStatus']['instanceState']

        MACHINE_STATUS.labels(
            machine_name   = machine['metadata']['name'],
            node_name      = node_name,
            instance_state = instance_state,
            instance_id    = instanceid
        ).set(value)

        MACHINE_INFO.labels(
            machine_name          = machine['metadata']['name'],
            region                = machine['spec']['providerSpec']['value']['placement']['region'],
            availability_zone     = machine['spec']['providerSpec']['value']['placement']['availabilityZone'],
            instance_type         = machine['spec']['providerSpec']['value']['instanceType'],
            machine_creation_time = machine['metadata']['creationTimestamp'],
            image_id              = machine['spec']['providerSpec']['value']['ami']['id']
        ).set(value)

    logging.debug("Have %d ACTIVE_MACHINES, seen %d machines, total machines from list_metrics %d",len(ACTIVE_MACHINES),len(seen_machines),len(machines))
    for inactive_machine in ACTIVE_MACHINES - seen_machines:
        logging.info("Removing machine_id='%s' from Prometheus ",inactive_machine)
        node_name = ""
        instanceid = ""
        instance_state = "not-created"
        if 'nodeRef' in machine['status'].keys():
            node_name = machine['status']['nodeRef']['name']
        if 'providerStatus' in machine['status'].keys():
            if 'instanceId' in machine['status']['providerStatus'].keys():
                instanceid = machine['status']['providerStatus']['instanceId']
            else:
                value = 0
            if 'instanceState' in machine['status']['providerStatus'].keys():
                instance_state = machine['status']['providerStatus']['instanceState']

        MACHINE_INFO.remove(
            machine_name          = machine['metadata']['name'],
            region                = machine['spec']['providerSpec']['value']['placement']['region'],
            availability_zone     = machine['spec']['providerSpec']['value']['placement']['availabilityZone'],
            instance_type         = machine['spec']['providerSpec']['value']['instanceType'],
            machine_creation_time = machine['metadata']['creationTimestamp'],
            image_id              = machine['spec']['providerSpec']['value']['ami']['id']
        )
        MACHINE_STATUS.remove(
            machine_name   = inactive_machine['metadata']['name'],
            node_name      = node_name,
            instance_state = instance_state,
            instance_id    = instanceid
        )
        ACTIVE_MACHINES.remove(inactive_machine)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(name)s:%(message)s')

    namespace = "openshift-machine-api"
    if "MACHINE_NAMESPACE" in os.environ:
        namespace = os.getenv("MACHINE_NAMESPACE")

    logging.info("Starting machinewatcher")
    incluster = config.load_incluster_config()
    k8s_cluster = client.api_client.ApiClient(incluster)
    dynclient = DynamicClient(k8s_cluster)

    start_http_server(8080)
    while True:
        collect(dynclient, namespace)
        time.sleep(30)
