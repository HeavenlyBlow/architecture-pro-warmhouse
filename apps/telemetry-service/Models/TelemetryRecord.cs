using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json.Serialization;

namespace TelemetryService.Models;

[Table("telemetry")]
public class TelemetryRecord
{
    [Key]
    [Column("id")]
    public int Id { get; set; }
    
    [Required]
    [Column("device_id")]
    [JsonPropertyName("device_id")]
    public string DeviceId { get; set; } = string.Empty;
    
    [Required]
    [Column("type")]
    public string Type { get; set; } = string.Empty;
    
    [Column("value")]
    public double Value { get; set; }
    
    [Column("unit")]
    public string? Unit { get; set; }
    
    [Column("timestamp")]
    public DateTime Timestamp { get; set; }
    
    [Column("created_at")]
    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; }
}

public class TelemetryCreate
{
    [JsonPropertyName("deviceId")]
    public string DeviceId { get; set; } = string.Empty;
    public string Type { get; set; } = string.Empty;
    public double Value { get; set; }
    public string? Unit { get; set; }
    public DateTime? Timestamp { get; set; }
}

public class TelemetryMessage
{
    [JsonPropertyName("device_id")]
    public string DeviceId { get; set; } = string.Empty;
    
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;
    
    [JsonPropertyName("value")]
    public double Value { get; set; }
    
    [JsonPropertyName("unit")]
    public string? Unit { get; set; }
    
    [JsonPropertyName("timestamp")]
    public DateTime Timestamp { get; set; }
}
