
# Installation Guide

This guide will help you install and set up PyCommerce for development or production use.

## Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Database**: PostgreSQL 12+ (recommended) or SQLite for development
- **Memory**: Minimum 2GB RAM (4GB+ recommended for production)
- **Storage**: 1GB+ available space

### Required Tools
- Git
- pip (Python package installer)
- PostgreSQL client (if using PostgreSQL)

## Installation Methods

### Method 1: Standard Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/pycommerce.git
   cd pycommerce
   ```

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**
   Create a `.env` file in the project root:
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://username:password@localhost:5432/pycommerce
   
   # Security
   SECRET_KEY=your-super-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key
   
   # Optional: Payment Processors
   STRIPE_SECRET_KEY=sk_test_your_stripe_key
   STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_key
   PAYPAL_CLIENT_ID=your_paypal_client_id
   PAYPAL_CLIENT_SECRET=your_paypal_secret
   
   # Optional: AI Services
   OPENAI_API_KEY=sk-your-openai-key
   GOOGLE_AI_API_KEY=your-google-ai-key
   ```

4. **Initialize Database**
   ```bash
   python initialize_db.py
   ```

5. **Start the Application**
   ```bash
   python main.py
   ```

### Method 2: Docker Installation

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-username/pycommerce.git
   cd pycommerce
   ```

2. **Build Docker Image**
   ```bash
   docker build -t pycommerce .
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Method 3: Replit Deployment

1. **Fork on Replit**
   - Go to [Replit](https://replit.com)
   - Import from GitHub: `https://github.com/your-username/pycommerce`

2. **Configure Environment**
   - Add secrets in Replit's Secrets tab
   - Set `DATABASE_URL`, `SECRET_KEY`, etc.

3. **Run**
   - Click the "Run" button
   - PyCommerce will be available at your Replit URL

## Database Setup

### PostgreSQL (Recommended)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # macOS (with Homebrew)
   brew install postgresql
   brew services start postgresql
   
   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. **Create Database and User**
   ```sql
   sudo -u postgres psql
   
   CREATE DATABASE pycommerce;
   CREATE USER pycommerce_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE pycommerce TO pycommerce_user;
   \q
   ```

3. **Update Environment Variables**
   ```bash
   DATABASE_URL=postgresql://pycommerce_user:your_password@localhost:5432/pycommerce
   ```

### SQLite (Development Only)

For development, you can use SQLite:
```bash
DATABASE_URL=sqlite:///pycommerce.db
```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@localhost:5432/db` |
| `SECRET_KEY` | Flask secret key | `your-secret-key-here` |
| `JWT_SECRET_KEY` | JWT token signing key | `your-jwt-secret` |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `False` |
| `HOST` | Application host | `0.0.0.0` |
| `PORT` | Application port | `5000` |
| `WORKERS` | Number of worker processes | `4` |

### Payment Processor Configuration

#### Stripe
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...  # Optional
```

#### PayPal
```bash
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
PAYPAL_MODE=sandbox  # or 'live' for production
```

### AI Service Configuration

#### OpenAI
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-3.5-turbo
```

#### Google AI
```bash
GOOGLE_AI_API_KEY=your_key
GOOGLE_AI_MODEL=gemini-pro  # Optional
```

### Email Configuration

#### SendGrid
```bash
SENDGRID_API_KEY=SG....
FROM_EMAIL=noreply@yourdomain.com
```

#### SMTP
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_USE_TLS=True
```

## Initial Setup

### 1. Database Initialization
```bash
python initialize_db.py
```

This will:
- Create all database tables
- Set up initial schema
- Create default admin user
- Configure basic settings

### 2. Create Demo Data (Optional)
```bash
python create_demo_data.py
```

This will create:
- Sample products and categories
- Test customers and orders
- Demo store configurations
- Media files

### 3. Create Admin User
```bash
python -c "
from pycommerce.models.user import User
from pycommerce.core.db import db

user = User(
    username='admin',
    email='admin@example.com',
    password='admin123',  # Change this!
    role='admin'
)
db.session.add(user)
db.session.commit()
print('Admin user created')
"
```

## Verification

### 1. Check Application Status
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected"
}
```

### 2. Access Admin Dashboard
Navigate to: `http://localhost:5000/admin`

Default credentials:
- Username: `admin`
- Password: `admin123`

### 3. Check API Documentation
- Swagger UI: `http://localhost:5000/api/docs`
- ReDoc: `http://localhost:5000/api/redoc`

## Troubleshooting

### Common Issues

#### Database Connection Error
```
Error: could not translate host name "localhost" to address
```

**Solution:**
- Check PostgreSQL is running
- Verify connection string in `DATABASE_URL`
- Ensure database exists and user has permissions

#### Permission Denied Error
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**
- Check file permissions
- Ensure write access to log directories
- Run with appropriate user permissions

#### Port Already in Use
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
export PORT=8000
```

#### Missing Dependencies
```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Debug Mode

Enable debug mode for development:
```bash
export DEBUG=True
export FLASK_ENV=development
python main.py
```

### Logging

Check application logs:
```bash
tail -f logs/app.log
```

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

### Using Docker
```bash
docker run -d \
  --name pycommerce \
  -p 5000:5000 \
  -e DATABASE_URL="your_db_url" \
  -e SECRET_KEY="your_secret" \
  pycommerce:latest
```

### Environment-Specific Settings

#### Development
- Debug mode enabled
- SQLite database
- Hot reloading
- Detailed error pages

#### Production
- Debug mode disabled
- PostgreSQL database
- Process management (Gunicorn)
- Error logging
- SSL/HTTPS enabled
- Environment variable security

## Next Steps

After successful installation:

1. **Configure Your Store**
   - Visit `/admin/settings`
   - Set up store information
   - Configure payment methods

2. **Customize Theme**
   - Go to `/admin/theme-settings`
   - Upload logo and customize colors
   - Set up custom CSS

3. **Add Products**
   - Navigate to `/admin/products`
   - Create product categories
   - Add your first products

4. **Test Functionality**
   - Place test orders
   - Verify payment processing
   - Check email notifications

For more detailed configuration, see the [Configuration Guide](configuration.md).
