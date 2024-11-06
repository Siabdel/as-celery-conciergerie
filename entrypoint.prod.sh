#!/bin/bash

# Ajoutez un shebang et définissez des options de shell :
set -euo pipefail

# Vérification de la disponibilité de la base de données avant de lancer les migrations 

until pg_isready -h $SQL_HOST -p $SQL_PORT -U $SQL_USER
do
  echo "Waiting for database..."
  sleep 2
done

#python3 manage.py flush --no-input
# python manage.py migrate --noinput
# rm -r staticfiles/*
# python manage.py collectstatic --no-input --clear

## creation du superuser abdel et admin
# echo "from django.contrib.auth.models import User; User.objects.create_superuser(username='admin', password='grutil001', email='admin@atlass.fr')" | python3 manage.py shell
# echo "from django.contrib.auth.models import User; User.objects.create_superuser(username='abdel', password='grutil001', email='abdel@atlass.fr')" | python3 manage.py shell


exec
"$@"