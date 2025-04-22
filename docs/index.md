# PyCommerce Documentation

## Introduction

Welcome to the PyCommerce documentation. PyCommerce is a sophisticated, multi-tenant ecommerce platform built with Python. This documentation provides comprehensive information on setting up, customizing, and extending the platform.

## Documentation Sections

### API Documentation
- [API Reference](api_reference.md) - Comprehensive reference for all API endpoints
- [API Endpoints](api_endpoints.md) - Focused reference for core API endpoints
- [Payment Integration](payment_integration.md) - Detailed guide on integrating payment providers

### Developer Guides

#### Setup and Configuration
- Environment Setup
- Database Configuration
- Multi-Tenant Configuration
- Custom Domain Setup

#### Core Concepts
- Plugin Architecture
- Multi-Tenant Design
- Security Model
- Data Isolation

#### Components
- Product Management
- Order Processing
- Customer Management
- Shipping and Tax Calculation
- Page Builder System

### Customization and Extension
- Custom Plugins Development
- Theme Development
- API Extensions
- Custom Checkout Flows

### Deployment and Operations
- Production Deployment
- Performance Optimization
- Monitoring and Logging
- Backup and Recovery

## API Access

PyCommerce provides several ways to interact with its API:

1. **Interactive API Documentation**:
   - Swagger UI: `/api/docs`
   - ReDoc: `/api/redoc`

2. **API Schema**:
   - OpenAPI Schema: `/api/openapi.json`

3. **Client Libraries**:
   - JavaScript SDK
   - Python SDK
   - PHP SDK

## Authentication

Most API endpoints require authentication. PyCommerce uses JWT (JSON Web Tokens) for API authentication. See the [API Reference](api_reference.md#authentication) for details on obtaining and using authentication tokens.

## Rate Limiting

API requests are subject to rate limiting to ensure platform stability:

- Anonymous requests: 60 requests per hour
- Authenticated requests: 1000 requests per hour

Rate limit headers are included in all API responses.

## Support

For additional support:

- GitHub Repository: [github.com/pycommerce/platform](https://github.com/pycommerce/platform)
- Documentation Issues: [github.com/pycommerce/platform/issues](https://github.com/pycommerce/platform/issues)
- Community Forum: [community.pycommerce.org](https://community.pycommerce.org)

## License

PyCommerce is released under the MIT License. See the LICENSE file for details.