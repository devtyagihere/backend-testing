/**
 * @file error.middleware.js
 * @description Global Centralized Error Handling Middleware.
 * Catches all errors forwarded through next(err), formats ApiError into standard JSON responses,
 * and logs unhandled exceptions while preventing sensitive stack trace leaks in production.
 */
