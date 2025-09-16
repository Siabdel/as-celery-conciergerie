sudo docker exec -i conciergerie_db pg_dump -U postgres postgres | gzip > ~/backup/postgres/db_save.sql.gz
