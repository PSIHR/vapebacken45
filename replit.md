# Telegram Mini App - Full Stack

## Overview
This is a **Telegram Mini App** with a complete full-stack implementation combining:
- **Backend**: FastAPI REST API with Telegram bot using aiogram
- **Frontend**: Modern React SPA with TailwindCSS and Telegram Web App integration
- **Database**: SQLite with async support for order management and product catalog

## Technology Stack

### Backend
- **Framework**: FastAPI 0.116.1
- **Telegram Bot**: aiogram 3.21.0
- **Database**: SQLite with aiosqlite (async)
- **ORM**: SQLAlchemy 2.0.41
- **Migrations**: Alembic 1.16.4
- **Web Server**: Uvicorn 0.35.0
- **Python Version**: 3.11+

### Frontend
- **Framework**: React 18 with Vite
- **Styling**: TailwindCSS with custom glassmorphism utilities
- **Typography**: Unbounded font from Google Fonts
- **Design**: Glassmorphism with gradient backgrounds
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Telegram SDK**: @telegram-apps/sdk-react

## Project Structure
```
.
├── app/                    # FastAPI application
│   └── main.py            # Main application entry point
├── bot/                    # Telegram bot
│   └── bot.py             # Bot handlers and logic
├── database/               # Database configuration
│   ├── db.py              # Database connection
│   ├── models.py          # SQLAlchemy models
│   └── init_db.py         # Database initialization
├── middlewares/            # FastAPI middlewares
│   └── ban.py             # Banned user middleware
├── typization/             # Pydantic models
│   └── models.py          # Request/response models
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components (Catalog, Cart, Checkout, Orders)
│   │   ├── services/      # API client
│   │   ├── hooks/         # Custom React hooks
│   │   └── utils/         # Helper functions
│   ├── vite.config.js     # Vite configuration
│   └── package.json       # Frontend dependencies
├── alembic/                # Database migrations
├── uploads/                # User uploaded files
├── config/                 # Configuration files
│   └── .env.local         # Backend environment variables
└── requirements.txt        # Python dependencies
```

## Recent Changes
- **2025-11-01**: Comprehensive delivery system update with time fields and cost calculation
  - Added "Яндекс доставка" delivery method with link to instructions
  - Updated self-pickup address to: пр. Дзержинского 26, подъезд 4
  - Implemented info modals (ℹ️ button) for each delivery method with full conditions
  - Added time input fields:
    - Self-pickup & Metro: Text input for preferred time
    - Address delivery: Dropdown for time slots (14:00-16:00 or 18:00-21:30)
  - Automatic delivery cost calculation:
    - Address delivery: 8 BYN if order < 80 BYN, free if ≥ 80 BYN
    - Other methods: Free
  - Database changes:
    - Added preferred_time, time_slot, delivery_cost columns to Order model
    - Changed address column to nullable for self-pickup and metro orders
    - Created two Alembic migrations for schema updates
  - Frontend auto-fills address for self-pickup and metro delivery
  - Backend notifications now show delivery cost and time information
  - All prices displayed in BYN (Belarusian Ruble)
- **2025-11-01**: Added FAQ page with accessible accordion component
  - Created comprehensive FAQ page with 11 questions and answers about products and usage
  - Implemented accordion with smooth transitions and glassmorphism design
  - First question opens by default for better UX
  - Added FAQ button to Header (top-right corner) for easy access
  - Full ARIA compliance: aria-expanded, aria-controls, aria-labelledby, aria-hidden
  - Screen reader compatible - collapsed panels hidden from assistive technology
  - Questions cover: warranty, cartridge care, taste fatigue, winter usage, PG/VG info, and more
  - Architect confirmed implementation meets all accessibility requirements ✓
- **2025-11-01**: Fixed critical bugs in loyalty discount logic (PRODUCTION READY)
  - Fixed NameError in basket endpoint return statement
  - Fixed discount allocation to use basket_item.id instead of item.id (handles same product with different tastes)
  - Discounts now correctly distribute across multiple items sorted by price (most expensive first)
  - Multiple discount thresholds handled correctly (6, 12, 18 items, etc.)
  - All earned discounts applied even when most expensive item has lower quantity
  - Architect confirmed implementation is production-ready ✓
