# PyCommerce Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-tenant ecommerce platform with plugin-based architecture
- Product management with categories and variants
- Shipping notification emails when order status changes to "shipped"
- Shopping cart and checkout functionality
- Order management with order notes and status tracking
- Payment processing with Stripe and PayPal plugins
- Shipping calculation with multiple shipping methods
- Admin dashboard for store management
- User management interface with CRUD operations
- Media manager with AI-generated content, multi-level sharing, and SVG preview support
- Mobile-friendly admin interface with responsive navigation
- Newsletter subscription and campaign management system
- Comprehensive sales and inventory reporting
- Enhanced product listing and detail pages

### Changed
- Updated order status to use string values instead of integers for improved readability and better display in the admin interface
- Email notifications for order confirmations
- Theme customization with dynamic CSS styling
- Enhanced mobile responsiveness with hamburger menu toggle for admin dashboard
- Refactored monolithic web_server.py into specialized route modules
- Enhanced error handling for payment providers with specific error types
- Updated order detail page to show product names correctly
- Reorganized admin UI for better user experience
- Improved database query efficiency

### Fixed
- [2025-04-10] Fixed SVG image previews in media library to properly display vector graphics
- [2025-04-10] Enhanced menu navigation with better organization and submenu structure
- [2025-04-09] Improved mobile navigation with hamburger menu and auto-collapsing sidebar
- [2025-04-09] Redesigned products page with improved filtering and organization
- [2025-04-08] Fixed product names in order details page to display proper product names instead of SKUs
- [2025-04-08] Added newsletter management system with subscription tracking
- [2025-04-07] Fixed admin sidebar navigation to be persistent across the admin panel
- [2025-04-07] Implemented comprehensive reporting system for sales and inventory
- [2025-04-06] Fixed duplicate menu issue in admin dashboard
- [2025-04-06] Fixed circular import issues in managers and route files
- [2025-04-05] Fixed server stability issues with Uvicorn configuration
- [2025-04-05] Fixed SQLAlchemy model conflicts with centralized model registry pattern
- [2025-04-04] Fixed method name inconsistencies between SDK and implementation

### Security
- Implemented proper authentication and authorization
- Enhanced data isolation for multi-tenant architecture
- Added JWT token-based authentication

## [0.1.0] - 2025-04-01

### Added
- Initial project setup
- Database schema with multi-tenant support
- Basic plugin architecture
- Core API endpoints
