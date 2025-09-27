# find . -path */migrations/*.py -not -name __init__.py -delete
# find . -path */migrations/*.pyc -delete
# find . -name migrations -exec rm -r {} \;
# Si vous êtes encore en développement :
rm -rf */migrations/*.py
python manage.py makemigrations
python manage.py migrate --fake-initial
