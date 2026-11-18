
# Flask API with MongoDB and Kubernetes

## About the Project

This project is a simple Flask REST API connected to MongoDB. It allows users to store and retrieve JSON data.

I built this project using Flask and PyMongo, then containerized it with Docker. I also deployed it on a local Kubernetes cluster using Minikube.

The API has three endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Returns a welcome message |
| POST | `/data` | Saves a JSON document in MongoDB |
| GET | `/data` | Retrieves saved documents |

## Tech Stack

- Python and Flask
- MongoDB and PyMongo
- Docker and Docker Compose
- Kubernetes and Minikube
- Gunicorn
- pytest and mongomock

## Project Structure

```text
faralpha/
├── app/
│   ├── __init__.py
│   ├── database.py
│   └── routes.py
├── tests/
│   └── test_app.py
├── k8s/
│   ├── namespace.yaml
│   ├── mongodb-secret.example.yaml
│   ├── mongodb-service.yaml
│   ├── mongodb-statefulset.yaml
│   ├── flask-deployment.yaml
│   ├── flask-service.yaml
│   └── flask-hpa.yaml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── test.py
├── cputest.py
└── README.md
```

## How It Works

I separated the application into three main parts:

- `app/__init__.py`: Creates and configures the Flask application.
- `app/routes.py`: Contains the API endpoints.
- `app/database.py`: Handles the MongoDB connection.

The MongoDB connection string and database name are read from environment variables.

For local development, Docker Compose starts both Flask and MongoDB. For Kubernetes, MongoDB runs as a StatefulSet with persistent storage, while Flask runs as a Deployment.

Flask connects to MongoDB through the Kubernetes Service name `mongodb:27017`. MongoDB is exposed internally through a ClusterIP Service, while Flask is accessible through a NodePort Service.

## Run Locally Using Docker Compose

### Requirements

- Python 3.12 or later
- Docker Desktop
- Docker Compose

Clone the repository and open its directory.

Start the application:

```powershell
docker compose up --build
```

This starts both Flask and MongoDB.

The API will be available at:

```text
http://localhost:5000
```

## Test the API

### 1. Check the welcome endpoint

```powershell
curl.exe http://localhost:5000/
```

### 2. Insert data

```powershell
curl.exe -X POST http://localhost:5000/data -H "Content-Type: application/json" -d '{"name":"Ada","role":"Engineer"}'
```

Expected response:

```json
{
  "inserted_id": "673abc1234567890abcdef12",
  "status": "created"
}
```

### 3. Retrieve data

```powershell
curl.exe http://localhost:5000/data
```

The response should contain the document that was just inserted.

## Run Automated Tests

Create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the test suite:

```powershell
python -m pytest -v
```

The tests use `mongomock`, so a running MongoDB server is not required for the automated tests.

**Test result:** 11 tests passed.

## Docker Image

Build the Flask Docker image:

```powershell
docker build -t faralpha-flask-app:latest .
```

The Dockerfile uses Gunicorn to run the Flask application.

## Deploy on Kubernetes Using Minikube

### 1. Start Minikube

```powershell
minikube start --driver=docker
```

### 2. Build and load the Flask image

```powershell
docker build -t faralpha-flask-app:latest .
minikube image load faralpha-flask-app:latest
```

### 3. Create the namespace

```powershell
kubectl apply -f k8s/namespace.yaml
```

### 4. Create the MongoDB Secret

Replace the example username and password with your own credentials.

```powershell
kubectl create secret generic mongodb-secret -n flask-assignment `
  --from-literal=MONGO_INITDB_ROOT_USERNAME='YOUR_USERNAME' `
  --from-literal=MONGO_INITDB_ROOT_PASSWORD='YOUR_PASSWORD' `
  --from-literal=MONGODB_URI='mongodb://YOUR_USERNAME:URL_ENCODED_PASSWORD@mongodb:27017/?authSource=admin'
