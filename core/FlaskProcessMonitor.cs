using System.Diagnostics;

namespace roku_voice_assistant
{
    public class FlaskProcessMonitor
    {
        private Process? _process;
        private readonly object _lock = new object();

        public void SetProcess(Process process)
        {
            lock (_lock)
            {
                _process = process;
            }
        }

        public bool IsRunning()
        {
            lock (_lock)
            {
                try
                {
                    return _process != null && !_process.HasExited;
                }
                catch
                {
                    return false;
                }
            }
        }

        public DateTime? StartTime
        {
            get
            {
                lock (_lock)
                {
                    try
                    {
                        return _process?.StartTime;
                    }
                    catch
                    {
                        return null;
                    }
                }
            }
        }

        public int? GetPid()
        {
            lock (_lock)
            {
                try
                {
                    return _process?.Id;
                }
                catch
                {
                    return null;
                }
            }
        }
    }
}
