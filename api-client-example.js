// Example API client for NextJS to connect to FastAPI backend
// This can be used in your NextJS application

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'your-api-key-here';

class ApiClient {
  constructor(baseURL = API_BASE_URL, apiKey = API_KEY) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Invalid API key. Please check your API_KEY environment variable.');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Health check (no API key required)
  async healthCheck() {
    const url = `${this.baseURL}/health`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  // Authentication endpoints (no API key required)
  async brandLogin(email, password) {
    const url = `${this.baseURL}/auth/brand-login`;
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important for cookies
        body: JSON.stringify({ email, password }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Brand login failed:', error);
      throw error;
    }
  }

  async brandLogout() {
    const url = `${this.baseURL}/auth/logout`;
    try {
      const response = await fetch(url, {
        method: 'POST',
        credentials: 'include', // Important for cookies
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Brand logout failed:', error);
      throw error;
    }
  }

  async getCurrentUser() {
    const url = `${this.baseURL}/auth/me`;
    try {
      const response = await fetch(url, {
        credentials: 'include', // Important for cookies
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get current user failed:', error);
      throw error;
    }
  }

  async verifySession() {
    const url = `${this.baseURL}/auth/verify-session`;
    try {
      const response = await fetch(url, {
        credentials: 'include', // Important for cookies
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Session verification failed:', error);
      throw error;
    }
  }

  // User endpoints
  async createUser(userData) {
    return this.request('/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getUser(userId) {
    return this.request(`/users/${userId}`);
  }

  async getUsersWithBrands() {
    return this.request('/users/with-brands');
  }

  async updateUser(userId, userData) {
    return this.request(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  // Brand endpoints
  async getBrands() {
    return this.request('/brands/');
  }

  async getBrand(brandId) {
    return this.request(`/brands/${brandId}`);
  }

  async getBrandProducts(brandId) {
    return this.request(`/brands/${brandId}/products`);
  }

  async getBrandStats(brandId) {
    return this.request(`/brands/${brandId}/stats`);
  }

  async getBrandStatsSimple(brandId) {
    return this.request(`/brands/${brandId}/stats/simple`);
  }

  async createBrand(brandData) {
    return this.request('/brands/', {
      method: 'POST',
      body: JSON.stringify(brandData),
    });
  }

  // Product endpoints
  async getProducts(brandId = null, category = null) {
    let endpoint = '/products/';
    const params = new URLSearchParams();
    
    if (brandId) params.append('brand_id', brandId);
    if (category) params.append('category', category);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return this.request(endpoint);
  }

  async getProduct(productId) {
    return this.request(`/products/${productId}`);
  }

  // Swipe endpoints
  async createSwipe(swipeData) {
    return this.request('/swipes/', {
      method: 'POST',
      body: JSON.stringify(swipeData),
    });
  }

  async getUserSwipes(userId, action = null) {
    let endpoint = `/swipes/user/${userId}`;
    if (action) {
      endpoint += `?action=${action}`;
    }
    return this.request(endpoint);
  }

  // Wishlist endpoints
  async getWishlist(userId) {
    return this.request(`/wishlist/user/${userId}`);
  }

  async addToWishlist(wishlistItem) {
    return this.request('/wishlist/', {
      method: 'POST',
      body: JSON.stringify(wishlistItem),
    });
  }

  async removeFromWishlist(wishlistItemId) {
    return this.request(`/wishlist/${wishlistItemId}`, {
      method: 'DELETE',
    });
  }

  // Brand members endpoints
  async getBrandMembers(brandId = null, userId = null) {
    let endpoint = '/brand-members/';
    const params = new URLSearchParams();
    
    if (brandId) params.append('brand_id', brandId);
    if (userId) params.append('user_id', userId);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return this.request(endpoint);
  }

  async createBrandMember(brandMemberData) {
    return this.request('/brand-members/', {
      method: 'POST',
      body: JSON.stringify(brandMemberData),
    });
  }

  // New method: Create user and brand member together
  async createUserAndBrandMember(userAndBrandMemberData) {
    return this.request('/brand-members/with-user', {
      method: 'POST',
      body: JSON.stringify(userAndBrandMemberData),
    });
  }

  // Analytics endpoints
  async createAnalyticsEvent(eventData) {
    return this.request('/analytics/events/', {
      method: 'POST',
      body: JSON.stringify(eventData),
    });
  }

  async getBrandAnalytics(brandId, startDate = null, endDate = null) {
    let endpoint = `/analytics/brand/${brandId}`;
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }
    
    return this.request(endpoint);
  }

  // Search endpoints
  async searchProducts(query, filters = {}) {
    return this.request('/search/products', {
      method: 'POST',
      body: JSON.stringify({ query, ...filters }),
    });
  }

  async searchBrands(query) {
    return this.request('/search/brands', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }
}

// Create a singleton instance
const apiClient = new ApiClient();

// Export for use in NextJS
export default apiClient;

// Example usage in NextJS components:
/*
import apiClient from '../lib/api-client';

// In a React component or API route
export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProducts() {
      try {
        // First check if API is healthy
        const health = await apiClient.healthCheck();
        console.log('API Health:', health);
        
        // Then fetch products
        const data = await apiClient.getProducts();
        setProducts(data);
      } catch (error) {
        console.error('Failed to fetch products:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchProducts();
  }, []);

  // ... rest of component
}

// Example: Create user and brand member together
const newMember = await apiClient.createUserAndBrandMember({
  email: "john@example.com",
  name: "John Doe",
  password: "securepassword123",  // Add password
  avatar: "https://example.com/avatar.jpg", // optional
  brand_id: "brand-uuid-here",
  role: "member",
  status: "active"
});
*/ 