# Telegram Mini App - Full Stack

## Overview
This project is a full-stack Telegram Mini App combining a FastAPI backend with an aiogram Telegram bot, a React SPA frontend with TailwindCSS, and an SQLite database. It aims to provide a comprehensive e-commerce solution within Telegram, featuring a product catalog, shopping cart, order management, and a loyalty program. The application is designed for both customer-facing interactions via the Mini App and administrative/courier functionalities through the Telegram bot.

## User Preferences
I prefer detailed explanations.
Do not make changes to the folder Z.
Do not make changes to the file Y.

## System Architecture

### UI/UX Decisions
The frontend is a React SPA using TailwindCSS for styling, with a modern glassmorphism design incorporating `Unbounded` font from Google Fonts. It adopts a minimalist Telegram-like aesthetic with dark gradient backgrounds and translucent elements. Key UI components include responsive product cards, a bottom navigation bar, and accessible elements like an accordion-based FAQ. The design prioritizes mobile UX within the Telegram environment.

### Technical Implementations
- **Backend**: FastAPI serves a REST API, integrated with `aiogram` for Telegram bot functionalities. It uses `SQLAlchemy` with `aiosqlite` for asynchronous database operations and `Alembic` for migrations.
- **Frontend**: Built with React 18 and Vite, it utilizes the official Telegram Web App script for integration with full-screen mode support. `Axios` handles API requests, and `React Router DOM` manages navigation.
- **Database**: SQLite is used for persistent data storage, including models for users, products, categories, orders, and loyalty program data.
- **Key Features**:
    - **Product Catalog**: Displays products with images, prices, categories, and taste/variant selection. Includes search and category filtering.
    - **Shopping Cart**: Allows quantity management and item removal.
    - **Order Management**: Supports various delivery methods (self-pickup, metro, courier, Yandex delivery, Европочта, Белпочта postal services) with dynamic cost calculation, time slot selection, and order status tracking.
    - **Loyalty Program**: Implemented with a stamp system (every 6th item discounted) and tiered loyalty cards (White, Platinum, Black) with increasing discounts. Tracks stamps and auto-upgrades levels.
    - **User Profiles**: Displays loyalty card and order history.
    - **Admin/Courier Bot Features**: Management of users, products, orders, promocodes, and access to analytics.
    - **Notifications**: Backend sends notifications to couriers and admins about new orders with full details.
    - **Accessibility**: Implemented ARIA-compliant components like the FAQ accordion.

### System Design Choices
The application follows a client-server architecture with a clear separation between frontend and backend. The Telegram bot acts as an interface for both customer entry points (via Web App button) and administrative tasks. The database schema supports a comprehensive e-commerce flow, including product variations (tastes), user baskets, orders, and promotional mechanics. Environment variables manage configuration for both backend and frontend. The system is designed for dual workflows, with the backend running on an internal port (3000) and the frontend on a public webview port (5000), utilizing a Vite proxy for API communication in development.

## Recent Changes

- **2025-11-02**: Fixed bot conflict in development environment
  - Changed default START_BOT value from "true" to "false" to prevent bot from auto-starting in development
  - Eliminates TelegramConflictError when production bot is running
  - Development environment now only runs FastAPI server without bot polling
  - Production deployment still runs bot with START_BOT=true environment variable
- **2025-11-02**: Added postal delivery options with full validation
  - Added two new delivery methods: Европочта (5 BYN) and Белпочта (3 BYN, displayed as 3-5 BYN range)
  - Database: Added 4 postal fields to Order model (postal_full_name, postal_phone, postal_address, postal_index)
  - Created incremental Alembic migration (a1b2c3d4e5f6) for postal delivery fields
  - Frontend: Added conditional forms in Checkout.jsx for postal recipient data collection
  - Backend: Added validation to enforce required fields based on delivery type (Европочта requires ФИО/phone/address, Белпочта additionally requires postal index)
  - Bot notifications: Enhanced to display formatted postal delivery information for admins and couriers
  - Migration chain: f50339118401 (dummy) → 0bd332ec95cc → a1b2c3d4e5f6 (ensures clean incremental updates)
- **2025-11-02**: Fixed preview white screen - corrected static files mounting
  - CRITICAL FIX: Moved static files mounting from lifespan to main app body (FastAPI requirement)
  - Fixed catchall route to not intercept /assets/ and /uploads/ requests
  - Added mock user (id: 123456789) for preview/testing when Telegram WebApp unavailable
  - Added safe fallbacks: showAlert → console.log, showConfirm → window.confirm
  - App fully functional in both preview and Telegram
  - Products display correctly with images, categories work, navigation works
  - Ready for production deployment via git commit + redeploy
