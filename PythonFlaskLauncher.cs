using System.Diagnostics;
using System.Runtime.InteropServices;

namespace roku_worker_service
{
    public class PythonFlaskLauncher : BackgroundService
    {
        private Process? _flaskProcess;
        private readonly ILogger<PythonFlaskLauncher> _logger;
        public PythonFlaskLauncher(ILogger<PythonFlaskLauncher> logger)
        {
            _logger = logger;
        }

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

            _logger.LogInformation($"Starting Flask backend: {pythonExe} {psi.Arguments}");
            _flaskProcess = Process.Start(psi);

            if (_flaskProcess != null)
            {
                _flaskProcess.OutputDataReceived += (s, e) => { if (e.Data != null) _logger.LogInformation(e.Data); };
                _flaskProcess.ErrorDataReceived += (s, e) => { if (e.Data != null) _logger.LogError(e.Data); };
                _flaskProcess.BeginOutputReadLine();
                _flaskProcess.BeginErrorReadLine();
            }

            // Open the browser to the remote control page (http://localhost:5000/)
            try
            {
                string url = "http://localhost:5000/";
                _logger.LogInformation($"Opening browser to {url}");
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
                    _logger.LogWarning($"Could not open browser: {ex.Message}");
                }

                // Wait until cancellation
                while (!stoppingToken.IsCancellationRequested)
                {
                    await Task.Delay(1000, stoppingToken);
                }
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
