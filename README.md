# Managed Prometheus Exporter for Machine Objects

As a stopgap until [openshift/machine-api-operator](https://github.com/openshift/machine-api-operator) exports metrics, this will export a metrics.

## Exported Metrics

* `machine_api_status` is a Gauge that has four labels and a possibility one or two values. `0` for when there is no corresponding `Node`, `1` for when there is such a `Node`.
  * `machine_name` - Name of the `Machine` custom resource (CR)
  * `node_name` - `Node` name that corresponds to the `Machine` object, if the node exists (`""` otherwise)
  * `instance_state` - State reported by the `Machine` object of the cloud instance
  * `instance_id`- ID of the corresponding cloud instance, if one exists (`""` otherwise)