- **2025-11-02**: Complete production deployment fixes and unified workflow
  - Removed separate frontend workflow - backend now serves built SPA on port 5000
  - Single workflow on port 5000 (webview)
  - Build script builds frontend to `frontend/dist`
  - Backend serves static files and handles SPA routing
  - Bot URL changed to `https://defivaultpro.com` (configurable via WEBAPP_URL env var)
  - Added START_BOT env var to control bot startup (false in development, true in production)
  - Production ready for defivaultpro.com
  - Note: Development runs with START_BOT=false to avoid bot conflicts with production
  - Important: VM deployment uses git commits, not workspace files - must commit changes before redeploy
- **2025-11-02**: Fixed production deployment configuration
  - Created `build.sh` script to properly build frontend in correct directory
  - Build command: `bash build.sh` (changes to frontend dir, runs npm install & build)
  - Run command: `bash -c "PYTHONPATH=/home/runner/workspace:$PYTHONPATH python app/main.py"`
  - Backend serves static files from `frontend/dist` when built (SPA fallback pattern)
  - Backend uses PORT environment variable (defaults to 5000 in production)
- **2025-11-01**: Added responsive "Выбрать" button to product cards
  - Mobile: Button is full-width below price for better UX
  - Desktop: Button appears inline next to price
  - Glassmorphism design with hover animations and chevron icon
- **2025-11-01**: Added product characteristics system
  - Database: Added 4 new nullable fields to Item model (strength, puffs, vg_pg, tank_volume)
  - Created Alembic migration for schema update
  - Bot admin panel: Added 4 new FSM states to collect characteristics during item creation
  - Characteristics are optional - admin can skip any field by entering "нет"
  - API: GET /items/ endpoint now returns all characteristics fields
  - Frontend ProductDetail improvements:
    - Moved tastes section ABOVE description for better UX flow
    - Made description collapsible with "Подробнее/Свернуть" button (auto-collapses after 3 lines if text >150 chars)
    - Added dedicated characteristics section displaying: крепкость, количество тяг, VG/PG, объем бака
    - Characteristics only display when present (handles nullable fields gracefully)
  - Full end-to-end flow: bot creation → database → API → frontend display
- **2025-11-01**: Added admin command to manually manage user loyalty profiles
  - New command `/set_loyalty` for admins to update loyalty data for any user
  - Allows setting: loyalty level (White/Platinum/Black), stamps (0-5), total items purchased
  - Interactive menu with buttons for easy management
  - Shows current loyalty status before making changes
  - Useful for migrating existing customers with established loyalty cards
- **2025-11-01**: Improved loyalty program UX with clearer messaging
  - Changed text from "6 покупок до скидки" to "5 покупок для скидки на 6-й заказ" (more logical)
  - When 5 stamps collected, shows animated message "🎉 На эту покупку у вас скидка!"
  - 6th circle gets golden ring highlight and pulse animation when discount is active
  - Added proper Russian pluralization (покупка/покупки) for better readability
- **2025-11-01**: Added full-screen mode and swipe-lock for Telegram Mini App
  - Implemented `requestFullscreen()` in `useTelegram` hook for immersive experience
  - App now automatically expands to full screen on launch, removing Telegram's header and bottom bars
  - Added `disableVerticalSwipes()` to prevent closing app by swiping down on content
  - Users can only close app via header swipe or close button (prevents accidental exits)
  - Full-screen mode provides better UX for product browsing and checkout
  - Falls back gracefully if features are not available on older Telegram clients
  - Added safe-area padding at top for devices with notches/Dynamic Island

## External Dependencies

- **FastAPI**: Backend web framework.
- **aiogram**: Telegram Bot API library.
- **React**: Frontend JavaScript library.
- **Vite**: Frontend build tool.
- **TailwindCSS**: CSS framework for styling.
- **SQLAlchemy**: Python ORM.
- **aiosqlite**: Async SQLite driver.
- **Alembic**: Database migration tool.
- **Uvicorn**: ASGI web server.
- **Axios**: Promise-based HTTP client for the browser and Node.js.
- **Lucide React**: Icon library.
- **Telegram Web App API**: Official Telegram script for Mini App integration with full-screen support.
- **Google Fonts**: For `Unbounded` typography.