using roku-voice-assistant;


var builder = Host.CreateApplicationBuilder(args);
builder.Services.AddHostedService<PythonFlaskLauncher>();
builder.Services.AddHostedService<Worker>();

var host = builder.Build();
host.Run();
