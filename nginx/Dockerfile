# FROM nginx:1.24.0-alpine-slim 

FROM nginx:alpine-slim

WORKDIR /home/app
RUN mkdir -p /home/app && \
    chown -R nginx:nginx /home/app

# supprimer la conf par défaut
RUN rm -f /etc/nginx/conf.d/default.conf

# copier ta conf
COPY nginx.conf /etc/nginx/conf.d/

# dossiers & pid : même user alpine
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

EXPOSE 80 443

# lancer nginx avec l’user alpine
USER nginx
CMD ["nginx", "-g", "daemon off;"]