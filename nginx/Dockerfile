# FROM nginx:1.24.0-alpine-slim 
FROM nginx:alpine-slim 

RUN rm /etc/nginx/conf.d/default.conf
## 

COPY nginx.conf /etc/nginx/conf.d


FROM nginx:1.24.0-alpine-slim 

RUN rm /etc/nginx/conf.d/default.conf

# Créer un utilisateur non-root
RUN adduser -D -H -u 1000 -s /sbin/nologin www-data -G www-data

# Copier la configuration Nginx
COPY nginx.conf /etc/nginx/conf.d/

# Ajuster les permissions
RUN chown -R www-data:www-data /var/cache/nginx /var/log/nginx /etc/nginx/conf.d
RUN touch /var/run/nginx.pid && chown -R www-data:www-data /var/run/nginx.pid

# Exposer les ports
EXPOSE 80 443

# Définir l'utilisateur non-root
USER www-data

# Démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]