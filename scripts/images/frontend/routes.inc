location /api/ {
    proxy_pass http://datamate-gateway:8080/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location /chat {
    proxy_pass http://datamate-gateway:8080/chat;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    proxy_intercept_errors on;
    error_page 500 501 502 503 504 =200 @static_fallback;
}

location /_next {
    proxy_pass http://datamate-gateway:8080/_next;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location /deer-flow-backend {
    proxy_pass http://datamate-gateway:8080/deer-flow-backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

location @static_fallback {
    root   /opt/frontend/statics;
    try_files $uri $uri/ /index.html;
}

location / {
    root   /opt/frontend/statics;
    try_files $uri $uri/ /index.html;
}