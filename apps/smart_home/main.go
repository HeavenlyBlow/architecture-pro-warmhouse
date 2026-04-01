package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"smarthome/db"
	"smarthome/handlers"
	"smarthome/services"

	_ "smarthome/docs"

	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
)

// @title SmartHome API
// @version 2.0
// @description SmartHome Platform API - управление умным домом
// @host localhost:8080
// @BasePath /
// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization

func main() {
	dbURL := getEnv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/smarthome")
	database, err := db.New(dbURL)
	if err != nil {
		log.Fatalf("Unable to connect to database: %v\n", err)
	}
	defer database.Close()
	log.Println("Connected to database successfully")

	mqttBroker := getEnv("MQTT_BROKER", "localhost:1883")
	var mqttPublisher *services.MQTTPublisher
	mqttPublisher, err = services.NewMQTTPublisher(mqttBroker)
	if err != nil {
		log.Printf("Warning: Failed to connect to MQTT broker: %v\n", err)
	} else {
		defer mqttPublisher.Close()
		log.Printf("Connected to MQTT broker at %s\n", mqttBroker)
	}

	temperatureAPIURL := getEnv("TEMPERATURE_API_URL", "http://temperature-api:8081")
	temperatureService := services.NewTemperatureService(temperatureAPIURL)
	log.Printf("Temperature service initialized with API URL: %s\n", temperatureAPIURL)

	router := gin.Default()

	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "ok",
			"service": "smart-home",
		})
	})

	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	apiV1 := router.Group("/api/v1")
	sensorHandler := handlers.NewSensorHandler(database, temperatureService)
	sensorHandler.RegisterRoutes(apiV1)

	apiV2 := router.Group("/api/v2")
	userHandler := handlers.NewUserHandler(database)
	userHandler.RegisterRoutes(apiV2)

	deviceHandler := handlers.NewDeviceHandler(database, mqttPublisher)
	deviceHandler.RegisterRoutes(apiV2)

	srv := &http.Server{
		Addr:    getEnv("PORT", ":8081"),
		Handler: router,
	}

	go func() {
		log.Printf("Server starting on %s\n", srv.Addr)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Failed to start server: %v\n", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v\n", err)
	}

	log.Println("Server exited properly")
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}
