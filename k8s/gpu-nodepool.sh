#!/bin/bash

# Azure CLI commands to set up the GPU-enabled AKS cluster for DealerFlow

RESOURCE_GROUP="dealerflow-rg"
CLUSTER_NAME="dealerflow-aks"

echo "Creating AKS Cluster (System Pool - CPU)..."
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $CLUSTER_NAME \
  --node-count 1 \
  --node-vm-size Standard_DS2_v2 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 3 \
  --generate-ssh-keys

echo "Adding GPU Nodepool (NC-Series T4)..."
# We taint this nodepool so standard pods don't schedule here.
# Only pods with the matching toleration will land on these expensive nodes.
az aks nodepool add \
  --resource-group $RESOURCE_GROUP \
  --cluster-name $CLUSTER_NAME \
  --name gpupool \
  --node-count 0 \
  --node-vm-size Standard_NC4as_T4_v3 \
  --enable-cluster-autoscaler \
  --min-count 0 \
  --max-count 5 \
  --node-taints sku=gpu:NoSchedule \
  --labels sku=gpu

echo "Connecting to Cluster..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $CLUSTER_NAME
