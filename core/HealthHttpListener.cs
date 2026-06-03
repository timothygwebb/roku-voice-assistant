using System.Net;
using System.Text;

namespace roku_voice_assistant
{
    public class HealthHttpListener : BackgroundService
    {
        private readonly FlaskProcessMonitor _monitor;
        private readonly ILogger<HealthHttpListener> _logger;
        private HttpListener? _listener;

        public HealthHttpListener(FlaskProcessMonitor monitor, ILogger<HealthHttpListener> logger)
        {
            _monitor = monitor;
            _logger = logger;
        }

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:9090/health/");
            try
            {
                _listener.Start();
            }
            catch (HttpListenerException ex)
            {
                _logger.LogWarning(ex, "HealthHttpListener failed to start. Is the port already in use?");
                return;
            }

            while (!stoppingToken.IsCancellationRequested)
            {
                try
                {
                    var ctx = await _listener.GetContextAsync();
                    var response = ctx.Response;

                    if (ctx.Request.HttpMethod == "GET")
                    {
                        var running = _monitor.IsRunning();
                        var pid = _monitor.GetPid();
                        var start = _monitor.StartTime?.ToString("o");
                        var obj = new { status = running ? "running" : "stopped", pid = pid, startTime = start };
                        var json = System.Text.Json.JsonSerializer.Serialize(obj);
                        var data = Encoding.UTF8.GetBytes(json);
                        response.ContentType = "application/json";
                        response.ContentLength64 = data.Length;
                        await response.OutputStream.WriteAsync(data, 0, data.Length, stoppingToken);
                        response.StatusCode = 200;
                    }
                    else
                    {
                        response.StatusCode = 405;
                    }

                    response.OutputStream.Close();
                }
                catch (Exception ex)
                {
                    _logger.LogDebug(ex, "Health listener loop error");
                }
            }

            _listener.Stop();
            _listener.Close();
        }
    }
}
