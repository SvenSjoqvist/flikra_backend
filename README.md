# Fashion Platform API

A comprehensive FastAPI backend for a fashion/brand/product platform with users, swipes, wishlists, analytics, and advanced search capabilities.

## 🚀 Features

- **User Management**: Registration, authentication, and profile management
- **Brand Management**: Brand profiles, members, and analytics
- **Product Catalog**: Product management with categories and pricing
- **Swipe System**: User interaction with products (like/dislike)
- **Wishlist**: Save favorite products
- **Analytics**: Track user behavior and brand performance
- **Advanced Search**: Vector-based product and brand search
- **Referral System**: Track referral clicks and conversions
- **Role-based Access**: User roles and permissions
- **API Key Authentication**: Secure access control for all endpoints

## 📋 New SQL Schema

The API now uses an updated SQL schema with the following tables:

### Core Tables
- **users**: User accounts with name, avatar, and profile info
- **brands**: Brand profiles with logo, industry, status, and plan
- **products**: Product catalog with pricing, categories, and status
- **roles**: System roles (user, admin, brand_owner, brand_team)
- **user_roles**: User role assignments with brand context
- **brand_members**: Direct brand membership relationships

### Interaction Tables
- **swipes**: User product interactions (left/right swipes)
- **wishlist_items**: Saved products with notes
- **referrals**: User referral tracking
- **referral_clicks**: Click tracking for referral links

### Analytics Tables
- **brand_analytics_events**: Comprehensive analytics events
- **referral_clicks**: Detailed referral click tracking

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backendcloth
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate API key**
   ```bash
   python generate_api_key.py
   ```

5. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/fashion_platform
   SECRET_KEY=your-secret-key-here
   API_KEY=your-generated-api-key-here
   ```

6. **Create database tables**
   ```bash
   python -m app.create_tables
   ```

7. **Run the API**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

## 🔐 API Key Authentication

The API is protected with API key authentication for enhanced security.

### Setup

1. **Generate an API key**:
   ```bash
   python generate_api_key.py
   ```

2. **Add to environment**:
   ```bash
   export API_KEY='your-generated-api-key'
   ```

3. **For NextJS frontend**, add to `.env.local`:
   ```env
   NEXT_PUBLIC_API_KEY=your-generated-api-key
   ```

### Usage

All API endpoints (except `/` and `/health`) require the API key in the Authorization header:

```
Authorization: Bearer your-api-key-here
```

### Security Features

- **Secure Key Generation**: Uses cryptographically secure random generation
- **Bearer Token**: Standard Bearer token authentication
- **Environment Variables**: Keys stored securely in environment variables
- **Public Endpoints**: Health check and root endpoint remain public
- **Error Handling**: Clear error messages for authentication failures

## 🔗 NextJS Integration

The API is configured with CORS support for NextJS frontend integration.

### API Client Setup

1. **Copy the API client** (`api-client-example.js`) to your NextJS project
2. **Set environment variables** in your NextJS `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_API_KEY=your-api-key-here
   ```

### Example Usage

```javascript
import apiClient from '../lib/api-client';

// Health check (no API key required)
const health = await apiClient.healthCheck();

// Fetch products (API key automatically included)
const products = await apiClient.getProducts();

// Create a swipe
await apiClient.createSwipe({
  user_id: "user-uuid",
  product_id: "product-uuid", 
  action: "right" // or "left"
});

// Get brand members
const members = await apiClient.getBrandMembers(brandId);
```

## 📚 API Endpoints

### Public Endpoints (No API Key Required)
- `GET /` - API information
- `GET /health` - Health check

### Protected Endpoints (API Key Required)

#### Users
- `POST /users/` - Create user
- `GET /users/{user_id}` - Get user
- `PUT /users/{user_id}` - Update user

#### Brands
- `GET /brands/` - List brands
- `POST /brands/` - Create brand
- `GET /brands/{brand_id}` - Get brand
- `PUT /brands/{brand_id}` - Update brand

#### Products
- `GET /products/` - List products
- `POST /products/` - Create product
- `GET /products/{product_id}` - Get product
- `PUT /products/{product_id}` - Update product

#### Swipes
- `POST /swipes/` - Create swipe
- `GET /swipes/user/{user_id}` - Get user swipes
- `GET /swipes/product/{product_id}` - Get product swipes

#### Wishlist
- `GET /wishlist/user/{user_id}` - Get user wishlist
- `POST /wishlist/` - Add to wishlist
- `DELETE /wishlist/{item_id}` - Remove from wishlist

#### Brand Members
- `GET /brand-members/` - List brand members
- `POST /brand-members/` - Add brand member
- `PUT /brand-members/{member_id}` - Update member
- `DELETE /brand-members/{member_id}` - Remove member

#### Analytics
- `POST /analytics/events/` - Create analytics event
- `GET /analytics/brand/{brand_id}` - Get brand analytics

#### Search
- `POST /search/products` - Search products
- `POST /search/brands` - Search brands

## 🔐 Authentication

The API uses two levels of authentication:

1. **API Key Authentication**: Required for all protected endpoints
2. **JWT Authentication**: For user-specific operations (when implemented)

Include the API key in the Authorization header:

```
Authorization: Bearer <your-api-key>
```

## 📊 Database Schema Changes

### Key Updates
- Added `name`, `avatar`, `updated_at` to users table
- Added `logo`, `website`, `industry`, `status`, `plan`, `updated_at` to brands table
- Simplified products table with `price`, `image`, `status`, `flagged` fields
- Changed `direction` to `action` in swipes table
- Added new `brand_members` table for direct brand relationships
- Updated analytics events to use `metadata` field

### Migration
Run the updated `create_tables.py` script to apply the new schema:

```bash
python -m app.create_tables
```

## 🧪 Testing

The API includes comprehensive test coverage. Run tests with:

```bash
pytest
```

## 📝 API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔒 Security Best Practices

1. **API Key Management**:
   - Generate unique keys for each environment
   - Rotate keys periodically
   - Never commit keys to version control

2. **Environment Variables**:
   - Use `.env` files for local development
   - Use secure environment variable management in production

3. **CORS Configuration**:
   - Only allow trusted origins
   - Configure CORS headers appropriately

4. **Database Security**:
   - Use strong database passwords
   - Limit database access to necessary IPs
   - Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 