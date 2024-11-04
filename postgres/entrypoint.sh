#!/bin/sh
export PGPASSWORD='postgres' 
# psql -h 'server name' -U 'user name' -d 'base name' -c 'command'
# su - postgres -c "export PGPASSWORD='postgres'; psql -h db -U postgres -p 5432 -d postgres -f /src/sql/dbcreate.sql --no-password ;"  
## su - postgres -c "pg_restore -d wagtailmonsitedb /src/wagtailmonsitedump.db --no-password ;";  bash-5.0# 
## su - postgres -c "psql -d postgres -f ./sql/dbcreate.sql --no-password ;"  
# su - postgres  -c "pg_ctl -D /usr/local/var/postgres start"
ls -l sql
#./create_db.sh
su - postgres -c "psql -U postgres  -f /src/sql/dbcreate.sql;"

