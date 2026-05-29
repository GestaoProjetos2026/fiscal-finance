FROM nginx:alpine

# Copy the frontend files to NGINX HTML directory
COPY . /usr/share/nginx/html

# Define environment variables for dynamic resolution
ENV BACKEND_HOST=fiscal-finance-backend-svc
ENV DNS_RESOLVER="10.43.0.10 10.96.0.10 kube-dns.kube-system.svc.cluster.local"
ENV NGINX_ENVSUBST_FILTER="BACKEND_HOST DNS_RESOLVER"

# Copy custom NGINX configuration as a template for envsubst
COPY nginx.conf /etc/nginx/templates/default.conf.template

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
