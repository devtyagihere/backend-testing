# Dockerfile skeleton for Backend Application
# ----------------------------------------------------
# Multi-stage build setup for production deployments

# Stage 1: Build & Dependencies
# FROM node:20-alpine AS builder
# WORKDIR /app
# COPY package*.json ./
# RUN npm ci
# COPY . .

# Stage 2: Production Runtime
# FROM node:20-alpine AS runner
# WORKDIR /app
# ENV NODE_ENV=production
# COPY --from=builder /app ./
# EXPOSE 5000
# CMD ["node", "src/server.js"]
