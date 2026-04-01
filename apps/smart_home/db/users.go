package db

import (
	"context"
	"fmt"
	"time"

	"smarthome/models"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

func (db *DB) CreateUser(ctx context.Context, u models.UserRegister) (models.User, error) {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(u.Password), bcrypt.DefaultCost)
	if err != nil {
		return models.User{}, fmt.Errorf("failed to hash password: %w", err)
	}

	userID := uuid.New().String()
	now := time.Now()

	query := `
		INSERT INTO users (user_id, email, password_hash, name, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $5)
		RETURNING id, user_id, email, password_hash, name, created_at, updated_at
	`

	var user models.User
	err = db.Pool.QueryRow(ctx, query, userID, u.Email, string(hashedPassword), u.Name, now).Scan(
		&user.ID,
		&user.UserID,
		&user.Email,
		&user.PasswordHash,
		&user.Name,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return models.User{}, fmt.Errorf("failed to create user: %w", err)
	}

	return user, nil
}

func (db *DB) GetUserByEmail(ctx context.Context, email string) (models.User, error) {
	query := `
		SELECT id, user_id, email, password_hash, name, created_at, updated_at
		FROM users
		WHERE email = $1
	`

	var user models.User
	err := db.Pool.QueryRow(ctx, query, email).Scan(
		&user.ID,
		&user.UserID,
		&user.Email,
		&user.PasswordHash,
		&user.Name,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return models.User{}, fmt.Errorf("user not found: %w", err)
	}

	return user, nil
}

func (db *DB) GetUserByID(ctx context.Context, userID string) (models.User, error) {
	query := `
		SELECT id, user_id, email, password_hash, name, created_at, updated_at
		FROM users
		WHERE user_id = $1
	`

	var user models.User
	err := db.Pool.QueryRow(ctx, query, userID).Scan(
		&user.ID,
		&user.UserID,
		&user.Email,
		&user.PasswordHash,
		&user.Name,
		&user.CreatedAt,
		&user.UpdatedAt,
	)
	if err != nil {
		return models.User{}, fmt.Errorf("user not found: %w", err)
	}

	return user, nil
}

func (db *DB) ValidatePassword(hashedPassword, password string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
	return err == nil
}
