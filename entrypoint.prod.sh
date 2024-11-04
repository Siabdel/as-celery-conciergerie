#! /bin/sh
if [ " $ DATABASE " = "postgres" ]
    then
        echo "En attente de postgres ..."
        while ! nc -z $ SQL_HOST $ SQL_PORT ; do
            sleep 0 .1
        done
    echo
    "PostgreSQL a démarré"
fi
#python3 manage.py flush --no-input
python3 manage.py migrate
rm -r staticfiles/*
python3 manage.py collectstatic --noinput
## creation du superuser abdel et admin
echo "from django.contrib.auth.models import User; User.objects.create_superuser(username='admin', password='grutil001', email='admin@atlass.fr')" | python3 manage.py shell
echo "from django.contrib.auth.models import User; User.objects.create_superuser(username='abdel', password='grutil001', email='abdel@atlass.fr')" | python3 manage.py shell


exec
"$@"