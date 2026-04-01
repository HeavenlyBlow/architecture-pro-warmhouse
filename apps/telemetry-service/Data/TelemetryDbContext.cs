using Microsoft.EntityFrameworkCore;
using TelemetryService.Models;

namespace TelemetryService.Data;

public class TelemetryDbContext : DbContext
{
    public TelemetryDbContext(DbContextOptions<TelemetryDbContext> options) : base(options)
    {
    }
    
    public DbSet<TelemetryRecord> Telemetry { get; set; }
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<TelemetryRecord>(entity =>
        {
            entity.ToTable("telemetry");
            entity.HasIndex(e => e.DeviceId);
            entity.HasIndex(e => e.Timestamp);
        });
    }
}
