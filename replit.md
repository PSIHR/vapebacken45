# Telegram Mini App - Full Stack

## Overview
This project is a full-stack Telegram Mini App providing a comprehensive e-commerce solution within Telegram. It features a FastAPI backend, an aiogram Telegram bot, and a React SPA frontend with TailwindCSS, all backed by an SQLite database. The app includes a product catalog, shopping cart, order management with various delivery options, and a loyalty program. It supports both customer interactions via the Mini App and administrative/courier functionalities through the Telegram bot. The brand is "VAPE PLUG," adopting a cyberpunk-inspired aesthetic.

## User Preferences
I prefer detailed explanations.
Do not make changes to the folder Z.
Do not make changes to the file Y.

## System Architecture

### UI/UX Decisions
The frontend is a React SPA styled with TailwindCSS, featuring a modern glassmorphism design and the `Unbounded` font. It follows a cyberpunk aesthetic with a black background and holographic cyan, purple, and pink gradient accents. Key UI components include responsive product cards, a bottom navigation bar, and accessible elements like an accordion-based FAQ, prioritizing mobile UX within the Telegram environment.

### Technical Implementations
- **Backend**: FastAPI for REST API, integrated with `aiogram` for Telegram bot functionalities. Uses `SQLAlchemy` with `aiosqlite` for async database operations and `Alembic` for migrations.
- **Frontend**: React 18 with Vite, utilizing the official Telegram Web App script for full-screen mode integration. `Axios` handles API requests, and `React Router DOM` manages navigation.
- **Database**: SQLite for persistent storage of users, products, categories, orders, and loyalty data.
- **Key Features**:
    - **Product Catalog**: Displays products with images, prices, categories, taste/variant selection, search, and filtering.
    - **Shopping Cart**: Allows quantity management and item removal.
    - **Order Management**: Supports various delivery methods (self-pickup, metro, courier, Yandex, postal services) with dynamic cost, time slot selection, and status tracking.
    - **Loyalty Program**: Stamp system (every 6th item discounted) and tiered loyalty cards (White, Platinum, Black) with increasing discounts.
    - **User Profiles**: Displays loyalty card and order history.
    - **Admin/Courier Bot Features**: Management of users, products, orders, promocodes, and analytics access.
    - **Notifications**: Backend sends detailed order notifications to couriers and admins.
    - **Accessibility**: Implemented ARIA-compliant components.

### System Design Choices
The application uses a client-server architecture. The Telegram bot serves as an entry point for customers and for administrative tasks. The database schema supports a comprehensive e-commerce flow, including product variations, user baskets, orders, and promotional mechanics. Configuration is managed via environment variables. The system is designed for a dual workflow, with the backend and a served static frontend operating on a unified port in production for Telegram Web App integration. It supports full-screen mode and swipe-lock for an immersive Telegram Mini App experience.

## Recent Changes

- **2025-11-17**: Fixed button overflow issues and duplicate taste creation bug
  - **ProductDetail page**: Made "Добавить в корзину" button fixed below navbar
    - Button positioned at bottom-0 with pb-24 offset and z-40 to sit under navbar (z-50)
    - Added max-h-96 with overflow-y-auto to taste selection grid for scrollable long lists
    - Enhanced button styling with shadow-xl and border for better visibility
    - Increased page padding-bottom (pb-44) to prevent content hiding under button
  - **ProductCard component**: Optimized card layout to prevent "Выбрать" button cutoff
    - Reduced image height from h-48 to h-36 for more compact cards
    - Removed description from card (only title + badge + price + buttons)
    - Used flexbox with flex-col and mt-auto to push buttons to bottom
    - Reduced padding (p-2.5) and button sizes (text-xs) for better mobile fit
    - Removed special "РАСХОДНИКИ" badge logic - only strength badges shown now
    - Strength badges show for all products with color coding: 0-39mg green, 40-69mg red, 70+mg burgundy
    - Cards now display properly in 2-column grid without overflow
  - **Bot duplicate taste fix**: Added deduplication logic when creating items with multiple tastes
    - Removes duplicate taste names from comma-separated input before database insert
    - Prevents UNIQUE constraint errors when same taste appears multiple times
    - Shows count of removed duplicates in success message
- **2025-11-16**: Fixed bot admin panel - taste creation and characteristics editing
  - **Taste Creation**: Removed mandatory photo requirement, now supports comma-separated bulk creation (e.g., "Барбарис, Вишня, Клубника")
  - **Characteristics Editing**: Shows current values (strength, puffs, VG/PG, tank volume) before editing, supports "-" to skip fields
  - Removed unused _handle_taste_image helper and photo handlers for taste creation
  - Added proper word declension for taste count (вкус/вкуса/вкусов)
  - Fixed characteristics saving to correct database fields instead of description field
