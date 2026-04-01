package models

import (
	"time"
)

type Device struct {
	ID         int       `json:"id"`
	DeviceID   string    `json:"device_id"`
	UserID     string    `json:"user_id"`
	Name       string    `json:"name"`
	DeviceType string    `json:"device_type"`
	Status     string    `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
	UpdatedAt  time.Time `json:"updated_at"`
}

type DeviceCreate struct {
	DeviceID   string `json:"device_id" binding:"required"`
	Name       string `json:"name" binding:"required"`
	DeviceType string `json:"device_type" binding:"required"`
}

type DeviceResponse struct {
	DeviceID   string    `json:"device_id"`
	Name       string    `json:"name"`
	DeviceType string    `json:"device_type"`
	Status     string    `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
}

type DeviceRegisteredEvent struct {
	Event      string    `json:"event"`
	DeviceID   string    `json:"device_id"`
	UserID     string    `json:"user_id"`
	DeviceType string    `json:"device_type"`
	Name       string    `json:"name"`
	Timestamp  time.Time `json:"timestamp"`
}
