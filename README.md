# Managed Prometheus Exporter for Machine Objects

Purpose is a stopgap until [openshift/machine-api-operator](https://github.com/openshift/machine-api-operator) exports metrics we can alert on.  The one goal of this repo is to have a gauge on which SRE can create an alert to trigger when a node has not been created for some period of time.


## Exported Metrics

* `machine_api_status` is a Gauge that has two labels and a possibility one or two values. `0` for when there is no corresponding `Node`, `1` for when there is such a `Node`.
  * `machine_name` - Name of the `Machine` custom resource (CR)
  * `namespace` - Namespace in which `Machine` custom resource is defined
