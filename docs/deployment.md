
# Deployment Guide

This guide covers deploying PyCommerce to various production environments.

## Deployment Options

### 1. Replit (Recommended for Quick Start)
### 2. Docker Container
### 3. Traditional Server (VPS/Dedicated)
### 4. Cloud Platforms (AWS, GCP, Azure)

## Replit Deployment

PyCommerce is optimized for deployment on Replit with minimal configuration.

### Steps

1. **Fork Repository**
   - Go to [Replit](https://replit.com)
   - Click "Create Repl" → "Import from GitHub"
   - Enter: `https://github.com/your-username/pycommerce`

2. **Configure Secrets**
   In Replit's Secrets tab, add:
   ```
   DATABASE_URL=postgresql://user:pass@host:port/db
   SECRET_KEY=your-secret-key
   STRIPE_SECRET_KEY=sk_test_... (optional)
   OPENAI_API_KEY=sk-... (optional)
   ```

3. **Database Setup**
   - Use Replit's PostgreSQL database or external provider
   - Update `DATABASE_URL` in secrets

4. **Deploy**
   - Click the "Run" button
   - Your app will be live at `https://your-repl-name.username.repl.co`

### Replit Configuration

The `.replit` file is already configured:
```toml
run = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"

[deployment]
run = ["sh", "-c", "gunicorn --bind 0.0.0.0:5000 main:app"]
```

## Docker Deployment

### Dockerfile

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/pycommerce
      - SECRET_KEY=your-secret-key
      - DEBUG=False
    depends_on:
      - db
    volumes:
      - ./static/media:/app/static/media
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=pycommerce
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

### Deployment Commands

```bash
# Build and start services
docker-compose up -d

# Initialize database
docker-compose exec app python initialize_db.py

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Traditional Server Deployment

### Requirements

- Ubuntu 20.04+ or CentOS 8+
- Python 3.11+
- PostgreSQL 12+
- Nginx (reverse proxy)
- SSL certificate

### Installation Steps

1. **Update System**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Dependencies**
   ```bash
   sudo apt install -y python3.11 python3.11-venv python3.11-dev \
     postgresql postgresql-contrib nginx git curl
   ```

3. **Create Application User**
   ```bash
   sudo useradd --system --shell /bin/bash --home /opt/pycommerce pycommerce
   sudo mkdir -p /opt/pycommerce
   sudo chown pycommerce:pycommerce /opt/pycommerce
   ```

4. **Deploy Application**
   ```bash
   sudo -u pycommerce bash
   cd /opt/pycommerce
   git clone https://github.com/your-username/pycommerce.git .
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure Database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE pycommerce;
   CREATE USER pycommerce WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE pycommerce TO pycommerce;
   \q
   ```

6. **Environment Configuration**
   ```bash
   sudo -u pycommerce tee /opt/pycommerce/.env << EOF
   DATABASE_URL=postgresql://pycommerce:secure_password@localhost:5432/pycommerce
   SECRET_KEY=$(openssl rand -base64 32)
   DEBUG=False
   HOST=127.0.0.1
   PORT=5000
   EOF
   ```

7. **Initialize Database**
   ```bash
   sudo -u pycommerce bash
   cd /opt/pycommerce
   source venv/bin/activate
   python initialize_db.py
   ```

### Systemd Service

Create `/etc/systemd/system/pycommerce.service`:
```ini
[Unit]
Description=PyCommerce E-commerce Platform
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=pycommerce
Group=pycommerce
WorkingDirectory=/opt/pycommerce
Environment=PATH=/opt/pycommerce/venv/bin
EnvironmentFile=/opt/pycommerce/.env
ExecStart=/opt/pycommerce/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 main:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pycommerce
sudo systemctl start pycommerce
sudo systemctl status pycommerce
```

### Nginx Configuration

Create `/etc/nginx/sites-available/pycommerce`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Proxy to application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Static files
    location /static/ {
        alias /opt/pycommerce/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/pycommerce/static/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Security - block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(env|ini|py)$ {
        deny all;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/pycommerce /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Cloud Platform Deployment

### AWS Deployment

#### Using AWS App Runner

1. **Create `apprunner.yaml`**
   ```yaml
   version: 1.0
   runtime: python3
   build:
     commands:
       build:
         - pip install -r requirements.txt
   run:
     runtime-version: 3.11
     command: gunicorn --bind 0.0.0.0:8000 main:app
     network:
       port: 8000
       env: PORT
   env:
     - name: DATABASE_URL
       value: "postgresql://user:pass@rds-endpoint:5432/db"
     - name: SECRET_KEY
       value: "your-secret-key"
   ```

2. **Deploy**
   - Go to AWS App Runner console
   - Create service from source code
   - Connect GitHub repository
   - Configure auto-deployment

#### Using ECS with Fargate

Create `task-definition.json`:
```json
{
  "family": "pycommerce",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "pycommerce",
      "image": "your-account.dkr.ecr.region.amazonaws.com/pycommerce:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/db"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/pycommerce",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### Using Cloud Run

1. **Create `cloudbuild.yaml`**
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/pycommerce', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/pycommerce']
   ```

2. **Deploy**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   gcloud run deploy pycommerce \
     --image gcr.io/PROJECT_ID/pycommerce \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name pycommerce \
  --image your-registry.azurecr.io/pycommerce:latest \
  --dns-name-label pycommerce-app \
  --ports 5000 \
  --environment-variables \
    DATABASE_URL="postgresql://user:pass@server:5432/db" \
    SECRET_KEY="your-secret-key"
```

## Database Deployment

### Managed Database Services

#### AWS RDS
- PostgreSQL 15
- Multi-AZ deployment for high availability
- Automated backups
- Read replicas for scaling

#### Google Cloud SQL
- PostgreSQL 15
- High availability configuration
- Automated backups and point-in-time recovery

#### Azure Database for PostgreSQL
- Flexible server deployment
- High availability options
- Automated patching and backups

### Self-Managed Database

#### PostgreSQL Configuration

`/etc/postgresql/15/main/postgresql.conf`:
```
# Performance tuning
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Logging
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_statement = 'ddl'

# Replication (if needed)
wal_level = replica
max_wal_senders = 3
```

#### Backup Strategy

```bash
#!/bin/bash
# Daily backup script
DB_NAME="pycommerce"
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump $DB_NAME | gzip > $BACKUP_DIR/pycommerce_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "pycommerce_*.sql.gz" -mtime +7 -delete
```

## Monitoring and Logging

### Application Monitoring

#### Health Checks
```python
# Add to main.py
@app.route('/health')
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0"
    }
```

#### Metrics Collection
```python
# Using Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(time.time() - g.start_time)
    return response
```

### Logging Configuration

`logging.conf`:
```ini
[loggers]
keys=root,pycommerce

[handlers]
keys=console,file

[formatters]
keys=standard

[logger_root]
level=INFO
handlers=console,file

[logger_pycommerce]
level=INFO
handlers=console,file
qualname=pycommerce
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=standard
args=(sys.stdout,)

[handler_file]
class=FileHandler
level=INFO
formatter=standard
args=('/var/log/pycommerce/app.log',)

[formatter_standard]
format=%(asctime)s [%(levelname)s] %(name)s: %(message)s
```

## Security Considerations

### Environment Variables
- Never commit secrets to version control
- Use environment-specific configurations
- Rotate secrets regularly

### Database Security
- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular security updates

### Application Security
- Enable HTTPS only
- Set security headers
- Input validation and sanitization
- Regular dependency updates

### Firewall Configuration
```bash
# UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Performance Optimization

### Application Level
- Enable caching (Redis)
- Database query optimization
- Static file serving via CDN
- Image optimization

### Infrastructure Level
- Load balancing
- Auto-scaling
- Database read replicas
- CDN integration

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
sudo journalctl -u pycommerce -f

# Check database connection
python -c "from pycommerce.core.db import db; print('DB OK')"
```

#### High Memory Usage
```bash
# Check memory usage
htop

# Optimize gunicorn workers
# Calculate: (2 x CPU cores) + 1
```

#### Database Connection Issues
```bash
# Test connection
psql -h hostname -U username -d database_name

# Check connection pool
# Monitor active connections
```

For additional help, see the [troubleshooting guide](troubleshooting.md) or open an issue on GitHub.
