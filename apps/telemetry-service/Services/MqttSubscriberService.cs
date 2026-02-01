using System.Text;
using System.Text.Json;
using MQTTnet;
using MQTTnet.Client;
using TelemetryService.Data;
using TelemetryService.Models;

namespace TelemetryService.Services;

public class MqttSubscriberService : IHostedService, IDisposable
{
    private readonly ILogger<MqttSubscriberService> _logger;
    private readonly IServiceProvider _serviceProvider;
    private IMqttClient? _mqttClient;

    public MqttSubscriberService(ILogger<MqttSubscriberService> logger, IServiceProvider serviceProvider)
    {
        _logger = logger;
        _serviceProvider = serviceProvider;
    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        var broker = Environment.GetEnvironmentVariable("MQTT_BROKER") ?? "localhost";
        var port = int.Parse(Environment.GetEnvironmentVariable("MQTT_PORT") ?? "1883");

        var factory = new MqttFactory();
        _mqttClient = factory.CreateMqttClient();

        var options = new MqttClientOptionsBuilder()
            .WithTcpServer(broker, port)
            .WithClientId("telemetry-service")
            .WithCleanSession()
            .Build();

        _mqttClient.ApplicationMessageReceivedAsync += HandleMessageAsync;
        _mqttClient.ConnectedAsync += async e =>
        {
            _logger.LogInformation("Connected to MQTT broker");
            
            await _mqttClient.SubscribeAsync(new MqttTopicFilterBuilder()
                .WithTopic("devices/+/telemetry")
                .Build(), cancellationToken);
            
            _logger.LogInformation("Subscribed to devices/+/telemetry");
        };

        _mqttClient.DisconnectedAsync += async e =>
        {
            _logger.LogWarning("Disconnected from MQTT broker: {Reason}", e.Reason);
            await Task.Delay(TimeSpan.FromSeconds(5), cancellationToken);
            
            try
            {
                await _mqttClient.ConnectAsync(options, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to reconnect to MQTT broker");
            }
        };

        try
        {
            await _mqttClient.ConnectAsync(options, cancellationToken);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to connect to MQTT broker");
        }
    }

    private async Task HandleMessageAsync(MqttApplicationMessageReceivedEventArgs e)
    {
        try
        {
            var topic = e.ApplicationMessage.Topic;
            var payload = Encoding.UTF8.GetString(e.ApplicationMessage.PayloadSegment);
            
            _logger.LogInformation("Received message on topic {Topic}: {Payload}", topic, payload);

            var message = JsonSerializer.Deserialize<TelemetryMessage>(payload, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (message != null)
            {
                using var scope = _serviceProvider.CreateScope();
                var db = scope.ServiceProvider.GetRequiredService<TelemetryDbContext>();

                var record = new TelemetryRecord
                {
                    DeviceId = message.DeviceId,
                    Type = message.Type,
                    Value = message.Value,
                    Unit = message.Unit,
                    Timestamp = message.Timestamp,
                    CreatedAt = DateTime.UtcNow
                };

                db.Telemetry.Add(record);
                await db.SaveChangesAsync();
                
                _logger.LogInformation("Saved telemetry record for device {DeviceId}", message.DeviceId);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing MQTT message");
        }
    }

    public async Task StopAsync(CancellationToken cancellationToken)
    {
        if (_mqttClient?.IsConnected == true)
        {
            await _mqttClient.DisconnectAsync(cancellationToken: cancellationToken);
        }
    }

    public void Dispose()
    {
        _mqttClient?.Dispose();
    }
}
