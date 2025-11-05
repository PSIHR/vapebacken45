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