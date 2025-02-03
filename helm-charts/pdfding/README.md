# PdfDing Helm Chart for Kubernetes

## Before you begin

This [Helm](https://github.com/kubernetes/helm) chart supports installation of
[PdfDing](https://github.com/mrmn2/PdfDing) - A selfhosted PDF manager, viewer and editor offering
a seamless user experience on multiple devices.

The prerequisites for this Helm chart is a working **Kubernetes Cluster** and **Helm** installed.

If you don't have a Kubernetes Cluster, create one with [minikube](https://minikube.sigs.k8s.io/docs/start/).

To install Helm, see [Helm Installation guide](https://helm.sh/docs/intro/install/).

<br>

## Installation and Configuration

To add the PdfDing helm repository, run command:

```bash
helm repo add pdfding https://charts.pdfding.com
```

To install the PdfDing helm chart with a release name `my-release` in `ns` namespace, run command:

```bash
helm install -n ns --create-namespace my-release pdfding/pdfding
```

To update latest changes of the charts from the Helm repository, run commands:

```bash
helm repo update

helm -n ns upgrade my-release pdfding/pdfding

```

To configure the Helm chart deployment, the configurable parameters can be found in `values.yaml` values file.
Those parameters can be set via `--set` flag during installation or configured by editing the `values.yaml` directly.
An example configuration can be found in the file [values.demo.yaml](./values.demo.yaml), which contains the values used for
deploying PdfDing's demo instance.

To uninstall/delete the `my-release` deployment, run command:

```bash
helm delete my-release
```
