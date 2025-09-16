su - postgres  -c pg_dump conciergeriedb  | gzip > ~/backup/postgres/db_save.sql.gz
su - postgres  -c pg_dump conciergeriedb  | gzip > ~/backup/postgres/conciergeriebd_save.sql.gz
