FROM nginx:alpine

# Copy the frontend files to NGINX HTML directory
COPY . /usr/share/nginx/html

# Define environment variables for dynamic resolution
ENV BACKEND_HOST=fiscal-finance-backend-svc
ENV NGINX_ENVSUBST_FILTER=BACKEND_HOST

# Copy custom NGINX configuration as a template for envsubst
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
