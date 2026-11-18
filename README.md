# Flask + MongoDB on Kubernetes

## 1. Project overview

This assignment packages a small Flask JSON API backed by MongoDB. It runs locally with Docker Compose and on Minikube with an authenticated MongoDB StatefulSet, persistent storage, a Flask Deployment, internal and client-facing Services, and a CPU-based Horizontal Pod Autoscaler (HPA).

## 2. Problem statement

Provide a simple HTTP service that accepts and retrieves JSON documents, stores them durably in MongoDB, and demonstrates containerization and Kubernetes deployment fundamentals: service discovery, secrets, storage, resource sizing, metrics, and autoscaling configuration.

## 3. Architecture

```mermaid
flowchart TD
    Client[PowerShell or HTTP client] -->|HTTP :5000 / NodePort| FlaskSvc[Flask Kubernetes Service<br/>NodePort]
    FlaskSvc --> Flask[Flask Deployment<br/>2 to 5 replicas]
    Flask -->|mongodb:27017| MongoSvc[MongoDB Service<br/>ClusterIP]
    MongoSvc --> Mongo[MongoDB StatefulSet<br/>1 replica]
    Mongo --> PVC[PersistentVolumeClaim<br/>1 GiB]
    Secret[Kubernetes Secret<br/>credentials and URI] -. injected into .-> Flask
    Secret -. injected into .-> Mongo
    HPA[HPA<br/>CPU target 70%] -->|scales| Flask
    Metrics[Metrics Server] -->|pod CPU metrics| HPA
```

## 4. Technology stack

- Python, Flask, PyMongo, Gunicorn
- MongoDB 8, Docker, Docker Compose
- Kubernetes, Minikube, kubectl, Metrics Server
- pytest and mongomock

## 5. Project directory structure

```text
faralpha/
├── app/
│   ├── __init__.py                 # Application factory and environment configuration
│   ├── database.py                 # MongoClient setup and collection access
│   └── routes.py                   # GET /, GET /data, POST /data
├── tests/
│   └── test_app.py                 # Isolated API tests using mongomock
├── k8s/
│   ├── namespace.yaml
│   ├── mongodb-secret.example.yaml # Placeholder only; safe to submit
│   ├── mongodb-statefulset.yaml
│   ├── mongodb-service.yaml
│   ├── flask-deployment.yaml
│   ├── flask-service.yaml
│   └── flask-hpa.yaml
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── test.py                          # Manual 3,000-request GET load run
├── cputest.py                       # Manual 10,000-request GET load run
└── README.md
```

The real `k8s/mongodb-secret.yaml` is intentionally local-only and ignored by Git. Do not force-add it.

## 6. Prerequisites

- Windows PowerShell
- Python 3.12 or later
- Docker Desktop with Docker Compose
- Minikube and kubectl for Kubernetes deployment

## 7–10. Local environment, virtual environment, and dependencies

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that shell and activate again. The application reads process environment variables; it does not load `.env` automatically. `.env.example` contains only local defaults.

Configuration variables are `APP_HOST` (default `0.0.0.0`), `APP_PORT` (default `5000`), `MONGODB_URI` (default `mongodb://localhost:27017/`), and `MONGODB_DATABASE` (default `flask_assignment`).

## 11–12. Running Flask locally and starting MongoDB with Compose

The simplest local run starts both services:

```powershell
docker compose up --build
```

The Flask API is at `http://localhost:5000`; Compose connects to MongoDB at `mongodb://mongodb:27017/`. To run Flask on the host instead, start just MongoDB:

```powershell
docker compose up -d mongodb
$env:MONGODB_URI = "mongodb://localhost:27017/"
$env:MONGODB_DATABASE = "flask_assignment"
python -c 'from app import create_app; app = create_app(); app.run(host=app.config["HOST"], port=app.config["PORT"])'
```

Local Compose MongoDB has no authentication. Kubernetes MongoDB uses credentials injected from a Secret.

## 13. Testing GET and POST endpoints

`GET /` returns a timestamped welcome message. `POST /data` accepts a non-empty JSON object and returns its inserted identifier. `GET /data` lists stored documents, serializing MongoDB `_id` values as strings.

```powershell
curl.exe http://localhost:5000/
```

Example response (timestamp will vary):

```text
Welcome to the Flask app! The current time is: 2026-11-18T10:30:00+05:30
```

```powershell
curl.exe -X POST http://localhost:5000/data -H "Content-Type: application/json" -d '{"name":"Ada","role":"Engineer"}'
curl.exe http://localhost:5000/data
```

Example responses:

```json
{"inserted_id":"673abc1234567890abcdef12","status":"created"}
```

```json
[{"_id":"673abc1234567890abcdef12","name":"Ada","role":"Engineer"}]
```

Malformed JSON, non-object JSON, or an empty object returns `400`; a non-JSON content type returns `415`; database errors return `503`.

## 14. Docker image build

The Dockerfile installs `requirements.txt`, copies the Flask package, and starts Gunicorn on port 5000:

