# Backend Architecture Documentation

## Core Principles

1. **Separation of Concerns**: Each directory/layer has one single responsibility.
2. **Layered Isolation**:
   - Controllers never query the database directly.
   - Services do not touch HTTP objects (eq, es).
   - Repositories handle all data persistence and retrieval.
3. **Centralized Error Handling**: All operational errors throw instances of ApiError which are caught by error.middleware.js.
4. **Standardized Responses**: Responses are wrapped in a unified structure using ApiResponse.
