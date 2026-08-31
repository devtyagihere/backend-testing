# Production Backend Architecture

A modular, scalable, and clean backend architecture template following standard Layered & Clean Architecture principles.

---

## 🏛️ Architecture Overview

The codebase is organized into distinct layers to ensure separation of concerns, testability, and maintainability:

`
src/
├── config/         # Centralized configuration (Environment, Database, Logger)
├── constants/      # App-wide constants (HTTP Status Codes, Messages)
├── controllers/    # HTTP Request & Response handlers (No business logic)
├── middlewares/    # Custom middlewares (Auth, Validation, Error Handling, Rate Limiting)
├── models/         # Database schemas / entity definitions
├── repositories/   # Data Access Layer (Direct database queries & persistence)
├── routes/         # API Endpoint definitions & route groupings
├── services/       # Core Business Logic Layer (Framework-agnostic logic)
├── types/          # Global TypeScript / JSDoc type definitions
├── utils/          # Shared utility functions, error classes, & response envelopes
├── validations/    # Request payload validation schemas (Zod / Joi / Yup)
├── app.js          # App initialization & middleware pipeline
└── server.js       # Server bootstrap, lifecycle & graceful shutdown
`

---

## 📂 Project Directory Structure

`plaintext
backend/
├── .env.example                         # Template for environment variables
├── .gitignore                           # Git ignore rules
├── Dockerfile                           # Container definition
├── docker-compose.yml                   # Multi-container local development setup
├── README.md                            # Project documentation
├── docs/                                # Technical documentation
│   ├── architecture.md                  # Detailed architectural guidelines & diagrams
│   └── api.md                           # API contract & endpoints documentation
├── scripts/                             # Utility scripts (Setup, Deployment, Migrations)
│   ├── setup.sh
│   └── deploy.sh
├── src/                                 # Source code
│   ├── config/                          # App configuration
│   │   ├── database.config.js
│   │   ├── env.config.js
│   │   ├── logger.config.js
│   │   └── index.js
│   ├── constants/                       # Constants & Enums
│   │   ├── httpStatusCodes.js
│   │   ├── responseMessages.js
│   │   └── index.js
│   ├── controllers/                     # Controllers Layer
│   │   ├── auth.controller.js
│   │   ├── user.controller.js
│   │   └── index.js
│   ├── middlewares/                     # Express / App Middlewares
│   │   ├── auth.middleware.js
│   │   ├── error.middleware.js
│   │   ├── logger.middleware.js
│   │   ├── rateLimiter.middleware.js
│   │   ├── validate.middleware.js
│   │   └── index.js
│   ├── models/                          # Data Models & Schemas
│   │   ├── user.model.js
│   │   ├── session.model.js
│   │   └── index.js
│   ├── repositories/                    # Data Access / Repository Layer
│   │   ├── base.repository.js
│   │   ├── user.repository.js
│   │   └── index.js
│   ├── routes/                          # Routing Layer
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.routes.js
│   │   │       ├── user.routes.js
│   │   │       └── index.routes.js
│   │   ├── health.routes.js
│   │   └── index.routes.js
│   ├── services/                        # Business Logic Layer
│   │   ├── auth.service.js
│   │   ├── user.service.js
│   │   ├── token.service.js
│   │   └── index.js
│   ├── types/                           # Type definitions
│   │   └── index.d.ts
│   ├── utils/                           # Helper functions & Utilities
│   │   ├── apiError.js
│   │   ├── apiResponse.js
│   │   ├── asyncHandler.js
│   │   ├── logger.js
│   │   └── index.js
│   ├── validations/                     # Request Validation Schemas
│   │   ├── auth.validation.js
│   │   ├── user.validation.js
│   │   └── index.js
│   ├── app.js                           # App entry
│   └── server.js                        # HTTP server runner
└── tests/                               # Test suite
    ├── setup.js                         # Global test setup
    ├── integration/                     # Integration tests
    │   ├── auth.test.js
    │   └── health.test.js
    └── unit/                            # Unit tests
        ├── controllers/
        │   └── auth.controller.test.js
        ├── services/
        │   └── auth.service.test.js
        └── utils/
            └── apiResponse.test.js
`

---

## 🔄 Request / Response Flow

`
[Client Request]
       │
       ▼
[Middlewares] (Rate Limiter, CORS, Body Parser, Auth, Validation)
       │
       ▼
[Routes] (Matches URL route & forwards to Controller)
       │
       ▼
[Controllers] (Parses HTTP parameters & delegates to Service)
       │
       ▼
[Services] (Executes business logic, transactions, rules)
       │
       ▼
[Repositories] (Direct DB Queries / ORM / ODM operations)
       │
       ▼
[Database / External APIs]
       │
       ▼
[Controllers] (Formats response via ApiResponse utility)
       │
       ▼
[Global Error Middleware] (Catches unhandled exceptions via ApiError)
       │
       ▼
[Client Response]
`

---

## 🚀 Getting Started

1. **Clone the repository:**
   `ash
   git clone https://github.com/devtyagihere/backend-testing.git
   cd backend-testing
   `

2. **Configure Environment:**
   `ash
   cp .env.example .env
   `

3. **Install Dependencies & Start:**
   Use your preferred package manager or runtime.
