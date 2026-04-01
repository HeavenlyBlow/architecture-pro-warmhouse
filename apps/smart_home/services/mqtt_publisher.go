package services

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

type MQTTPublisher struct {
	client mqtt.Client
}

func NewMQTTPublisher(broker string) (*MQTTPublisher, error) {
	opts := mqtt.NewClientOptions()
	opts.AddBroker(fmt.Sprintf("tcp://%s", broker))
	opts.SetClientID("smart-home-publisher")
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(5 * time.Second)
	opts.SetOnConnectHandler(func(c mqtt.Client) {
		log.Println("MQTT: Connected to broker")
	})
	opts.SetConnectionLostHandler(func(c mqtt.Client, err error) {
		log.Printf("MQTT: Connection lost: %v", err)
	})

	client := mqtt.NewClient(opts)
	token := client.Connect()
	if token.Wait() && token.Error() != nil {
		return nil, fmt.Errorf("failed to connect to MQTT broker: %w", token.Error())
	}

	return &MQTTPublisher{client: client}, nil
}

func (p *MQTTPublisher) PublishDevicePaired(deviceID, userID, deviceType, name string) error {
	event := map[string]interface{}{
		"event":       "device_paired",
		"device_id":   deviceID,
		"user_id":     userID,
		"device_type": deviceType,
		"name":        name,
		"timestamp":   time.Now().UTC().Format(time.RFC3339),
	}

	payload, err := json.Marshal(event)
	if err != nil {
		return fmt.Errorf("failed to marshal event: %w", err)
	}

	topic := "devices/paired"
	token := p.client.Publish(topic, 1, false, payload)
	if token.Wait() && token.Error() != nil {
		return fmt.Errorf("failed to publish to %s: %w", topic, token.Error())
	}

	log.Printf("MQTT: Published device_paired event for device %s", deviceID)
	return nil
}

func (p *MQTTPublisher) Close() {
	if p.client.IsConnected() {
		p.client.Disconnect(250)
	}
}
