# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Sprunki Phase 4**, a multilingual Flask web application that serves as a gaming website with embedded iframe games. The application supports 27+ languages and includes a sophisticated comment system with admin management capabilities.

## Development Commands

### Starting the Application
```bash
# Development server (runs on port 9028)
python run.py

# Or using python3 if needed
python3 run.py
```

### Key URLs
- **Main Application**: http://localhost:9028
- **Admin Panel**: http://localhost:9028/admin (credentials via env vars: `ADMIN_USERNAME`, `ADMIN_PASSWORD`)
- **Comment Demo**: http://localhost:9028/comment-demo
- **Test Endpoint**: http://localhost:9028/test

### Environment Setup
```bash
# Install dependencies (note: requirements.txt has encoding issues, install manually)
pip install Flask==2.2.3 flask-admin==1.6.1 flask-babel==4.0.0 flask-mongoengine==1.0.0
pip install pymongo==3.13.0 loguru python-dotenv flask-compress

# Copy environment template
cp .env.example .env
```

## Architecture Overview

### Core Application Structure
- **Entry Point**: `run.py` - Main application runner with Flask-Admin integration
- **App Factory**: `get_app.py` - Flask app creation with Babel i18n setup
- **Configuration**: `setting.py` - Environment-based config with 27 language support
- **Database**: MongoDB via MongoEngine with custom document models

### Multi-language Architecture
The application implements a URL-based language routing system:
- **URL Pattern**: `/{language_code}/path` (e.g., `/ja/sprunki-phase-3.html`)
- **Language Detection**: Extracted from URL path segments in `get_locale()`
- **Supported Languages**: 27 languages defined in `ALLOWED_LANGUAGES`
- **Translation Files**: Located in `translations/{lang_code}/LC_MESSAGES/`

### Blueprint Structure
```
apps/views/
├── admin_urls.py    # Admin panel routes
├── base_urls.py     # Core application routes  
├── web_url.py       # Main website content routes
└── comment_api.py   # Comment system API endpoints
```

### Database Models (MongoDB)
```
apps/models/
├── article_model.py    # Content models (文章db, 分类db, 标签db, etc.)
├── comment_model.py    # Comment system models
├── admin_model.py      # Admin user management
└── article_view.py     # Flask-Admin views
```

### Frontend Assets Architecture
```
static/
├── style/
│   ├── fullscreen.js         # iOS-optimized fullscreen functionality
│   ├── native-fullscreen.js  # Standard browser fullscreen
│   ├── script.js             # General utilities
│   └── style.css             # Main stylesheet
├── js/
│   ├── game-status-bar.js    # Game controls integration
│   ├── comment-system.js     # Comment form handling
│   └── comments.js           # Comment display logic
└── css/
    └── comment-system.css    # Comment styling
```

## Key Features & Systems

### 1. iOS Fullscreen System
**Critical Implementation Detail**: The fullscreen system has device-specific handling:
- **iOS Devices**: Uses CSS transform-based fullscreen with rotation (`fullscreen.js`)
- **Other Devices**: Standard browser fullscreen API (`native-fullscreen.js`) 
- **Script Loading**: Dynamic sequential loading to ensure proper initialization order

**DO NOT** modify the script loading sequence in templates - it's carefully orchestrated.

### 2. Comment System
Fully integrated comment system with:
- **API Endpoints**: `/api/comments/{article_url}` for CRUD operations
- **Admin Integration**: Flask-Admin views for moderation
- **Performance**: Limited to 5 replies per comment for optimization
- **Spam Detection**: Configurable keyword filtering

### 3. Multi-language Content Management
- **Content Models**: Support both Chinese and English field names
- **URL Generation**: Custom `join_multiple_paths()` for multi-segment URLs
- **Template Context**: `inject_locale()` provides language data to all templates

## Critical Development Notes

### Environment Variables (Required)
```bash
# Database (REQUIRED for production)
MONGO_URI=mongodb://user:password@host:port/database

# Admin credentials (REQUIRED - change defaults!)
ADMIN_USERNAME=superadmin
ADMIN_PASSWORD=your_secure_password_here

# R2 Storage (for images)
R2_ENDPOINT_URL=https://...
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
R2_BUCKET_NAME=...

# OpenAI API (for translation)
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1

# Optional
STRIPE_ENDPOINT_SECRET=...
TESTING=0  # Set to 1 for test database
```

### Performance Considerations
- **Server Response Time**: Currently ~3 seconds (major optimization target)
- **Static Assets**: Use preload for CSS, sequential loading for JS
- **Database**: Uses custom sequence counters for auto-incrementing IDs
- **Caching**: Comment system has 300s cache timeout

### Security Features
- **Environment Variables**: All sensitive data moved from hardcoded values
- **Admin Access**: Flask-Admin with custom authentication
- **Content Validation**: XSS protection via bleach library
- **CORS**: Properly configured for API endpoints

## Recent Major Changes

### Theme Toggle & CSS Fix (December 2024)
Fixed critical CSS truncation issue affecting theme toggle and light mode:
- **Root Cause**: Gzip compression was truncating large CSS files (61KB sent, 54KB received)
- **Solution**: Excluded CSS files from Gzip compression in `get_app.py`
- **Theme Toggle**: Now works correctly with sun/moon icon animation
- **Light Mode**: Full light theme support via `[data-theme="light"]` CSS variables
- **Fallback**: Inline CSS added to templates as safety net

### iOS Fullscreen Replacement (July 2024)
Complete rewrite of fullscreen functionality to support iOS Safari limitations:
- Replaced standard `requestFullscreen()` with CSS transform approach
- Added device detection and orientation handling
- Maintained backward compatibility for non-iOS devices

### Comment System Integration
- Full CRUD API with moderation capabilities
- Admin panel integration with batch operations
- Performance optimized with reply limits
- Multi-language comment support

### Security Hardening (December 2024)
- Migrated from hardcoded secrets to environment variables
- Removed all API keys from source code (OpenAI, Stripe, Supabase)
- Added input validation and spam detection
- Implemented proper cache headers

## Template System Notes

### Base Template Structure
- **Main Layout**: `templates/base/head_foot.html`
- **Content Pages**: `templates/web/content.html`, `templates/web/index.html`
- **Asset Loading**: CSS preloading, JS sequential dynamic loading

### Critical Template Dependencies
The game pages rely on specific script loading order:
1. `fullscreen.js` (core fullscreen functionality)
2. `native-fullscreen.js` (browser-specific features)  
3. `game-status-bar.js` (UI integration)

**DO NOT** convert these to standard `<script defer>` tags - use the existing dynamic loading pattern.

## Documentation
Comprehensive documentation available in `doc/` directory:
- **Performance Optimization**: Security-audited optimization plan
- **Comment System**: Technical documentation and usage guide  
- **iOS Fullscreen**: Implementation details and rationale
- **Change Log**: Detailed modification history

## Testing Strategy
- **Functional**: Admin panel, comment system, fullscreen features
- **Performance**: Lighthouse auditing (baseline report available)
- **Cross-platform**: Special attention to iOS Safari compatibility
- **Multi-language**: URL routing and content rendering across all 27 languages