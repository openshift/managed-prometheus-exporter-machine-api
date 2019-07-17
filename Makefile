SHELL := /bin/bash
include project.mk
include functions.mk

# Name of the exporter
EXPORTER_NAME := machine-api-status-exporter
# valid: deployment or daemonset
# currently unused
EXPORTER_TYPE := deployment

# All of the source files which compose the monitor. 
# Important note: No directory structure will be maintained
SOURCEFILES ?= monitor/main.py monitor/start.sh

# What to prefix the name of resources with?
NAME_PREFIX ?= sre-
SOURCE_CONFIGMAP_SUFFIX ?= -code
CREDENITALS_SUFFIX ?= -aws-credentials

MAIN_IMAGE_URI ?= quay.io/openshift-sre/managed-prometheus-exporter-base
IMAGE_VERSION ?= 0.1.3-5a0899dd
INIT_IMAGE_URI ?= quay.io/lseelye/yq-kubectl
INIT_IMAGE_VERSION ?= 1903.0.0

# Generate variables

MAIN_IMAGE ?= $(MAIN_IMAGE_URI):$(IMAGE_VERSION)
INIT_IMAGE ?= $(INIT_IMAGE_URI):$(INIT_IMAGE_VERSION)

PREFIXED_NAME ?= $(NAME_PREFIX)$(EXPORTER_NAME)

AWS_CREDENTIALS_SECRET_NAME ?= $(PREFIXED_NAME)$(CREDENITALS_SUFFIX)
SOURCE_CONFIGMAP_NAME ?= $(PREFIXED_NAME)$(SOURCE_CONFIGMAP_SUFFIX)
SERVICEACCOUNT_NAME ?= $(PREFIXED_NAME)

RESOURCELIST := servicemonitor/$(PREFIXED_NAME) service/$(PREFIXED_NAME) \
	deploymentconfig/$(PREFIXED_NAME) \
	configmap/$(SOURCE_CONFIGMAP_NAME) rolebinding/$(PREFIXED_NAME) \
	serviceaccount/$(SERVICEACCOUNT_NAME) clusterrole/sre-allow-read-cluster-setup \
	rolebinding/$(SERVICEACCOUNT_NAME)-read-cluster-setup 


all: deploy/010_serviceaccount-rolebinding.yaml deploy/025_sourcecode.yaml deploy/040_deployment.yaml deploy/050_service.yaml deploy/060_servicemonitor.yaml generate-syncset

deploy/010_serviceaccount-rolebinding.yaml: resources/010_serviceaccount-rolebinding.yaml.tmpl Makefile
	@$(call generate_file,010_serviceaccount-rolebinding)

deploy/025_sourcecode.yaml: $(SOURCEFILES) Makefile
	@for sfile in $(SOURCEFILES); do \
		files="--from-file=$$sfile $$files" ; \
	done ; \
	kubectl -n openshift-monitoring create configmap $(SOURCE_CONFIGMAP_NAME) --dry-run=true -o yaml $$files 1> deploy/025_sourcecode.yaml

deploy/040_deployment.yaml: resources/040_deployment.yaml.tmpl Makefile $(SOURCEFILES)
	@$(call generate_file,040_deployment)

deploy/050_service.yaml: resources/050_service.yaml.tmpl Makefile
	@$(call generate_file,050_service)

deploy/060_servicemonitor.yaml: resources/060_servicemonitor.yaml.tmpl Makefile
	@$(call generate_file,060_servicemonitor)

.PHONY: generate-syncset
generate-syncset:
	docker run --rm -v `pwd -P`:`pwd -P` python:2.7.15 /bin/sh -c "cd `pwd -P`; pip install pyyaml; scripts/generate_syncset.py -t ${SELECTOR_SYNC_SET_TEMPLATE_DIR} -y ${YAML_DIRECTORY} -d ${SELECTOR_SYNC_SET_DESTINATION} -r ${REPO_NAME}"

.PHONY: clean
clean:
	rm -f deploy/*.yaml

.PHONY: filelist
filelist: all
	@ls -1 deploy/*.y*ml

.PHONE: resourcelist
resourcelist:
	@echo $(RESOURCELIST)

.PHONY: vardump
vardump:
	@echo $(SOURCE_CODE_HASH)

.PHONY: uninstall
uninstall:
	oc delete -f deploy

.PHONY: install
install:
	oc apply -f deploy

