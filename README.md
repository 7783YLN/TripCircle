# Flask Application Deployment with Docker

This repository contains all necessary files to deploy a Flask web application using Docker and Docker Compose.

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- Git (optional, for version control)

## Project Structure

```
.
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose orchestration
├── requirements.txt        # Python dependencies
├── app.py                  # Flask application (your main file)
├── build.sh               # Script to build Docker image
├── run.sh                 # Script to run the application
├── push.sh                # Script to push image to cloud registry
└── .env                   # Environment variables (create this file)
```

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the project root directory with your database credentials (if applicable):

```env
# Database Configuration (example)
DB_HOST=your_database_host
DB_PORT=5432
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name

# Application Configuration
FLASK_ENV=production
FLASK_APP=app.py
```

**Important:** Never commit the `.env` file to version control. Add it to `.gitignore`.

### 2. Ensure app.py Binds to Correct Host and Port

Make sure your `app.py` file includes the following at the end:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500, debug=False)
```

**Note:** Use `0.0.0.0` instead of `127.0.0.1` to allow external connections within Docker.

### 3. Make Shell Scripts Executable

On Linux/Mac or Windows with WSL/Git Bash:

```bash
chmod +x build.sh run.sh push.sh
```

## Usage

### Building the Docker Image

Run the build script:

```bash
./build.sh
```

Or manually:

```bash
docker build -t tripcircle:latest .
```

### Running the Application

Run the application using Docker Compose:

```bash
./run.sh
```

Or manually:

```bash
docker compose up -d
```

The application will be accessible at: `http://localhost:5500`

### Viewing Logs

```bash
docker compose logs -f app
```

### Stopping the Application

```bash
docker compose down
```

### Pushing to Cloud Registry

Before pushing, configure your cloud registry credentials:

**For Docker Hub:**
```bash
docker login
```

**For AWS ECR:**
```bash
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
```

**For Google Container Registry (GCR):**
```bash
gcloud auth configure-docker
```

Then run the push script:

```bash
./push.sh
```

**Note:** Edit `push.sh` to specify your registry URL and repository name.

## Deployment to Cloud

### AWS (ECS/EC2)

1. Push the image to Amazon ECR
2. Create an ECS task definition using the image
3. Deploy to ECS cluster or EC2 instance
4. Configure security groups to allow traffic on port 5500

### Google Cloud Platform (GCP)

1. Push the image to Google Container Registry
2. Deploy to Cloud Run or GKE
3. Configure firewall rules for port 5500

### Azure

1. Push the image to Azure Container Registry
2. Deploy to Azure Container Instances or AKS
3. Configure network security groups

## Troubleshooting

### ERR_EMPTY_RESPONSE

If you encounter this error:
- Ensure `app.py` binds to `0.0.0.0` instead of `127.0.0.1`
- Check that port 5500 is properly exposed in Dockerfile
- Verify port mapping in docker-compose.yml

### Container Exits Immediately

Check logs:
```bash
docker compose logs app
```

Common issues:
- Missing dependencies in requirements.txt
- Syntax errors in app.py
- Missing environment variables

### Database Connection Issues

- Verify database credentials in `.env` file
- Ensure database service is running and accessible
- Check network connectivity between containers

## Production Considerations

### Using Gunicorn (Recommended for Production)

1. Add `gunicorn` to `requirements.txt`:
```
Flask
Flask-Cors
python-dateutil
gunicorn
```

2. Update Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5500", "app:app"]
```

### Security Best Practices

- Use Docker secrets for sensitive data in production
- Run containers as non-root user
- Regularly update base images and dependencies
- Use HTTPS/TLS for production deployments
- Implement proper logging and monitoring

## License

[Your License Here]

## Support

For issues and questions, please contact your DevOps team.
