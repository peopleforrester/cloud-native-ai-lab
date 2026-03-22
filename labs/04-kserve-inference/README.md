# Lab 04: KServe Inference

## What you'll learn

- How to deploy a machine learning model on Kubernetes using KServe
- The InferenceService custom resource definition (CRD) and its lifecycle
- Autoscaling behavior: automatic scale-up under load and scale-to-zero when idle
- How KServe builds on Knative Serving for serverless model inference

## Prerequisites

- Lab 00 completed (kind cluster running with kubectl configured)
- `curl` available on your machine

## Background

If you already know Kubernetes Ingress or Gateway API, KServe will feel familiar.
An Ingress controller accepts HTTP traffic and routes it to backend Services.
KServe does the same thing, but the "backends" are ML models instead of
microservices. You define an **InferenceService** resource, KServe provisions the
serving container, wires up the networking, and manages the lifecycle — including
autoscaling.

KServe runs in **serverless mode** on top of Knative Serving. Knative gives you
request-driven autoscaling (the Knative Pod Autoscaler, or KPA) and
scale-to-zero. When no requests arrive for a configurable window (default: 60
seconds), Knative scales the model pod down to zero replicas. The next request
triggers a cold start — Knative spins up a pod, loads the model, and serves the
prediction. This is the same scale-to-zero pattern that powers serverless
platforms like AWS Lambda, but it runs on your own cluster.

Under the hood, KServe supports multiple ML frameworks: scikit-learn, XGBoost,
TensorFlow, PyTorch, Triton, and custom containers. Each framework has a
pre-built serving image that knows how to load models from a storage URI (an S3
bucket, GCS path, PVC, or HTTP URL). In this lab we use scikit-learn with KServe's
official example iris classifier — a tiny model that runs on CPU. No GPU needed.

KServe also defines an **LLMInferenceService** CRD specifically for large
language models, which handles concerns like tensor parallelism, continuous
batching, and model sharding across multiple GPUs. We won't exercise that CRD in
this lab, but it is worth knowing it exists as you move toward production LLM
serving.

## Exercise

### Step 1: Install KServe in serverless mode

KServe requires Knative Serving and a networking layer. Install them in order.

First, install the Knative Serving CRDs and core components:

```bash
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.17.0/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.17.0/serving-core.yaml
```

Install the Knative networking layer (Kourier — lightweight, good for kind):

```bash
kubectl apply -f https://github.com/knative/net-kourier/releases/download/knative-v1.17.0/kourier.yaml
```

Configure Knative to use Kourier:

```bash
kubectl patch configmap/config-network \
  --namespace knative-serving \
  --type merge \
  --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
```

Wait for Knative components to be ready:

```bash
kubectl wait --for=condition=Available deployment --all \
  -n knative-serving --timeout=120s
```

Now install KServe (CRDs first, then the controller):

```bash
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve.yaml
kubectl apply -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve-cluster-resources.yaml
```

Wait for KServe to be ready:

```bash
kubectl wait --for=condition=Available deployment/kserve-controller-manager \
  -n kserve --timeout=120s
```

### Step 2: Create a namespace for inference workloads

```bash
kubectl create namespace inference
```

### Step 3: Deploy the sklearn InferenceService

Apply the InferenceService manifest:

```bash
kubectl apply -f manifests/inference-service.yaml
```

### Step 4: Wait for the service to become ready

Watch the InferenceService status until it shows `READY = True`:

```bash
kubectl get inferenceservice -n inference --watch
```

This may take 1-3 minutes on kind while the container image is pulled. Press
Ctrl+C once you see `READY = True`.

You can also check the underlying Knative revision:

```bash
kubectl get revisions -n inference
```

### Step 5: Send a prediction request

Determine the ingress endpoint. On kind, Kourier's service is a ClusterIP by
default, so we port-forward:

```bash
kubectl port-forward -n kourier-system service/kourier 8080:80 &
PF_PID=$!
```

Get the host header for your InferenceService:

