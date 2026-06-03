using roku_voice_assistant;

var builder = Host.CreateApplicationBuilder(args);
// Monitor for the Flask process so other services can report health
builder.Services.AddSingleton<FlaskProcessMonitor>();
builder.Services.AddHostedService<PythonFlaskLauncher>();
builder.Services.AddHostedService<Worker>();
// Small HTTP health listener that reports Flask backend status
builder.Services.AddHostedService<HealthHttpListener>();

var host = builder.Build();
host.Run();
