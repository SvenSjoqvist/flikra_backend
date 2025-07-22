# Fashion Platform API

A comprehensive FastAPI backend for a fashion/brand/product platform with user management, product swiping, wishlists, analytics, and recommendations.

## Features

- **User Management**: User registration, authentication, and role-based access
- **Brand Management**: Create and manage fashion brands
- **Product Management**: Add products with categories, tags, images, and metadata
- **Swipe System**: Tinder-like swiping mechanism for products
- **Wishlist**: Save and manage favorite products
- **Analytics**: Track user interactions and brand performance
- **Recommendations**: AI-powered product recommendations based on user behavior
- **Role-based Access**: Support for different user roles (user, admin, brand_owner, brand_team)

## Database Schema

The application uses PostgreSQL with the following main tables:
- `users` - User accounts and authentication
- `roles` - User role definitions
- `brands` - Fashion brand information
- `user_roles` - User-brand-role relationships
- `products` - Product catalog with metadata
- `swipes` - User swipe interactions
- `wishlist_items` - User saved products
- `referrals` - User referral system
- `brand_analytics_events` - Detailed analytics tracking
- `referral_clicks` - Referral click tracking

## Project Structure

```
venv/app/
├── main.py                 # FastAPI application setup
├── db.py                   # Database configuration
├── models/                 # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── user.py
│   ├── role.py
│   ├── brand.py
│   ├── product.py
│   ├── swipe.py
│   ├── wishlist_item.py
│   └── ...
├── schemas/                # Pydantic schemas
│   ├── __init__.py
│   ├── user.py
│   ├── brand.py
│   ├── product.py
│   └── ...
├── routers/                # API route handlers
│   ├── __init__.py
│   ├── users.py
│   ├── brands.py
│   ├── products.py
│   ├── swipes.py
│   ├── wishlist.py
│   ├── analytics.py
│   └── recommendations.py
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── auth.py             # Authentication utilities
└── services/               # Business logic services
    └── vector_service.py   # Vector similarity service
```

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**
   - Install PostgreSQL
   - Create a database
   - Run the SQL schema from your database schema file
   - Update the `DATABASE_URL` in `venv/app/db.py`

3. **Environment Variables**
   ```bash
   export SECRET_KEY="your-secret-key-here"
   export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
   ```

4. **Run the Application**
   ```bash
   cd venv
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Users (`/users`)
- `GET /users/` - List all users
- `POST /users/` - Create new user
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Brands (`/brands`)
- `GET /brands/` - List all brands
- `POST /brands/` - Create new brand
- `GET /brands/{brand_id}` - Get brand by ID
- `PUT /brands/{brand_id}` - Update brand
- `DELETE /brands/{brand_id}` - Delete brand
- `GET /brands/{brand_id}/products` - Get brand products

### Products (`/products`)
- `GET /products/` - List products (with filtering)
- `POST /products/` - Create new product
- `GET /products/{product_id}` - Get product by ID
- `PUT /products/{product_id}` - Update product
- `DELETE /products/{product_id}` - Delete product
- `GET /products/categories/` - Get all categories
- `GET /products/tags/` - Get all tags

### Swipes (`/swipes`)
- `POST /swipes/` - Record a swipe
- `GET /swipes/user/{user_id}` - Get user's swipes
- `GET /swipes/product/{product_id}` - Get product's swipes
- `GET /swipes/stats/product/{product_id}` - Get swipe statistics

### Wishlist (`/wishlist`)
- `POST /wishlist/` - Add item to wishlist
- `GET /wishlist/user/{user_id}` - Get user's wishlist
- `PUT /wishlist/{wishlist_item_id}` - Update wishlist item
- `DELETE /wishlist/{wishlist_item_id}` - Remove from wishlist

### Analytics (`/analytics`)
- `POST /analytics/` - Track analytics event
- `GET /analytics/brand/{brand_id}` - Get brand events
- `GET /analytics/product/{product_id}` - Get product events
- `GET /analytics/stats/brand/{brand_id}` - Get brand statistics
- `GET /analytics/stats/product/{product_id}` - Get product statistics

### Recommendations (`/recommendations`)
- `GET /recommendations/{user_id}` - Get product recommendations

## Authentication

The API uses JWT tokens for authentication. Password hashing is implemented using bcrypt.

## Database Features

- **Automatic Triggers**: Swipe counts are automatically updated via PostgreSQL triggers
- **Materialized Views**: `top_performing_products` view for analytics
- **Indexes**: Optimized for common queries (category, tags, user lookups)
- **UUID Primary Keys**: For better scalability and security

## Development

The API is built with:
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: ORM for database operations
- **Pydantic**: Data validation and serialization
- **PostgreSQL**: Primary database with advanced features
- **pgvector**: Vector similarity search for recommendations

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

1. Follow the existing code structure
2. Add proper type hints and docstrings
3. Update schemas and models when adding new features
4. Test all endpoints before submitting changes 