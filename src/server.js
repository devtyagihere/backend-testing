/**
 * @file server.js
 * @description Server bootstrap entry point.
 * Responsible for:
 *  - Initializing database connections
 *  - Starting the HTTP server on configured PORT
 *  - Handling process lifecycle events (SIGINT, SIGTERM, unhandledRejection, uncaughtException)
 *  - Managing graceful shutdown
 */
