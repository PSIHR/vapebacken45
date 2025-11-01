# Telegram Mini App - Backend

## Overview
This is a **Telegram Mini App backend** that combines a FastAPI REST API with a Telegram bot using aiogram. The application provides order management, user authentication, and product catalog functionality for a Telegram-based e-commerce system.

## Technology Stack
- **Framework**: FastAPI 0.116.1
- **Telegram Bot**: aiogram 3.21.0
- **Database**: SQLite with aiosqlite (async)
- **ORM**: SQLAlchemy 2.0.41
- **Migrations**: Alembic 1.16.4
- **Web Server**: Uvicorn 0.35.0
- **Python Version**: 3.11+

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
├── alembic/                # Database migrations
├── uploads/                # User uploaded files
├── config/                 # Configuration files
│   └── .env.local         # Environment variables
└── requirements.txt        # Python dependencies
```

## Recent Changes
- **2025-11-01**: Imported from GitHub and configured for Replit environment
  - Updated port from 8084 to 5000 for Replit compatibility
  - Updated host from localhost to 0.0.0.0 for public access
  - Added python-dotenv to requirements.txt
  - Configured PYTHONPATH in workflow to resolve module imports
  - Set up workflow for automatic server startup

## Environment Variables
Required environment variables in `config/.env.local`:
- `LOG_LEVEL`: Logging level (default: ERROR)
- `BACKEND_URL`: Backend URL for API
- `TOKEN`: Telegram Bot API token
- `ADMINS`: Comma-separated list of admin Telegram user IDs
- `COURIERS`: Comma-separated list of courier Telegram user IDs

## Running the Application
The application runs automatically via the configured workflow:
```bash
PYTHONPATH=/home/runner/workspace:$PYTHONPATH python app/main.py
```

The server starts on:
- **Host**: 0.0.0.0
- **Port**: 5000

## Features
- User registration and authentication via Telegram
- Product catalog management
- Shopping basket functionality
- Order creation and management
- Courier assignment and order tracking
- Promocode system
- User ban/unban functionality
- Analytics and sales reporting
- Admin panel via Telegram bot

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

## Deployment Notes
- The application is configured to run on port 5000 for Replit deployments
- CORS is enabled for all origins
- Static files (uploads) are served from the `/uploads` directory
- The Telegram bot polls for updates in the background
