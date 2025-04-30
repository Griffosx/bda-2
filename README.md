# Dice Roller Application

This is a full-stack application that provides a dice rolling service with statistical analysis capabilities. The application consists of a FastAPI backend and a javascript (react) frontend, containerized using Docker.

## Architecture

The application uses a multi-stage Docker build process to create an optimized production image:

1. **Frontend Stage**: Builds the javascript (react) frontend application
2. **Backend Stage**: Sets up the Python FastAPI backend and combines it with the built frontend

## Docker Deployment

### Building the Image

To build the Docker image, run the following command from the project root:

```bash
docker build -t dice-roller .
```

### Running Locally

Once the image is built, you can run the container with:

```bash
docker run -p 8000:8000 dice-roller
```

The application will be available at `http://localhost:8000`

### DockerHub Instructions

To pull and run the image from DockerHub:

```bash
docker pull griffosx/dice-roller:latest
docker run -p 8000:8000 griffosx/dice-roller:latest
```

## Dockerfile Structure

The Dockerfile uses a multi-stage build process to optimize the final image size:

### Stage 1: Frontend Builder

```dockerfile
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --frozen-lockfile; else npm install; fi
COPY frontend/ ./
RUN npm run build
```

### Stage 2: Backend Application

```dockerfile
FROM python:3.12-slim AS backend
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY --from=frontend-builder /app/frontend/dist /app/static
EXPOSE 8000
CMD ["uvicorn", "src.web:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Application Features

- Dice rolling with support for various dice types (e.g., d6, d20)
- Statistical analysis of dice rolls
- RESTful API endpoints:
  - `GET /`: Serves the frontend application
  - `POST /prompt`: Handles dice roll commands and statistical analysis

## API Endpoints

### Frontend

- `GET /`: Serves the main frontend application
- `GET /assets/*`: Serves static assets (JS, CSS, etc.)

### Backend

- `POST /prompt`: Accepts dice commands and returns results
  - Example commands:
    - `roll 1d6` or simply `r 1d6`: Roll a single six-sided die
    - `stats 10 2d8+1` or simply `s 10 2s8+1`: Calculate statistics for 10 rolls of 2d8+1

## Development

For local development without Docker:

1. Frontend:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. Backend:

   ```bash
   pip install -r requirements.txt
   ```

   You can use the provided Makefile commands for common development tasks:

   ```bash
   # Run the development server
   make dev

   # Run tests
   make test

   # Run tests with coverage report
   make test-cov
   ```

   Alternatively, you can run the development server directly:

   ```bash
   uvicorn src.web:app --reload
   ```

## Notes

- The application uses Python 3.12 for the backend
- Node.js 20 (Alpine) is used for the frontend build
- The application runs on port 8000 by default
- CORS is enabled for all origins in development
- Static files are served from the `/app/static` directory in the container
