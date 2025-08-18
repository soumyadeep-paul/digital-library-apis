# Digital Library API

This project is a Python-based backend for a community digital library. It allows users to add their books to a shared catalog, browse available books, and manage borrowing and returning books through a confirmation-based system. The API is built with FastAPI and uses MongoDB as its database.

## Features

- **User Management**: Simple user creation.
- **Book Catalog**: Add books via ISBN, which fetches book details automatically.
- **Browse Books**: List all available books with an optional search filter.
- **Lending Workflow**:
  - Users can request to reserve a book.
  - The book owner must confirm the reservation before the book is considered "borrowed".
  - The borrower can initiate a return.
  - The owner must confirm the return to make the book available again.

## Project Structure

```
.
├── digital_library/
│   ├── routers/
│   │   ├── books.py      # API endpoints for books
│   │   └── users.py      # API endpoints for users
│   ├── database.py     # MongoDB connection setup
│   ├── main.py         # FastAPI application entry point
│   └── models.py       # Pydantic models for data validation
├── docs/
│   └── api_and_schema.md # Detailed API and schema documentation
├── scripts/
│   └── populate_db.py  # Script to populate the DB with sample data
├── .env                # Environment variables (needs to be created)
├── requirements.txt    # Project dependencies
└── README.md           # This file
```

## Getting Started

### Prerequisites

- Python 3.7+
- MongoDB instance (running locally or on a cloud service)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd digital-library-api
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your environment:**
    - Create a `.env` file in the project root.
    - Add your MongoDB connection string to it:
      ```
      MONGO_DETAILS="mongodb://<user>:<password>@<host>:<port>"
      ```
      For a local instance, this might be `MONGO_DETAILS="mongodb://localhost:27017"`.

5.  **Populate the database with sample data (optional):**
    ```bash
    python scripts/populate_db.py
    ```

### Running the Application

There are multiple ways to run the application.

#### Using `uvicorn` (for development)

To run the API server directly, use `uvicorn`:

```bash
uvicorn digital_library.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

#### Using Docker Compose (recommended for local testing)

The included `docker-compose.yml` file makes it easy to start the application along with a MongoDB database.

1.  **Start the services:**
    ```bash
    docker-compose up --build
    ```

2.  The API will be available at `http://127.0.0.1:8000`. The MongoDB instance is also exposed on port `27017`.

#### Deploying to Kubernetes

1.  **Build and push your Docker image:**
    - First, you need to build the Docker image and push it to a registry that your Kubernetes cluster can access (e.g., Docker Hub, GCR, ECR).
    - Update the `image` field in `kubernetes/deployment.yaml` to point to your image.

2.  **Deploy the application:**
    ```bash
    kubectl apply -f kubernetes/deployment.yaml
    ```

3.  **Check the status:**
    ```bash
    kubectl get deployments
    kubectl get services
    ```
    The `digital-library-api-service` will show you the external IP or NodePort to access the application, depending on your cluster's configuration.

## API Documentation

Once the server is running, you can access the interactive API documentation (provided by Swagger UI) at `http://127.0.0.1:8000/docs`.

For a detailed description of the API endpoints and the database schema, please see `docs/api_and_schema.md`.

## How to Contribute

Contributions are welcome! Please feel free to open an issue or submit a pull request.