```

The actual Secret file is not included in the repository. Only the example file with placeholders is provided.

### 5. Deploy MongoDB

```powershell
kubectl apply -f k8s/mongodb-service.yaml
kubectl apply -f k8s/mongodb-statefulset.yaml
```

Wait for MongoDB to start:

```powershell
kubectl rollout status statefulset/mongodb -n flask-assignment
```

### 6. Deploy Flask

```powershell
kubectl apply -f k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-service.yaml
```

Check the deployment:

```powershell
kubectl get pods -n flask-assignment
```

The Flask Deployment starts with two replicas.

### 7. Access the Flask API

Run port forwarding:

```powershell
kubectl port-forward service/flask-service 5000:5000 -n flask-assignment
```

Now access the API at:

```text
http://127.0.0.1:5000
```

You can test the same GET and POST endpoints using the commands shown earlier.

## Kubernetes Configuration

The Kubernetes setup includes:

- **Flask Deployment:** Starts with two replicas.
- **Flask Service:** Exposes the API through NodePort.
- **MongoDB StatefulSet:** Runs MongoDB with persistent storage.
- **MongoDB Service:** Provides internal access to MongoDB.
- **PersistentVolumeClaim:** Provides 1 GiB of storage for MongoDB data.
- **Kubernetes Secret:** Stores MongoDB credentials and connection URI.
- **HPA:** Configured to scale Flask between 2 and 5 replicas based on CPU utilization.

### Resource Requests and Limits

| Resource | CPU | Memory |
|---|---:|---:|
| Request | 200m | 250M |
| Limit | 500m | 500M |

These values are configured for both Flask and MongoDB containers.

## Kubernetes DNS

Flask connects to MongoDB using:

```text
mongodb:27017
```

Both services are deployed in the `flask-assignment` namespace. Kubernetes DNS resolves `mongodb` to the MongoDB Service IP.

This allows Flask to connect to MongoDB without depending on the MongoDB pod's IP address.

## HPA and Load Testing

Enable Metrics Server:

```powershell
minikube addons enable metrics-server
```

Apply the HPA configuration:

```powershell
kubectl apply -f k8s/flask-hpa.yaml
```

Check HPA status:

```powershell
kubectl get hpa -n flask-assignment
kubectl top pods -n flask-assignment
```

The screenshot below records the observed HPA metrics and pod status. It shows two Flask replicas ready and current CPU utilization below the 70% target; it does not demonstrate scale-up.

![HPA status, running pods, and CPU metrics](Screenshot%202026-11-18%20154918.png)

The HPA is configured with:
- CPU utilization target: 70%
- Minimum replicas: 2
- Maximum replicas: 5

### Load Testing

I used two Python scripts to send concurrent GET requests:

- `test.py`: Sends 3,000 requests.
- `cputest.py`: Sends 10,000 requests by default.

To run the configurable load test:

```powershell
$env:LOAD_URL = "http://127.0.0.1:5000/"
$env:TOTAL_REQUESTS = "10000"
$env:WORKERS = "50"
python cputest.py
```

In another terminal, monitor the HPA:

```powershell
kubectl get hpa flask-hpa -n flask-assignment --watch
```

The captured 3,000-request run completed with 2,951 successful and 49 failed requests. The captured 10,000-request run completed with 10,000 successful and 0 failed requests.

![Load test results for 3,000 and 10,000 requests](Screenshot%202026-11-18%20155758.png)

The HPA configuration and metrics were verified. However, scaling beyond the initial two Flask replicas was not observed during my tests.

## Verify Kubernetes Resources

These commands can be used to check the deployed resources:

```powershell
kubectl get deployments -n flask-assignment
kubectl get statefulsets -n flask-assignment
kubectl get pods -n flask-assignment
kubectl get services -n flask-assignment
kubectl get pvc -n flask-assignment
kubectl get hpa -n flask-assignment
```

## Notes

- MongoDB authentication is enabled in Kubernetes.
- Local Docker Compose MongoDB is unauthenticated and intended for development.
- Real MongoDB credentials should be kept out of the repository.
- HPA scale-up beyond two replicas has not been verified.
