
# PyCommerce - Multi-Tenant E-commerce Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-red.svg)](https://flask.palletsprojects.com/)

PyCommerce is a powerful, multi-tenant e-commerce platform built with Python, featuring a plugin-based architecture and comprehensive admin dashboard. It supports multiple stores, advanced product management, AI-powered content generation, and extensive customization options.

## 🌟 Features

### Core E-commerce Functionality
- **Multi-tenant Architecture**: Support for multiple independent stores
- **Product Management**: Categories, variants, inventory tracking, and media management
- **Order Processing**: Complete order lifecycle with status tracking and fulfillment
- **Shopping Cart & Checkout**: Seamless customer experience with multiple payment options
- **Customer Management**: User accounts, order history, and customer analytics

### Advanced Features
- **AI Integration**: Content generation with OpenAI, Google Gemini, DeepSeek, and OpenRouter
- **Page Builder**: Drag-and-drop interface for creating custom store pages
- **Payment Processing**: Stripe and PayPal integration with secure checkout
- **Shipping Management**: Multiple shipping methods and rate calculation
- **Analytics & Reporting**: Sales trends, inventory reports, and market analysis
- **Media Management**: AI-generated content and multi-level sharing
- **Email System**: Automated notifications and marketing campaigns
- **Theme Customization**: Dynamic CSS styling and custom domain support

### Developer-Friendly
- **Plugin Architecture**: Extensible system for custom functionality
- **API-First Design**: Comprehensive REST API with OpenAPI documentation
- **Database Support**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT-based authentication with role management
- **GDPR Compliance**: Built-in privacy and data protection tools

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/pycommerce.git
   cd pycommerce
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/pycommerce"
   export SECRET_KEY="your-secret-key"
   export STRIPE_SECRET_KEY="your-stripe-key"  # Optional
   export OPENAI_API_KEY="your-openai-key"    # Optional
   ```

4. **Initialize the database**
   ```bash
   python initialize_db.py
   ```

5. **Start the application**
   ```bash
   python main.py
   ```

The application will be available at `http://localhost:5000`

### Demo Data (Optional)
```bash
python create_demo_data.py
```

## 📚 Documentation

- **[API Documentation](docs/api_reference.md)** - Complete API reference
- **[Plugin Development](docs/plugin_development.md)** - Creating custom plugins
- **[Deployment Guide](docs/deployment.md)** - Production deployment instructions
- **[Configuration](docs/configuration.md)** - Environment and settings configuration

### Interactive API Docs
- Swagger UI: `http://localhost:5000/api/docs`
- ReDoc: `http://localhost:5000/api/redoc`

## 🏗️ Architecture

PyCommerce follows a modular architecture:

```
pycommerce/
├── api/           # FastAPI routes and schemas
├── core/          # Core functionality and database
├── models/        # SQLAlchemy models
├── plugins/       # Payment, shipping, and AI plugins
├── services/      # Business logic services
└── utils/         # Utility functions

routes/
├── admin/         # Admin dashboard routes
├── api/           # API endpoints
└── storefront/    # Customer-facing routes

templates/         # Jinja2 templates
static/           # CSS, JavaScript, and media files
```

## 🔌 Plugin System

PyCommerce supports extensible plugins for:

- **Payment Processors**: Stripe, PayPal, and custom gateways
- **Shipping Methods**: Standard, express, and custom calculators  
- **AI Providers**: OpenAI, Google Gemini, DeepSeek, OpenRouter
- **Analytics**: Custom reporting and data analysis tools

### Creating a Plugin

```python
from pycommerce.core.plugin import Plugin

class CustomPaymentPlugin(Plugin):
    name = "custom_payment"
    version = "1.0.0"
    
    def process_payment(self, amount, currency, **kwargs):
        # Implementation here
        pass
```

## 🌐 Multi-Tenant Support

Each tenant operates independently with:
- Separate databases or schema isolation
- Custom domain support
- Individual theme customization
- Isolated user management
- Independent plugin configurations

## 🛡️ Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- CSRF protection
- SQL injection prevention
- XSS protection
- GDPR compliance tools
- Audit logging

## 📊 Analytics & Reporting

- Real-time sales dashboards
- Inventory tracking and alerts
- Customer behavior analysis
- Market trend analysis
- Performance metrics
- Custom report generation

## 🎨 Customization

### Theme System
- Dynamic CSS customization
- Custom page layouts
- Responsive design templates
- Brand customization

### Page Builder
- Drag-and-drop interface
- Pre-built components
- Custom HTML/CSS support
- Mobile-responsive design

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/pycommerce

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# Payment Processors
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-secret

# AI Services
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=your-google-key

# Email
SENDGRID_API_KEY=your-sendgrid-key
MAIL_SERVER=smtp.gmail.com
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=pycommerce

# Run specific test file
python -m pytest tests/test_products.py
```

## 🚀 Deployment

### Docker (Recommended)
```bash
docker build -t pycommerce .
docker run -p 5000:5000 pycommerce
```

### Traditional Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 main:app
```

### Replit Deployment
PyCommerce is optimized for deployment on Replit with automatic configuration.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all functions and classes
- Write comprehensive tests for new features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/index.md](docs/index.md)
- **Issues**: [GitHub Issues](https://github.com/your-username/pycommerce/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/pycommerce/discussions)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Flask for admin interface capabilities
- SQLAlchemy for robust ORM functionality
- Bootstrap for responsive UI components
- All our contributors and users

## 📈 Roadmap

- [ ] Mobile app support
- [ ] Advanced SEO tools
- [ ] Social media integration
- [ ] Marketplace functionality
- [ ] Advanced analytics dashboard
- [ ] Internationalization (i18n)
- [ ] Enhanced plugin marketplace

---

**PyCommerce** - Empowering businesses with flexible, scalable e-commerce solutions.