```bash
SERVICE_HOSTNAME=$(kubectl get inferenceservice sklearn-iris -n inference \
  -o jsonpath='{.status.url}' | sed 's|http://||')
echo "Host: ${SERVICE_HOSTNAME}"
```

Send a prediction request with sample iris data (sepal length, sepal width,
petal length, petal width):

```bash
curl -H "Host: ${SERVICE_HOSTNAME}" \
  http://localhost:8080/v1/models/sklearn-iris:predict \
  -d '{"instances": [[6.8, 2.8, 4.8, 1.4], [6.0, 3.4, 4.5, 1.6]]}'
```

You should see a JSON response with predictions like:

```json
{"predictions": [1, 1]}
```

The values (0, 1, or 2) correspond to iris species: setosa, versicolor, or
virginica.

Stop the port-forward:

```bash
kill $PF_PID
```

### Step 6: Observe scale-to-zero behavior

Watch the pods in the inference namespace:

```bash
kubectl get pods -n inference --watch
```

After approximately 60 seconds of no traffic, you will see the model pod
terminate (scale-to-zero). When you send another prediction request, a new pod
will spin up automatically.

> **Note on kind:** Scale-to-zero may take longer than 60 seconds on kind due to
> resource constraints. Knative's default scale-down window is 60 seconds, but
> the actual termination depends on the KPA polling interval. Be patient — it
> will happen.

To test scale-up, restart the port-forward and send another request:

```bash
kubectl port-forward -n kourier-system service/kourier 8080:80 &
PF_PID=$!
sleep 2

curl -H "Host: ${SERVICE_HOSTNAME}" \
  http://localhost:8080/v1/models/sklearn-iris:predict \
  -d '{"instances": [[5.1, 3.5, 1.4, 0.2]]}'

kill $PF_PID
```

Watch the pods again — you should see a new pod created to serve the request.

## Verify it worked

Run these checks to confirm everything is functioning:

```bash
# InferenceService should show READY = True
kubectl get inferenceservice -n inference

# The URL field should be populated
kubectl get inferenceservice sklearn-iris -n inference \
  -o jsonpath='{.status.url}'
echo

# Knative revision should exist
kubectl get revisions -n inference
```

## What just happened?

You deployed a machine learning model to Kubernetes without writing any serving
code. Here is what KServe did for you:

1. **Created a Knative Service** — KServe translated the InferenceService spec
   into a Knative Service, which manages revisions and traffic routing.

2. **Pulled the model server image** — KServe selected the sklearn server image
   based on the `sklearn` predictor type in the spec.

3. **Loaded the model from storage** — The sklearn server container downloaded
   the serialized model from the `storageUri` (a GCS bucket in this case,
   accessible without credentials because it is a public KServe example).

4. **Set up autoscaling** — Knative's KPA monitors request concurrency and
   scales the deployment between 0 and N replicas automatically.

5. **Configured networking** — Kourier (the Knative ingress) routes traffic to
   the correct revision based on the Host header.

This is the same pattern used in production, but at production scale you would
use a real ingress (like Istio or Envoy Gateway), connect to private model
registries, add authentication, and configure resource limits.

## Clean up

Remove the resources in reverse order:

```bash
# Delete the InferenceService
kubectl delete -f manifests/inference-service.yaml

# Delete the inference namespace
kubectl delete namespace inference

# Remove KServe
kubectl delete -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve-cluster-resources.yaml
kubectl delete -f https://github.com/kserve/kserve/releases/download/v0.14.1/kserve.yaml

# Remove Knative networking (Kourier)
kubectl delete -f https://github.com/knative/net-kourier/releases/download/knative-v1.17.0/kourier.yaml

# Remove Knative Serving
kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.17.0/serving-core.yaml
kubectl delete -f https://github.com/knative/serving/releases/download/knative-v1.17.0/serving-crds.yaml
```

## Next step

Continue to [Lab 05: Gateway API Inference Routing](../05-gateway-routing/).