- **2025-11-16**: Enhanced product navigation and UX improvements
  - Fixed back button navigation in ProductDetail to return to correct catalog using location.state.categoryId
  - Implemented Promise.all for parallel API requests when adding multiple tastes to cart (performance improvement)
  - Updated strength badge regex to support both "mg" and "мг" (localized) formats, plus numeric-only values
  - ProductCard now passes categoryId in navigation state for correct back button behavior
  - Added multiple taste selection with checkboxes instead of radio buttons
  - Added magnifying glass button with modal overlay for quick taste preview
  - Added "Консультант" button linking to https://t.me/vapepluggmanager
  - Removed BYN duplication in Profile orders display
  - Implemented lazy loading (loading="lazy") for all images across ProductCard, CartItem, Home, ProductDetail
  - Changed product card badges from category name to strength (mg) with color coding: 0-39mg green, 40-69mg red, 70+mg burgundy
- **2025-11-12**: Implemented PNG document upload support in Telegram bot
  - Added document handlers (F.document) alongside existing photo handlers (F.photo) for all 4 image upload states
  - Created paired-handler pattern with shared helper functions to eliminate code duplication
  - Document handlers validate MIME-type (image/*) before processing
  - Telegram can now send PNG files as documents (not just photos), and bot correctly processes them
  - Fixed FSM state reset bug in taste image upload when duplicate name detected
  - Refactored 4 photo handlers to use centralized helper functions: _handle_item_image, _handle_taste_image, _handle_item_edit_image, _handle_category_image
- **2025-11-12**: Implemented PNG transparency support throughout the application
  - Fixed bot's `save_photo` function to preserve file extensions (PNG, JPG) instead of forcing .jpg
  - Removed background colors from image containers across frontend (ProductCard, Home, ProductDetail, CartItem)
  - Transparent PNG images now "float" on the cyberpunk background without obstruction
  - Alpha channel is fully preserved from bot upload to frontend display
- **2025-11-12**: Fixed cart quantity synchronization with backend
  - Created PATCH endpoint `/basket/{user_id}/items/{basket_item_id}` for updating item quantities
  - Cart quantity changes now persist to backend immediately with optimistic UI updates
  - Checkout page now displays correct quantities and prices from synchronized backend data
  - Added rollback mechanism for failed quantity updates
- **2025-11-12**: Fixed payment options in checkout
  - Removed "Карта" payment option from non-postal delivery methods (Самовывоз, Курьером, По метро, Яндекс)
  - Added "Карта" and "Наложка" payment options for postal delivery methods (Европочта, Белпочта)
  - Auto-reset payment to "Наличные" when switching from postal to non-postal delivery
- **2025-11-05**: Updated bot welcome button URL to production store
  - Changed "Открыть магазин" button link from Replit dev URL to https://vaultroi.com
  - Bot now directs users to production store instead of development environment
- **2025-11-05**: Fixed text contrast on product detail page
  - Changed category badge text from white to black for better readability on bg-pink-100
  - Changed selected taste button text from white to black when bg-pink-100 is active
  - Unselected taste buttons keep white text on transparent background
  - Improved border color to pink-400 for selected taste buttons
- **2025-11-05**: Enhanced glassmorphism styling and white text hierarchy
  - Improved glass-card with enhanced blur (26px), white borders (0.3 opacity), and sophisticated inset shadows
  - Upgraded navbar (glass-bottom-nav) with premium glassmorphism effects and gradient top edge
  - Added new glass-button class for all interactive buttons with glassmorphism effects
  - Changed ALL text colors from gray to white across entire application (text-gray-* → text-white/text-white/80/text-white/70)
  - Updated all placeholders to white/50 opacity
  - All components now use consistent white text hierarchy: white (headers), white/80 (primary), white/70 (secondary), white/60 (tertiary)
  - Enhanced visual depth with ::before and ::after pseudo-elements creating light gradients
  - Added Cache-Control headers to disable image caching (fixes image update issues)
- **2025-11-05**: Updated product category names to uppercase short forms
  - Changed category names in database: "ОДНОРАЗКИ", "ЖИЖИ", "РАСХОДНИКИ", "СНЮС"
  - Previous names: "Одноразовые электронные сигареты" → "ОДНОРАЗКИ", "Жидкости" → "ЖИЖИ", "Поды" → "РАСХОДНИКИ", "Устройства" → "СНЮС"
  - Category images kept the same (will be replaced manually via admin panel)
  - Bot admin panel automatically displays new category names from database
- **2025-11-05**: Complete rebrand from "BASTER SHOP" to "VAPE PLUG" with cyberpunk design
  - Brand name changed to "VAPE PLUG" throughout application
  - Manager contact: @vapepluggmanager
  - Channel: https://t.me/vapplugg
  - Community chat: https://t.me/vapepluggcommunity
  - Pickup address: ст.м Грушевка
  - Black background (#000000) with gradient accents (cyan, purple, pink)
  - Glassmorphism with gradient borders and effects
  - All UI elements updated to cyberpunk aesthetic

## External Dependencies

- **FastAPI**: Backend web framework.
- **aiogram**: Telegram Bot API library.
- **React**: Frontend JavaScript library.
- **Vite**: Frontend build tool.
- **TailwindCSS**: CSS framework.
- **SQLAlchemy**: Python ORM.
- **aiosqlite**: Async SQLite driver.
- **Alembic**: Database migration tool.
- **Uvicorn**: ASGI web server.
- **Axios**: HTTP client.
- **Lucide React**: Icon library.
- **Telegram Web App API**: Official Telegram script for Mini App integration.
- **Google Fonts**: For `Unbounded` typography.