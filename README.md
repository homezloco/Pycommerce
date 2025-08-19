
# PyCommerce - Multi-Tenant E-commerce Platform

[![PyCommerce CI](https://github.com/yourusername/pycommerce/actions/workflows/django.yml/badge.svg)](https://github.com/yourusername/pycommerce/actions/workflows/django.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive, multi-tenant e-commerce platform built with FastAPI, Flask, and modern web technologies. PyCommerce provides a complete solution for building and managing online stores with advanced features like AI integration, payment processing, inventory management, and customizable storefronts.

## 🚀 Features

### Core E-commerce
- **Multi-tenant architecture** - Support multiple stores in one installation
- **Product catalog** - Categories, variants, inventory tracking
- **Shopping cart & checkout** - Session-based cart with persistent storage
- **Order management** - Complete order lifecycle with status tracking
- **User accounts** - Customer registration and authentication
- **Admin dashboard** - Comprehensive management interface

### Advanced Features
- **Payment processing** - Stripe and PayPal integration
- **Shipping calculations** - Multiple shipping options and rate calculation
- **AI integration** - OpenAI, Google Gemini, Anthropic support
- **Media management** - Image uploads with AI generation
- **Page builder** - Drag-and-drop page creation
- **Email notifications** - Order confirmations and updates
- **Market analysis** - Demand forecasting and trend analysis
- **Estimates system** - Quote generation with PDF export
- **Return management** - Return request processing
- **Analytics** - Sales reporting and customer insights

### Technical Features
- **RESTful API** - FastAPI-based with automatic documentation
- **Database flexibility** - PostgreSQL with SQLAlchemy ORM
- **Plugin system** - Extensible architecture
- **Theme customization** - Customizable storefront themes
- **Security** - GDPR compliance tools, fraud detection
- **Performance** - Query optimization and caching

## 🛠️ Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL database
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pycommerce.git
   cd pycommerce
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/pycommerce"
   export SECRET_KEY="your-secret-key-here"
   export STRIPE_PUBLISHABLE_KEY="pk_test_..."
   export STRIPE_SECRET_KEY="sk_test_..."
   ```

4. **Initialize the database**
   ```bash
   python initialize_db.py
   ```

5. **Generate sample data (optional)**
   ```bash
   python generate_sample_data.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

The application will be available at `http://localhost:5000`

### Docker Installation (Coming Soon)
```bash
docker run -d \
  --name pycommerce \
  -p 5000:5000 \
  -e DATABASE_URL="your_db_url" \
  -e SECRET_KEY="your_secret" \
  pycommerce:latest
```

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [API Reference](docs/api_reference.md)
- [Features Overview](docs/features.md)
- [Payment Integration](docs/payment_integration.md)
- [Website Customization](docs/website_customization.md)
- [Deployment Guide](docs/deployment.md)

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | Flask/FastAPI secret key | Yes |
| `STRIPE_PUBLISHABLE_KEY` | Stripe public key | No |
| `STRIPE_SECRET_KEY` | Stripe secret key | No |
| `PAYPAL_CLIENT_ID` | PayPal client ID | No |
| `PAYPAL_CLIENT_SECRET` | PayPal client secret | No |
| `OPENAI_API_KEY` | OpenAI API key for AI features | No |
| `SENDGRID_API_KEY` | SendGrid for email notifications | No |

### Database Setup

PyCommerce uses PostgreSQL as the primary database. You can use any PostgreSQL provider:

- **Local PostgreSQL**: Install PostgreSQL locally
- **Cloud providers**: Neon, Supabase, AWS RDS, etc.
- **Development**: SQLite support for development

## 🏗️ Architecture

PyCommerce uses a hybrid architecture combining FastAPI for the API layer and Flask for the admin interface:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask Admin   │    │   FastAPI API   │
│   (Templates)   │◄──►│   Interface     │◄──►│   Backend       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────────────────────────┐
                        │          PostgreSQL Database        │
                        └─────────────────────────────────────┘
```

### Key Components

- **FastAPI App** (`web_app.py`) - Main API server
- **Flask Adapter** (`main.py`) - Admin interface and proxy
- **Models** (`pycommerce/models/`) - SQLAlchemy database models
- **Routes** (`routes/`) - API and admin route handlers
- **Services** (`pycommerce/services/`) - Business logic
- **Plugins** (`pycommerce/plugins/`) - Payment, shipping, AI integrations

## 🔌 Plugins

PyCommerce features an extensible plugin system:

### Payment Plugins
- **Stripe** - Credit card processing
- **PayPal** - PayPal payments

### Shipping Plugins
- **Standard Shipping** - Flat rate and weight-based shipping

### AI Plugins
- **OpenAI** - GPT-4 integration
- **Google Gemini** - Google's AI model
- **Anthropic** - Claude AI integration

### Creating Custom Plugins

```python
from pycommerce.core.plugin import BasePlugin

class MyCustomPlugin(BasePlugin):
    name = "my_custom_plugin"
    version = "1.0.0"
    
    def initialize(self):
        # Plugin initialization logic
        pass
```

## 🧪 Testing

Run the test suite:
```bash
python run_tests.py
```

For development with auto-reload:
```bash
export DEBUG=True
python main.py
```

## 🚀 Deployment

### Production Deployment

1. **Using Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
   ```

2. **Environment Configuration**
   ```bash
   export FLASK_ENV=production
   export DEBUG=False
   export DATABASE_URL="postgresql://..."
   ```

### Replit Deployment

PyCommerce is optimized for Replit deployment:

1. Fork this repository on Replit
2. Set environment variables in Replit Secrets
3. Click "Run" to start the application

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Reporting Issues

Please use the [GitHub issue tracker](https://github.com/yourusername/pycommerce/issues) to report bugs or request features.

## 📋 Roadmap

- [ ] Docker containerization
- [ ] Kubernetes deployment charts
- [ ] Mobile app API
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Advanced SEO tools
- [ ] Marketplace features
- [ ] Subscription products
- [ ] Advanced inventory management
- [ ] Integration with popular CMSs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Flask](https://flask.palletsprojects.com/)
- Database management with [SQLAlchemy](https://www.sqlalchemy.org/)
- Payment processing by [Stripe](https://stripe.com/) and [PayPal](https://paypal.com/)
- AI integration with [OpenAI](https://openai.com/), [Google Gemini](https://gemini.google.com/), and [Anthropic](https://anthropic.com/)

## 📞 Support

- 📧 Email: support@pycommerce.dev
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/pycommerce/discussions)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/yourusername/pycommerce/issues)
- 📖 Documentation: [docs/](docs/)

---

Made with ❤️ by the PyCommerce team
