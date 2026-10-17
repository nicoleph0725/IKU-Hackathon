-- Separate database for pytest so tests never touch dev data.
CREATE DATABASE studycafe_test OWNER studycafe;
\c studycafe_test
CREATE EXTENSION IF NOT EXISTS timescaledb;
