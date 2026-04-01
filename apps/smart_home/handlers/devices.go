package handlers

import (
	"log"
	"net/http"

	"smarthome/db"
	"smarthome/models"
	"smarthome/services"

	"github.com/gin-gonic/gin"
)

type DeviceHandler struct {
	DB            *db.DB
	MQTTPublisher *services.MQTTPublisher
}

func NewDeviceHandler(database *db.DB, mqttPublisher *services.MQTTPublisher) *DeviceHandler {
	return &DeviceHandler{
		DB:            database,
		MQTTPublisher: mqttPublisher,
	}
}

func (h *DeviceHandler) RegisterRoutes(router *gin.RouterGroup) {
	devices := router.Group("/devices")
	devices.Use(AuthMiddleware())
	{
		devices.GET("", h.GetDevices)
		devices.POST("", h.CreateDevice)
		devices.DELETE("/:id", h.DeleteDevice)
	}
}

// GetDevices godoc
// @Summary Get user devices
// @Description Get all devices for authenticated user
// @Tags devices
// @Accept json
// @Produce json
// @Security BearerAuth
// @Success 200 {array} models.DeviceResponse
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/v2/devices [get]
func (h *DeviceHandler) GetDevices(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	devices, err := h.DB.GetDevicesByUserID(c.Request.Context(), userID.(string))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	response := make([]models.DeviceResponse, len(devices))
	for i, d := range devices {
		response[i] = models.DeviceResponse{
			DeviceID:   d.DeviceID,
			Name:       d.Name,
			DeviceType: d.DeviceType,
			Status:     d.Status,
			CreatedAt:  d.CreatedAt,
		}
	}

	c.JSON(http.StatusOK, response)
}

// CreateDevice godoc
// @Summary Create new device
// @Description Create a new device for authenticated user
// @Tags devices
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param device body models.DeviceCreate true "Device data"
// @Success 201 {object} models.DeviceResponse
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/v2/devices [post]
func (h *DeviceHandler) CreateDevice(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	var req models.DeviceCreate
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	device, err := h.DB.CreateDevice(c.Request.Context(), userID.(string), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	if h.MQTTPublisher != nil {
		if err := h.MQTTPublisher.PublishDevicePaired(
			device.DeviceID,
			device.UserID,
			device.DeviceType,
			device.Name,
		); err != nil {
			log.Printf("Failed to publish device paired event: %v", err)
		}
	}

	response := models.DeviceResponse{
		DeviceID:   device.DeviceID,
		Name:       device.Name,
		DeviceType: device.DeviceType,
		Status:     device.Status,
		CreatedAt:  device.CreatedAt,
	}

	c.JSON(http.StatusCreated, response)
}

// DeleteDevice godoc
// @Summary Delete device
// @Description Delete a device by ID
// @Tags devices
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Device ID"
// @Success 200 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /api/v2/devices/{id} [delete]
func (h *DeviceHandler) DeleteDevice(c *gin.Context) {
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	deviceID := c.Param("id")
	if deviceID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "device ID required"})
		return
	}

	err := h.DB.DeleteDevice(c.Request.Context(), deviceID, userID.(string))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "device deleted successfully"})
}
