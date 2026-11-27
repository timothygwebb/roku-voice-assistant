using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.Logging;

namespace roku_voice_assistant
{
    /// <summary>
    /// Windows Job Object wrapper that guarantees a child process dies
    /// when this process dies, however it dies.
    ///
    /// The launcher already kills Flask in a finally block, but that
    /// only runs on a graceful shutdown. Pressing Stop Debugging in
    /// Visual Studio terminates the dotnet process outright, so the
    /// finally block never runs and Flask is orphaned on port 8443.
    /// A Job Object with JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE is enforced
    /// by Windows itself: when the last handle to the job is closed
    /// (which happens when this process exits, gracefully or not),
    /// Windows terminates every process in the job.
    ///
    /// The job handle is deliberately kept open for the lifetime of
    /// this process. Closing the last handle to a KILL_ON_JOB_CLOSE
    /// job terminates its processes, so never close it here.
    ///
    /// If assignment fails (for example the child is already in a
    /// job created by the debugger), this returns false and the caller
    /// falls back to the parent watcher in mobile_app/app.py.
    /// </summary>
    public static class ChildProcessJob
    {
        private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;
        private const int JobObjectExtendedLimitInformation = 9;

        private static IntPtr _jobHandle = IntPtr.Zero;
        private static readonly object _lock = new object();
        private static bool _jobFailed;

        [StructLayout(LayoutKind.Sequential)]
        private struct JOBOBJECT_BASIC_LIMIT_INFORMATION
        {
            public long PerProcessUserTimeLimit;
            public long PerJobUserTimeLimit;
            public uint LimitFlags;
            public UIntPtr MinimumWorkingSetSize;
            public UIntPtr MaximumWorkingSetSize;
            public uint ActiveProcessLimit;
            public UIntPtr Affinity;
            public uint PriorityClass;
            public uint SchedulingClass;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct IO_COUNTERS
        {
            public ulong ReadOperationCount;
            public ulong WriteOperationCount;
            public ulong OtherOperationCount;
            public ulong ReadTransferCount;
            public ulong WriteTransferCount;
            public ulong OtherTransferCount;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
        {
            public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
            public IO_COUNTERS IoInfo;
            public UIntPtr ProcessMemoryLimit;
            public UIntPtr JobMemoryLimit;
            public UIntPtr PeakProcessMemoryUsed;
            public UIntPtr PeakJobMemoryUsed;
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string? lpName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool SetInformationJobObject(IntPtr hJob, int JobObjectInfoClass, ref JOBOBJECT_EXTENDED_LIMIT_INFORMATION lpJobObjectInfo, uint cbJobObjectInfoLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool CloseHandle(IntPtr hObject);

        public static bool TryAssign(Process process, ILogger logger)
        {
            if (!OperatingSystem.IsWindows())
            {
                return false;
            }
            if (process.HasExited)
            {
                return false;
            }
            lock (_lock)
            {
                if (_jobFailed)
                {
                    return false;
                }
                if (_jobHandle == IntPtr.Zero)
                {
                    _jobHandle = CreateJobObject(IntPtr.Zero, null);
                    if (_jobHandle == IntPtr.Zero)
                    {
                        _jobFailed = true;
                        logger.LogWarning("Could not create Job Object for Flask backend (Win32 error {Error}). Flask will rely on the parent watcher.", Marshal.GetLastWin32Error());
                        return false;
                    }
                    var info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION
                    {
                        BasicLimitInformation = new JOBOBJECT_BASIC_LIMIT_INFORMATION
                        {
                            LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
                        }
                    };
                    uint size = (uint)Marshal.SizeOf(info);
                    if (!SetInformationJobObject(_jobHandle, JobObjectExtendedLimitInformation, ref info, size))
                    {
                        int error = Marshal.GetLastWin32Error();
                        CloseHandle(_jobHandle);
                        _jobHandle = IntPtr.Zero;
                        _jobFailed = true;
                        logger.LogWarning("Could not set KILL_ON_JOB_CLOSE on Job Object (Win32 error {Error}). Flask will rely on the parent watcher.", error);
                        return false;
                    }
                }
                if (!AssignProcessToJobObject(_jobHandle, process.Handle))
                {
                    int error = Marshal.GetLastWin32Error();
                    logger.LogWarning("Could not assign Flask process {Pid} to Job Object (Win32 error {Error}). Flask will rely on the parent watcher.", process.Id, error);
                    return false;
                }
                logger.LogInformation("Assigned Flask process {Pid} to Job Object (kill on parent exit).", process.Id);
                return true;
            }
        }
    }
}
