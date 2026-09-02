using Elastic.OpenTelemetry;

var builder = WebApplication.CreateBuilder(args);

// Mandatory: Register EDOT for automatic tracing, metrics, and logs
// This replaces manual TracerProvider/MeterProvider configuration
builder.AddElasticOpenTelemetry();

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();

var app = builder.Build();

app.MapControllers();

// Sample endpoints
app.MapGet("/", () => new { message = "Service .NET instrumenté avec EDOT", timestamp = DateTimeOffset.UtcNow.ToString("o") });
app.MapGet("/health", () => new { status = "healthy" });
app.MapGet("/orders", () => new { orders = new[] { new { id = 1, amount = 99.9 }, new { id = 2, amount = 49.9 } } });
app.MapGet("/orders/{id}", (int id) => new { id, amount = 99.9 });

app.Run();