```powershell
docker build -t faralpha-flask-app:latest .
```

### Optional: push the image to a container registry

For a remote Kubernetes cluster, tag and push the image to a registry you control. This Docker Hub example keeps the username and tag in shell variables and lets `docker login` prompt for credentials; do not put passwords or tokens in commands or source files.

```powershell
$env:DOCKERHUB_USER = "YOUR_DOCKERHUB_USERNAME"
$env:IMAGE_TAG = "$($env:DOCKERHUB_USER)/faralpha-flask-app:v1"
docker login --username $env:DOCKERHUB_USER
docker build -t $env:IMAGE_TAG .
docker push $env:IMAGE_TAG
```

For deployment from that registry, change `image` in `k8s/flask-deployment.yaml` to the pushed image reference and set `imagePullPolicy: IfNotPresent`, then apply the Deployment manifest. A private registry also requires an image pull Secret. The default manifest remains configured for the already tested local Minikube image.

## 15–16. Minikube and image loading

Start Minikube if it is not already running, then build the image directly into its image store:

```powershell
minikube start
minikube image build -t faralpha-flask-app:latest .
```

The Deployment uses `faralpha-flask-app:latest` with `imagePullPolicy: IfNotPresent`, matching this local workflow.

## 17. Kubernetes namespace

```powershell
kubectl apply -f k8s/namespace.yaml
```

The namespace is `flask-assignment`.

## 18–19. MongoDB StatefulSet and authentication

Create a Secret in the namespace. Keep the real credentials local; the checked-in example contains placeholders only. Replace the sample values interactively in your own command, and URL-encode any reserved characters in the password used in the URI.

```powershell
kubectl create secret generic mongodb-secret -n flask-assignment `
  --from-literal=MONGO_INITDB_ROOT_USERNAME='YOUR_USERNAME' `
  --from-literal=MONGO_INITDB_ROOT_PASSWORD='YOUR_STRONG_PASSWORD' `
  --from-literal=MONGODB_URI='mongodb://YOUR_USERNAME:URL_ENCODED_PASSWORD@mongodb:27017/?authSource=admin'
```

MongoDB reads the root username and password from the Secret. Flask reads the URI from the same Secret; credentials are not embedded in the Deployment manifest or README.

Deploy its internal Service and StatefulSet:

```powershell
kubectl apply -f k8s/mongodb-service.yaml
kubectl apply -f k8s/mongodb-statefulset.yaml
kubectl rollout status statefulset/mongodb -n flask-assignment
```

The StatefulSet has one replica, resource requests of 200m CPU and 250M memory, and limits of 500m CPU and 500M memory, matching the assignment's sample resource values.

## 20. Persistent storage

The StatefulSet's `volumeClaimTemplates` creates a 1 GiB `ReadWriteOnce` PersistentVolumeClaim for `/data/db`. Kubernetes retains database files on the volume across MongoDB pod replacement. The claim is not removed by ordinary pod restarts. Avoid deleting PVCs if the stored data must be preserved.

## 21–22. Flask Deployment and Service

```powershell
kubectl apply -f k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-service.yaml
```

The Deployment requests 200m CPU and 250M memory per pod and limits each to 500m CPU and 500M memory. It starts with two replicas. Its NodePort Service exposes port 5000 to the Minikube host; MongoDB remains internal.

## 23. Port forwarding and local access

Use Minikube's service helper to get a reachable URL:

```powershell
minikube service flask-service -n flask-assignment --url
```

Alternatively, port-forward without changing the Service:

```powershell
kubectl port-forward -n flask-assignment service/flask-service 5000:5000
```

Then use `http://127.0.0.1:5000/` and `http://127.0.0.1:5000/data`.

## 24. Kubernetes DNS and service discovery

Flask connects to MongoDB through the Service address `mongodb:27017`. Since both workloads are in the `flask-assignment` namespace, CoreDNS resolves the short Service name `mongodb` to the ClusterIP assigned to the MongoDB Service. Its full DNS name is `mongodb.flask-assignment.svc.cluster.local`.

A Kubernetes Service provides a stable virtual address and DNS name while selecting the matching backend pods. Pod IPs can change when pods are replaced, so Flask uses the Service name rather than a pod IP. MongoDB uses a `ClusterIP` because only in-cluster clients need database access; it does not need public exposure. Flask is exposed separately through a NodePort Service for assignment access.

## 25. CPU and memory requests and limits

Requests reserve the baseline resources Kubernetes uses for scheduling. Limits cap container resource use. Flask's CPU request is also the denominator for the HPA's CPU utilization percentage, so it must be set for CPU utilization metrics to work. Both containers use the assignment's sample requests (200m CPU, 250M memory) and limits (500m CPU, 500M memory). Changing the Flask CPU request changes utilization percentages, so compare HPA readings only with the resource configuration active at the time of measurement.

## 26. Metrics Server

Enable the Minikube addon so the resource metrics API can report pod CPU and memory:

```powershell
minikube addons enable metrics-server
kubectl top pods -n flask-assignment
```

