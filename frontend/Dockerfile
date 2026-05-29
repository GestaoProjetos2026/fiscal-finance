FROM nginx:alpine

# Copy the frontend files to NGINX HTML directory
COPY . /usr/share/nginx/html

# Copy custom NGINX configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
