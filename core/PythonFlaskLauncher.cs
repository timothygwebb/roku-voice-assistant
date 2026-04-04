using System.Diagnostics;
using System.Runtime.InteropServices;

namespace roku_voice_assistant
{
    public class PythonFlaskLauncher(ILogger<PythonFlaskLauncher> logger) : BackgroundService
    {
        private Process? _flaskProcess;
        private readonly ILogger<PythonFlaskLauncher> _logger = logger;

        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            var pythonExe = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "python" : "python3";
            var scriptPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "mobile_app", "app.py");
            scriptPath = Path.GetFullPath(scriptPath);

            var psi = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = $"\"{scriptPath}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = Path.GetDirectoryName(scriptPath) ?? "."
            };

            if (_logger.IsEnabled(LogLevel.Information))
            {
                _logger.LogInformation("Starting Flask backend: {PythonExe} {Arguments}", pythonExe, psi.Arguments);
            }

            _flaskProcess = Process.Start(psi);

            if (_flaskProcess != null)
            {
                _flaskProcess.OutputDataReceived += (s, e) => 
                { 
                    if (!string.IsNullOrWhiteSpace(e.Data)) 
                    {
                        if (_logger.IsEnabled(LogLevel.Information))
                        {
                            _logger.LogInformation("Flask Output: {Data}", e.Data); 
                        }
                    } 
                };
                _flaskProcess.ErrorDataReceived += (s, e) => 
                { 
                    if (!string.IsNullOrWhiteSpace(e.Data)) 
                    {
                        if (e.Data.Contains("error", StringComparison.OrdinalIgnoreCase) || e.Data.Contains("fail", StringComparison.OrdinalIgnoreCase))
                        {
                            _logger.LogError("Flask Error: {Data}", e.Data);
                        }
                        else if (e.Data.Contains("warning", StringComparison.OrdinalIgnoreCase))
                        {
                            _logger.LogWarning("Flask Warning: {Data}", e.Data);
                        }
                        else if (_logger.IsEnabled(LogLevel.Information))
                        {
                            _logger.LogInformation("Flask Log: {Data}", e.Data);
                        }
                    } 
                };
                _flaskProcess.BeginOutputReadLine();
                _flaskProcess.BeginErrorReadLine();
            }

            // Open the browser to the remote control page (http://localhost:5000/)
            try
            {
                string url = "http://localhost:5000/";
                if (_logger.IsEnabled(LogLevel.Information))
                {
                    _logger.LogInformation("Opening browser to {Url}", url);
                }
                try
                {
                    if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                        Process.Start(new ProcessStartInfo("cmd", $"/c start {url}") { CreateNoWindow = true });
                    else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                        Process.Start("xdg-open", url);
                    else if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                        Process.Start("open", url);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning("Could not open browser: {Message}", ex.Message);
                }

                // Wait until cancellation
                await Task.Delay(Timeout.Infinite, stoppingToken);
            }
            finally
            {
                if (_flaskProcess != null && !_flaskProcess.HasExited)
                {
                    _logger.LogInformation("Stopping Flask backend...");
                    _flaskProcess.Kill(true);
                }
            }
        }
    }
}
