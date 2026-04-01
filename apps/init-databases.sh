#!/bin/bash
set -e

echo "Creating databases..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE smarthome;
    CREATE DATABASE telemetry;
    CREATE DATABASE command;
EOSQL

echo "Initializing smarthome database..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "smarthome" <<-EOSQL
    CREATE TABLE IF NOT EXISTS sensors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        location VARCHAR(100) NOT NULL,
        value FLOAT DEFAULT 0,
        unit VARCHAR(20),
        status VARCHAR(20) NOT NULL DEFAULT 'inactive',
        last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_sensors_type ON sensors(type);
    CREATE INDEX IF NOT EXISTS idx_sensors_location ON sensors(location);
    CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);

    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);

    CREATE TABLE IF NOT EXISTS devices (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(100) UNIQUE NOT NULL,
        user_id VARCHAR(100) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        device_type VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'offline',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
    CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id);
    CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
EOSQL

echo "Initializing telemetry database..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "telemetry" <<-EOSQL
    CREATE TABLE IF NOT EXISTS telemetry (
        id SERIAL PRIMARY KEY,
        device_id VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        value DOUBLE PRECISION NOT NULL,
        unit VARCHAR(20),
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_telemetry_device_id ON telemetry(device_id);
    CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);
    CREATE INDEX IF NOT EXISTS idx_telemetry_device_timestamp ON telemetry(device_id, timestamp DESC);
EOSQL

echo "Initializing command database..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "command" <<-EOSQL
    CREATE TABLE IF NOT EXISTS commands (
        id SERIAL PRIMARY KEY,
        command_id VARCHAR(100) UNIQUE NOT NULL,
        device_id VARCHAR(100) NOT NULL,
        action VARCHAR(100) NOT NULL,
        params JSONB,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        executed_at TIMESTAMP WITH TIME ZONE
    );

    CREATE INDEX IF NOT EXISTS idx_commands_device_id ON commands(device_id);
    CREATE INDEX IF NOT EXISTS idx_commands_status ON commands(status);
    CREATE INDEX IF NOT EXISTS idx_commands_command_id ON commands(command_id);
EOSQL

echo "Database initialization complete!"
