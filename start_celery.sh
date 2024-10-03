## kill old process celery
killall celery
## start  process celery
nohup celery -A conciergerie beat --loglevel=info &
nohup celery -A conciergerie worker --loglevel=info & 
