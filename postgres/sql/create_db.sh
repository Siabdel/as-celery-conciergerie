#!/bin/bash
## create database
## psql -h 192.168.59.103 -p 49159 -d docker -U docker --password
#
# sudo apt install postgresql postgresql-contrib
# sudo service postgresql restart
# pg_lsclusters 11 main start
# psql -p 5532 -U postgres
# psql -h 0.0.0.0 -U postgres blogrestapidb
# sudo -u postgres psql -c "SELECT version();"
# sudo -u postgres psql

## su - postgres -c "psql -U postgres -p 5532 -f /src/sql/dbcreate.sql;"
su - postgres -c "psql -U postgres  -f /src/sql/dbcreate.sql;"

