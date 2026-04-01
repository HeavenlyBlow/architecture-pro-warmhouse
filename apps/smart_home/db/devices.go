package db

import (
	"context"
	"errors"
	"fmt"
	"time"

	"smarthome/models"
)

func (db *DB) CreateDevice(ctx context.Context, userID string, d models.DeviceCreate) (models.Device, error) {
	now := time.Now()

	query := `
		INSERT INTO devices (device_id, user_id, name, device_type, status, created_at, updated_at)
		VALUES ($1, $2, $3, $4, 'online', $5, $5)
		RETURNING id, device_id, user_id, name, device_type, status, created_at, updated_at
	`

	var device models.Device
	err := db.Pool.QueryRow(ctx, query, d.DeviceID, userID, d.Name, d.DeviceType, now).Scan(
		&device.ID,
		&device.DeviceID,
		&device.UserID,
		&device.Name,
		&device.DeviceType,
		&device.Status,
		&device.CreatedAt,
		&device.UpdatedAt,
	)
	if err != nil {
		return models.Device{}, fmt.Errorf("failed to pair device: %w", err)
	}

	return device, nil
}

func (db *DB) GetDevicesByUserID(ctx context.Context, userID string) ([]models.Device, error) {
	query := `
		SELECT id, device_id, user_id, name, device_type, status, created_at, updated_at
		FROM devices
		WHERE user_id = $1
		ORDER BY created_at DESC
	`

	rows, err := db.Pool.Query(ctx, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to query devices: %w", err)
	}
	defer rows.Close()

	var devices []models.Device
	for rows.Next() {
		var d models.Device
		err := rows.Scan(
			&d.ID,
			&d.DeviceID,
			&d.UserID,
			&d.Name,
			&d.DeviceType,
			&d.Status,
			&d.CreatedAt,
			&d.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan device: %w", err)
		}
		devices = append(devices, d)
	}

	return devices, nil
}

func (db *DB) GetDeviceByID(ctx context.Context, deviceID string) (models.Device, error) {
	query := `
		SELECT id, device_id, user_id, name, device_type, status, created_at, updated_at
		FROM devices
		WHERE device_id = $1
	`

	var device models.Device
	err := db.Pool.QueryRow(ctx, query, deviceID).Scan(
		&device.ID,
		&device.DeviceID,
		&device.UserID,
		&device.Name,
		&device.DeviceType,
		&device.Status,
		&device.CreatedAt,
		&device.UpdatedAt,
	)
	if err != nil {
		return models.Device{}, fmt.Errorf("device not found: %w", err)
	}

	return device, nil
}

func (db *DB) DeleteDevice(ctx context.Context, deviceID, userID string) error {
	query := `DELETE FROM devices WHERE device_id = $1 AND user_id = $2`

	result, err := db.Pool.Exec(ctx, query, deviceID, userID)
	if err != nil {
		return fmt.Errorf("failed to delete device: %w", err)
	}

	if result.RowsAffected() == 0 {
		return errors.New("device not found or access denied")
	}

	return nil
}
