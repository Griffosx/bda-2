# Stage 1: Build the frontend
FROM node:20-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN if [ -f package-lock.json ]; then npm ci --frozen-lockfile; else npm install; fi

# Copy the rest of the frontend source code
COPY frontend/ ./

# Build the frontend for production
RUN npm run build

# Stage 2: Build the backend application
FROM python:3.12-slim AS backend

# Set working directory for backend
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the backend source code
# Ensure the 'src' directory is copied correctly
COPY src ./src

# Copy the built frontend assets from the builder stage
COPY --from=frontend-builder /app/frontend/dist /app/static

# Expose the port the app runs on (matching frontend fetch and Uvicorn command)
EXPOSE 8000

# Command to run the application using uvicorn
# Runs the FastAPI app defined in src/web.py
# Listens on all interfaces (0.0.0.0) on port 8000
CMD ["uvicorn", "src.web:app", "--host", "0.0.0.0", "--port", "8000"]