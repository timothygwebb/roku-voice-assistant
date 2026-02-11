import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import sys
import os

class RokuVoiceAssistantService(win32serviceutil.ServiceFramework):
    _svc_name_ = "RokuVoiceAssistant"
    _svc_display_name_ = "Roku Voice Assistant Service"
    _svc_description_ = "Runs the Roku Voice Assistant Flask API as a Windows Service."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            self.process.terminate()
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ""))
        self.main()

    def main(self):
        # Start the Flask app as a subprocess
        python_exe = sys.executable
        app_path = os.path.join(os.path.dirname(__file__), 'mobile_app', 'app.py')
        self.process = subprocess.Popen([python_exe, app_path])
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        if self.process:
            self.process.terminate()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(RokuVoiceAssistantService)