- **2025-11-01**: Implemented Loyalty Program with Stamp System
  - Added loyalty program: 1 stamp per purchased item, every 6th item gets discount
  - Three loyalty card levels: White (25%), Platinum (30%), Black (35% forever)
  - Created Profile page with beautiful 3D loyalty card and order history
  - Replaced "Orders" navigation button with "Profile" 
  - Automatic discount applied in cart on most expensive item when eligible
  - Backend tracks stamps, loyalty_level, total_items_purchased for each user
  - Stamps reset every 6 items and loyalty level upgrades automatically
  - Created LoyaltyCard component with 3D effects and level-specific styling
- **2025-11-01**: Simplified product cards for better mobile UX
  - Removed "В корзину" button from product cards (was too bulky on mobile)
  - Entire product card is now clickable to open product detail page
  - Users add items to cart from detail page where they can select taste/variant
  - Cleaner, more minimalist card design with just product info and price
  - Price increased to text-2xl for better visibility without button
- **2025-11-01**: Improved product card layout and styling
  - Product titles now larger and bolder (text-xl font-bold)
  - Changed currency from ₽ to BYN (Belarusian Ruble)
  - Grid layout changed to 2 columns for better mobile view
  - Fixed search icon blur issue by restructuring backdrop-blur application
- **2025-11-01**: Added categories and search functionality to main catalog page
  - Categories now load from backend `/categories/` API endpoint
  - Added categoriesAPI to services/api.js for fetching categories
  - Implemented search bar below categories with real-time filtering
  - Search filters products by name and description
  - Combined filtering: both category and search work together
  - Updated Catalog.jsx to use Promise.all for parallel data loading
  - Search bar styled with glassmorphism effect matching app design
- **2025-11-01**: Added Web App button to /start command
  - Users now see "🛍 Открыть магазин" inline button after /start command
  - Button opens Telegram Mini App directly from bot conversation
  - Available for all user types (customers, couriers, admins)
  - Uses WebAppInfo with REPLIT_DEV_DOMAIN for Web App URL
- **2025-11-01**: Added metro delivery option with line and station selection
  - Added "По метро" as delivery option in checkout
  - Implemented cascading dropdowns: select metro line first, then station
  - Three metro lines available: Московская, Автозаводская, Зеленолужская (Minsk metro)
  - Each line has 7-15 stations to choose from
  - Database updated with metro_line and metro_station columns in orders table
  - Bot notifications updated to show metro information to couriers and admins
  - Frontend validates metro fields when metro delivery is selected
  - Created metroData.js with complete metro lines and stations data
- **2025-11-01**: Added bottom navigation in Telegram style with glassmorphism
  - Created BottomNavigation component with three buttons: Магазин, Корзина, Заказы
  - Implemented glassmorphism effect with dark translucent background and blur
  - Active button highlighted in blue (Telegram style)
  - Added badge counter for cart items
  - Simplified Header to show only shop name (centered)
  - Navigation fixed at bottom with safe-area-inset support
  - Smooth transitions and hover effects
