CREATE DATABASE conciergeriedb;
ALTER USER postgres WITH PASSWORD 'grutil001';
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE conciergeriedb TO postgres;