Metrics can take a short time to become available after enabling the addon or starting pods.

## 27. HPA configuration

Apply the autoscaler manifest:

```powershell
kubectl apply -f k8s/flask-hpa.yaml
kubectl get hpa -n flask-assignment
```

It targets Deployment `flask-app`, uses `autoscaling/v2`, requests an average CPU utilization target of 70%, and allows 2–5 replicas. The minimum is already two, so evidence of scale-up requires observing more than two replicas under sufficient sustained CPU load.

## 28. Load testing

Start the target API before running either script. `test.py` sends 3,000 GET requests with up to 50 workers. `cputest.py` sends 10,000 with up to 50 workers by default and accepts `LOAD_URL`, `TOTAL_REQUESTS`, and `WORKERS` environment variables. These scripts exercise HTTP success and are not a substitute for a controlled CPU stress workload.

## 29. Verification commands and observed results

Run the automated suite with `pytest -v` (or `python -m pytest -v`). The tests use an isolated `mongomock` client and do not require a live database.

```powershell
kubectl get deployments -n flask-assignment
kubectl get statefulsets -n flask-assignment
kubectl get pods -n flask-assignment
kubectl get services -n flask-assignment
kubectl get pvc -n flask-assignment
kubectl get hpa -n flask-assignment
kubectl top pods -n flask-assignment
```

Reported assignment checks: Flask Deployment 2/2 ready, MongoDB 1/1 running, GET `/` successful, and POST `/data` followed by GET `/data` readback successful. Load runs reported 3,000/3,000 successful requests and 10,000/10,000 successful requests. A prior load observation reached 57% CPU with the prior 100m Flask CPU request. The Flask request is now 200m to match the assignment sample; the earlier utilization percentage should not be treated as a measurement under this updated configuration. The HPA is configured and metrics were reported available; scale-up beyond two replicas remains unverified.

To make a sustained high-traffic attempt against Minikube, open one PowerShell window for load and another to watch scaling. Use the URL printed by `minikube service` (or a local port-forward). The larger request count is a test setting, not a reported result:

```powershell
$env:LOAD_URL = "http://127.0.0.1:5000/"
$env:TOTAL_REQUESTS = "1000000"
$env:WORKERS = "100"
python cputest.py
```

While it runs, observe metrics and replicas in the second window:

```powershell
kubectl get hpa flask-hpa -n flask-assignment --watch
kubectl get deployment flask-app -n flask-assignment --watch
```

Record the observed CPU, HPA current/desired replicas, and Deployment ready replicas. Stop the load script with `Ctrl+C` after collecting results. This endpoint is lightweight; if it does not drive Flask above 70%, report that honestly rather than claiming the HPA scaled. The earlier 57% run did not prove scale-up.

## 30. Troubleshooting

- **MongoDB connection errors:** Check `kubectl get pods,svc -n flask-assignment`, that the Secret keys exist, and that `MONGODB_URI` uses host `mongodb` and `authSource=admin`.
- **Pods stuck pending:** Check PVC status with `kubectl get pvc -n flask-assignment` and pod events with `kubectl describe pod`.
- **HPA shows unknown metrics:** Confirm Metrics Server is enabled and wait for metrics; check `kubectl top pods` and `kubectl describe hpa flask-hpa -n flask-assignment`.
- **ImagePullBackOff:** Confirm the image was built into the active Minikube profile with the exact tag `faralpha-flask-app:latest`.
- **Service URL unavailable:** Check `minikube status`, NodePort Service selectors, and Flask pod readiness.

## 31. Design decisions

- The Flask app factory isolates configuration and allows tests to inject mongomock.
- MongoDB access is centralized in `app/database.py`; routes do not embed connection strings.
- MongoDB is a StatefulSet with a claim template because it needs stable persistent storage.
- A ClusterIP Service gives database clients stable in-cluster discovery without public exposure.
- Secret values are passed at runtime; only a placeholder example is submitted.
- Flask CPU requests make HPA utilization calculations meaningful.

## 32. Limitations and future improvements

- Actual HPA scale-up above two replicas has not been verified; the reported 57% CPU was below target.
- The default image workflow targets local Minikube. Optional registry push instructions are provided for remote clusters, but the checked-in Deployment defaults to the Minikube-local image.
- Production deployment would need TLS/Ingress, health probes, resource tuning, secret management beyond a basic Kubernetes Secret, and operational monitoring.
- Local Compose MongoDB is intentionally unauthenticated and is for development only.

## GitHub submission commands

This workspace may need Git initialization. Review the staged file list before committing, and never force-add `k8s/mongodb-secret.yaml`.

```powershell
git init
git status --short
git add .
git status --short
git commit -m "Prepare Flask MongoDB Kubernetes assignment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If a secret file was already tracked in a repository, stop tracking it while retaining the local file with `git rm --cached k8s/mongodb-secret.yaml`, then commit that removal. This does not erase prior commits; credentials exposed in Git history require a separate approved response. No repository was created and no changes were pushed.
