using Microsoft.EntityFrameworkCore;
using Microsoft.OpenApi.Models;
using TelemetryService.Data;
using TelemetryService.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<TelemetryDbContext>(options =>
    options.UseNpgsql(Environment.GetEnvironmentVariable("DATABASE_URL") 
        ?? "Host=localhost;Database=telemetry;Username=postgres;Password=postgres"));

builder.Services.AddSingleton<MqttSubscriberService>();
builder.Services.AddHostedService(sp => sp.GetRequiredService<MqttSubscriberService>());

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Telemetry Service API",
        Version = "v1",
        Description = "API для работы с телеметрией устройств"
    });
});

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<TelemetryDbContext>();
    db.Database.EnsureCreated();
}

app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "Telemetry Service API v1");
    c.RoutePrefix = string.Empty;
});

app.MapGet("/health", () => Results.Ok(new { status = "ok", service = "telemetry-service" }))
    .WithName("HealthCheck")
    .WithTags("Health");

app.MapGet("/api/v1/telemetry", async (TelemetryDbContext db, string? deviceId, DateTime? from, DateTime? to) =>
{
    var query = db.Telemetry.AsQueryable();
    
    if (!string.IsNullOrEmpty(deviceId))
        query = query.Where(t => t.DeviceId == deviceId);
    
    if (from.HasValue)
        query = query.Where(t => t.Timestamp >= from.Value);
    
    if (to.HasValue)
        query = query.Where(t => t.Timestamp <= to.Value);
    
    var result = await query.OrderByDescending(t => t.Timestamp).Take(100).ToListAsync();
    return Results.Ok(result);
})
.WithName("GetTelemetry")
.WithTags("Telemetry")
.WithOpenApi(operation =>
{
    operation.Summary = "Get telemetry data";
    operation.Description = "Get telemetry data with optional filters";
    return operation;
})
.Produces<List<TelemetryService.Models.TelemetryRecord>>(StatusCodes.Status200OK);

app.MapGet("/api/v1/telemetry/{deviceId}/latest", async (TelemetryDbContext db, string deviceId) =>
{
    var record = await db.Telemetry
        .Where(t => t.DeviceId == deviceId)
        .OrderByDescending(t => t.Timestamp)
        .FirstOrDefaultAsync();
    
    if (record == null)
        return Results.NotFound(new { error = "No telemetry found for device" });
    
    return Results.Ok(record);
})
.WithName("GetLatestTelemetry")
.WithTags("Telemetry")
.WithOpenApi(operation =>
{
    operation.Summary = "Get latest telemetry";
    operation.Description = "Get the most recent telemetry record for a device";
    return operation;
})
.Produces<TelemetryService.Models.TelemetryRecord>(StatusCodes.Status200OK)
.Produces(StatusCodes.Status404NotFound);

app.MapPost("/api/v1/telemetry", async (TelemetryDbContext db, TelemetryService.Models.TelemetryCreate telemetry) =>
{
    var record = new TelemetryService.Models.TelemetryRecord
    {
        DeviceId = telemetry.DeviceId,
        Type = telemetry.Type,
        Value = telemetry.Value,
        Unit = telemetry.Unit,
        Timestamp = telemetry.Timestamp ?? DateTime.UtcNow,
        CreatedAt = DateTime.UtcNow
    };
    
    db.Telemetry.Add(record);
    await db.SaveChangesAsync();
    
    return Results.Created($"/api/v1/telemetry/{record.Id}", record);
})
.WithName("CreateTelemetry")
.WithTags("Telemetry")
.WithOpenApi(operation =>
{
    operation.Summary = "Create telemetry record";
    operation.Description = "Manually create a telemetry record";
    return operation;
})
.Produces<TelemetryService.Models.TelemetryRecord>(StatusCodes.Status201Created)
.Produces(StatusCodes.Status400BadRequest);

app.Run();