- **2025-11-01**: Fixed dark gradient background display issue
  - Removed bg-gray-50 from App.jsx that was overriding body gradient
  - Applied dark gradient background (135deg, #0f172a slate-900 to #581c87 purple-900)
  - Added background-attachment: fixed for consistent gradient display
  - All pages now correctly display dark gradient with excellent text contrast
- **2025-11-01**: Implemented glassmorphism design with Unbounded font
  - Added Unbounded font from Google Fonts for modern typography
  - Implemented glassmorphism effect with backdrop blur and translucency
  - Created custom CSS utility classes: .glass-card, .glass-header, .glass-panel
  - Updated all components with glassmorphism styling (ProductCard, Header, CartItem, Cart, Checkout, Orders, OrderCard)
  - Changed all text colors to white/white-translucent for readability on dark gradient background
  - Product images display with object-contain for full, uncropped photos
  - Modern, premium aesthetic combining Telegram minimalism with glassmorphism effects
- **2025-11-01**: Added product detail page with taste selection
  - Created ProductDetail page to view full product information
  - Implemented taste/flavor selection functionality
  - Made product cards clickable to navigate to detail page
  - Added navigation routing for /product/:id
  - Users can now select taste before adding to cart
  - Fixed image loading by adding /uploads proxy in Vite config
- **2025-11-01**: Redesigned UI in Telegram minimalist style
  - Removed bright gradients and emojis for clean, professional look
  - Applied Telegram color palette: white backgrounds, #f4f4f5 page background, #3390ec accent color
  - Simplified all components (Header, ProductCard, Catalog, Cart, Checkout, CartItem)
  - Replaced shadows with subtle borders for consistency
  - Minimalist typography and spacing throughout
  - Clean, modern, professional design matching Telegram aesthetic
- **2025-11-01**: Complete full-stack implementation
  - Added React + Vite frontend with TailwindCSS
  - Integrated Telegram Web App SDK
  - Created UI for catalog, cart, checkout, and orders
  - Backend moved to port 3000, frontend on port 5000
  - Set up dual workflows for backend and frontend
  - Configured API proxy for seamless communication
  - Added responsive design optimized for mobile Telegram app

## Environment Variables

### Backend (`config/.env.local`)
- `LOG_LEVEL`: Logging level (default: ERROR)
- `BACKEND_URL`: Backend URL for API
- `TOKEN`: Telegram Bot API token
- `ADMINS`: Comma-separated list of admin Telegram user IDs
- `COURIERS`: Comma-separated list of courier Telegram user IDs

### Frontend (`frontend/.env`)
- `VITE_API_URL`: Backend API URL (used in production builds)
  - Development mode uses Vite proxy to route `/api` → `localhost:3000`
  - Production mode requires explicit VITE_API_URL configuration

## Running the Application

The application runs automatically via two configured workflows:

### Backend Workflow
```bash
PYTHONPATH=/home/runner/workspace:$PYTHONPATH python app/main.py
```
- **Host**: 0.0.0.0
- **Port**: 3000
- **Type**: Console (internal API)

### Frontend Workflow
```bash
cd frontend && npm run dev
```
- **Host**: 0.0.0.0
- **Port**: 5000
- **Type**: Webview (public web interface)

## Features

### Customer Features (Web App)
- 🛍️ Beautiful product catalog with categories
- 🎨 Responsive design optimized for Telegram
- 🛒 Shopping cart with quantity management
- 📝 Order checkout with address and payment options
- 📦 Order history and status tracking
- 🎯 Category filtering
- 💰 Promocode support

### Admin/Courier Features (Telegram Bot)
- 👥 User management (ban/unban)
- 📦 Product catalog management
- 🚚 Order assignment and tracking
- 📊 Analytics and sales reporting
- 🏷️ Promocode creation and management
- 📈 Customer statistics (new, regular, VIP)

## Database
The application uses SQLite with async support (aiosqlite). The database file is created automatically on first run as `database.db` in the root directory.

### Database Models
- **DBUser**: User accounts
- **Item**: Products/items
- **Category**: Product categories
- **Taste**: Product variations
- **Basket**: User shopping baskets
- **BasketItem**: Items in baskets
- **Order**: Customer orders
- **OrderItem**: Items in orders
- **Promocode**: Discount codes
- **Courier**: Delivery couriers

## API Endpoints
- `GET /`: Health check
- `POST /users/register`: User registration
- `GET /users/{user_id}/orders/`: Get user orders
- `POST /basket/{user_id}`: Get or create basket
- `POST /basket/{user_id}/items`: Add item to basket
- `DELETE /basket/{user_id}/items/{item_id}`: Remove item from basket
- `GET /items/`: Get all items
- `POST /orders/from_basket/{user_id}`: Create order from basket
- `PATCH /orders/{order_id}/status`: Update order status
- Plus many admin endpoints for item, category, and promocode management

## Telegram Bot Commands
The bot provides different interfaces for:
- **Customers**: Order tracking, product browsing
- **Couriers**: New orders, active orders, completed orders
- **Admins**: User management, product management, analytics

## Frontend Pages

### Catalog Page (`/`)
- Displays all products with images, prices, and descriptions
- Category filtering
- Add to cart functionality
- Product taste/variant selection

### Cart Page (`/cart`)
- View cart items
- Adjust quantities
- Remove items
- See total price
- Proceed to checkout

### Checkout Page (`/checkout`)
- Enter delivery address
- Provide phone number
- Select payment method
- Choose delivery type
- Apply promocodes
- Confirm order

### Orders Page (`/orders`)
- View order history
- Track order status
- See order details and items

## Deployment Notes
- Backend runs on port 3000 (internal API)
- Frontend runs on port 5000 (public web interface)
- CORS is enabled for all origins
- Static files (uploads) are served from the `/uploads` directory
- The Telegram bot polls for updates in the background
- Frontend uses Replit domain for backend API calls
- Telegram Web App SDK integrated for native Telegram features
