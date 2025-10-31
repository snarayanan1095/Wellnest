# Multi-stage build for React dashboard

# Stage 1: Build the React app
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json ./


RUN rm -rf node_modules package-lock.json && \
    npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]