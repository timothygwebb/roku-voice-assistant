Param(
    [switch]$NonInteractive,
    [int]$BindingPort = 5000,
    [string]$Backend = 'https://localhost:8443/',
    [switch]$CreateFirewall,
    [switch]$CreateHttps,
    [int]$HttpsPort = 443,
    [string]$CertThumb = ''
)

<#
Configure IIS to act as a reverse proxy for the mobile Flask app (listening on localhost:8443).

Usage (run as Administrator in PowerShell):
  cd C:\path\to\repo
  .\tools\configure_iis.ps1

What the script does:
 - Checks for Administrator privileges
 - Ensures IIS (Web-Server) feature is installed
 - Checks for URL Rewrite and ARR presence (best-effort detection)
 - If ARR is present, enables proxy and creates an IIS site named "RokuVoiceAssistant"
   with a URL Rewrite inbound rule that proxies requests to http://localhost:8443/
 - If ARR is missing, prints instructions to install URL Rewrite and ARR modules

Note: Installing ARR via script is not included because Web Platform Installer may not
be available. Manual installation steps are printed when required.
#>

function Assert-Admin {
    $isAdmin = ([bool]([Security.Principal.WindowsIdentity]::GetCurrent()).IsAuthenticated) -and ((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
    if (-not $isAdmin) {
        Write-Error "This script must be run as Administrator. Start PowerShell as Administrator and re-run."
        exit 1
    }
}

function Ensure-IIS {
    Write-Host "Checking IIS (Web-Server) feature..."
    # Get-WindowsFeature is only available on Windows Server / with ServerManager module.
    if (Get-Command Get-WindowsFeature -ErrorAction SilentlyContinue) {
        $feature = Get-WindowsFeature -Name Web-Server -ErrorAction SilentlyContinue
        if (-not $feature) {
            Write-Host "Could not query Windows features via Get-WindowsFeature."
            return $false
        }

        if (-not $feature.Installed) {
            Write-Host "IIS not installed. Installing Web-Server (IIS) with management tools..."
            Install-WindowsFeature Web-Server -IncludeManagementTools -ErrorAction Stop
            Write-Host "IIS installed."
        }
        else {
            Write-Host "IIS is already installed."
        }

        return $true
    }
    else {
        # On Windows 10/11 the ServerManager cmdlets are not present. Check for IIS by service.
        Write-Host "Get-WindowsFeature not available on this OS. Falling back to service check."
        $svc = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Host "IIS appears to be installed (W3SVC service found)."
            return $true
        }
        else {
            Write-Warning "IIS does not appear to be installed and Get-WindowsFeature is not available on this machine."
            Write-Host "To install IIS on Windows 10/11 run PowerShell as Administrator and execute:"
            Write-Host "  dism /online /enable-feature /featurename:IIS-WebServer /all"
            Write-Host "Or enable 'Internet Information Services' via 'Turn Windows features on or off' in Control Panel."
            return $false
        }
    }
}

function Detect-UrlRewriteARR {
    Write-Host "Detecting URL Rewrite and ARR modules..."

    $hasRewrite = Test-Path "${env:ProgramFiles}\IIS\URL Rewrite" -PathType Container -ErrorAction SilentlyContinue
    $hasARR = Test-Path "${env:ProgramFiles}\IIS\Application Request Routing" -PathType Container -ErrorAction SilentlyContinue

    # Alternative checks
    if (-not $hasRewrite) {
        try { $hasRewrite = (Get-WebGlobalModule -ErrorAction SilentlyContinue | Where-Object name -match 'Rewrite') -ne $null } catch { }
    }
    if (-not $hasARR) {
        try { $hasARR = (Get-WebConfigurationProperty -pspath 'MACHINE/WEBROOT/APPHOST' -filter "system.webServer/serverRuntime" -name 'enabled' -ErrorAction SilentlyContinue) -ne $null } catch { }
    }

    return @{ Rewrite = $hasRewrite; ARR = $hasARR }
}

function Enable-ARRProxy {
    # Use appcmd to set proxy enabled (requires ARR)
    $appcmd = Join-Path $env:windir "system32\inetsrv\appcmd.exe"
    if (-not (Test-Path $appcmd)) {
        Write-Error "appcmd.exe not found at $appcmd"
        return $false
    }

    Write-Host "Enabling ARR proxy via appcmd..."
    & $appcmd set config -section:system.webServer/proxy /enabled:"True" /commit:apphost
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "appcmd returned non-zero exit code ($LASTEXITCODE) when enabling proxy. Proxy may not be enabled."
        return $false
    }
    Write-Host "ARR proxy enabled."
    return $true
}

function Create-ReverseProxySite {
    param(
        [string]$SiteName = 'RokuVoiceAssistant',
        [int]$BindingPort = 5000,
        [string]$Backend = 'https://localhost:8443/'
    )

    Import-Module WebAdministration -ErrorAction Stop

    $existing = Get-ChildItem IIS:\Sites | Where-Object { $_.Name -eq $SiteName }
    if ($existing) {
        Write-Host "Site '$SiteName' already exists. Updating rewrite rules to proxy to $Backend"
        $sitePath = "IIS:\Sites\$SiteName"
    }
    else {
        $physicalPath = Join-Path $env:SystemDrive 'inetpub\wwwroot\rokuproxy'
        if (-not (Test-Path $physicalPath)) {
            New-Item -Path $physicalPath -ItemType Directory | Out-Null
            Set-Content -Path (Join-Path $physicalPath 'index.html') -Value '<html><head><meta http-equiv="refresh" content="0;url=/ROKU" /></head><body></body></html>' -Encoding utf8
        }

        Write-Host "Creating IIS site '$SiteName' bound to port $BindingPort (http)..."
        New-Item IIS:\Sites\$SiteName -bindings @{protocol='http';bindingInformation="*:${BindingPort}:"} -physicalPath $physicalPath | Out-Null
        $sitePath = "IIS:\Sites\$SiteName"
    }

    # Create or replace URL Rewrite rule at site level to proxy to backend
    $rulesPath = "MACHINE/WEBROOT/APPHOST/$SiteName"
    # Determine physical path for the site so we can write a site-level web.config if needed
    try {
        $siteItem = Get-Item "IIS:\Sites\$SiteName" -ErrorAction SilentlyContinue
        if ($siteItem) {
            $physicalPath = $siteItem.physicalPath
        }
    }
    catch {
        $physicalPath = $null
    }
    try {
        # Remove existing rule if present
        $existingRule = Get-WebConfiguration -Filter "system.webServer/rewrite/rules/rule[@name='ReverseProxyToBackend']" -PSPath $rulesPath -ErrorAction SilentlyContinue
        if ($existingRule) {
            Remove-WebConfigurationProperty -pspath $rulesPath -filter "system.webServer/rewrite/rules" -name "." -AtElement @{name='ReverseProxyToBackend'} -ErrorAction SilentlyContinue
        }

        # Safely build XML for the rule, escaping the backend URL
        $escapedBackend = [System.Security.SecurityElement]::Escape($Backend)
        $xmlString = "<rules><rule name='ReverseProxyToBackend' stopProcessing='true'><match url='(.*)' /><action type='Rewrite' url='$escapedBackend{R:1}' logRewrittenUrl='true' /></rule></rules>"
        try {
            [xml]$xmlDoc = $xmlString
        }
        catch {
            Write-Warning "Failed to construct XML for rewrite rule: $_"
            return $false
        }

        $ruleNode = $xmlDoc.rules.rule
        if ($ruleNode) {
            try {
                Add-WebConfiguration -PSPath $rulesPath -Filter "system.webServer/rewrite/rules" -Value $ruleNode -ErrorAction Stop
                Write-Host "Added URL Rewrite rule 'ReverseProxyToBackend' to site '$SiteName' via configuration API."
            }
            catch {
                Write-Warning "Add-WebConfiguration failed: $_. Will attempt to write site web.config as fallback."
                $ruleNode = $null
            }
        }

        if (-not $ruleNode) {
            if (-not $physicalPath) {
                Write-Warning "Cannot determine site physical path; cannot write site-level web.config fallback."
                return $false
            }

            $webConfigPath = Join-Path $physicalPath 'web.config'
            try {
                if (Test-Path $webConfigPath) {
                    Copy-Item $webConfigPath "$webConfigPath.bak_$(Get-Date -Format yyyyMMddHHmmss)" -ErrorAction SilentlyContinue
                }

                $webConfigContent = @"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="ReverseProxyToBackend" stopProcessing="true">
          <match url="(.*)" />
          <action type="Rewrite" url="$($Backend){R:1}" logRewrittenUrl="true" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
"@

                Set-Content -Path $webConfigPath -Value $webConfigContent -Encoding UTF8
                Write-Host "Wrote site-level web.config with rewrite rule to $webConfigPath"
            }
            catch {
                Write-Warning "Failed to write web.config fallback: $_"
                return $false
            }
        }
    }
    catch {
        Write-Warning "Failed to add URL Rewrite rule: $_"
        return $false
    }

    return $true
}

# --- Script entry ---
Assert-Admin

Write-Host "Interactive configuration: press Enter to accept the default in [brackets]."
$SiteName = 'RokuVoiceAssistant'
try {
    $bindingPortInput = Read-Host "Front-end (IIS) port [5000]"
    if ([string]::IsNullOrWhiteSpace($bindingPortInput)) { $bindingPort = 5000 } else { $bindingPort = [int]$bindingPortInput }
    $backendInput = Read-Host "Backend URL to proxy to [http://localhost:8443/]"
    if ([string]::IsNullOrWhiteSpace($backendInput)) { $backend = 'http://localhost:8443/' } else { $backend = $backendInput }
    $createFirewallInput = Read-Host "Create firewall rule to allow inbound connections to port $bindingPort? (y/N)"
    $createFirewall = $createFirewallInput -and $createFirewallInput.ToLower().StartsWith('y')
    $createHttpsInput = Read-Host "Create HTTPS binding on IIS site? (y/N)"
    $createHttps = $createHttpsInput -and $createHttpsInput.ToLower().StartsWith('y')
    if ($createHttps) {
        $httpsPortInput = Read-Host "HTTPS port [443]"
        if ([string]::IsNullOrWhiteSpace($httpsPortInput)) { $httpsPort = 443 } else { $httpsPort = [int]$httpsPortInput }
        Write-Host "To create an HTTPS binding we need a certificate installed in LocalMachine\\My."
        Write-Host "If you do not have a certificate yet, import it into 'Local Machine -> Personal' and then re-run this script."
        $certThumb = Read-Host "Certificate thumbprint to bind (leave empty to skip binding now)"
    }
}
catch {
    Write-Warning "Invalid input. Using defaults."
    $bindingPort = 5000
    $backend = 'http://localhost:8443/'
    $createFirewall = $false
    $createHttps = $false
}

if (-not (Ensure-IIS)) { exit 1 }

$mods = Detect-UrlRewriteARR
Write-Host "URL Rewrite detected: $($mods.Rewrite)    ARR detected: $($mods.ARR)"

if (-not $mods.Rewrite) {
    Write-Warning "URL Rewrite module not detected. Please install 'URL Rewrite' for IIS:
  - Download and install: https://www.iis.net/downloads/microsoft/url-rewrite"
}

if (-not $mods.ARR) {
    Write-Warning "Application Request Routing (ARR) not detected. ARR is required for reverse-proxying (proxy functionality).
  - Install ARR from: https://www.iis.net/downloads/microsoft/application-request-routing
  - After installing ARR, re-run this script.
"
}

if ($mods.ARR) {
    if (-not (Enable-ARRProxy)) {
        Write-Warning "Failed to enable ARR proxy. Check ARR installation and try enabling proxy manually."
    }

    $ok = Create-ReverseProxySite -SiteName $SiteName -BindingPort $bindingPort -Backend $backend
    if ($ok) {
        Write-Host "IIS site configured. Browse to http://localhost:$bindingPort/ and requests will be proxied to $backend"

        if ($createFirewall) {
            try {
                Write-Host "Creating Windows Firewall rule to allow port $bindingPort..."
                New-NetFirewallRule -DisplayName "IIS RokuVoiceAssistant Port $bindingPort" -Direction Inbound -LocalPort $bindingPort -Protocol TCP -Action Allow -Profile Any -ErrorAction Stop
                Write-Host "Firewall rule created."
            }
            catch {
                Write-Warning "Failed to create firewall rule: $_"
            }
        }

        if ($createHttps) {
            if ([string]::IsNullOrWhiteSpace($certThumb)) {
                Write-Warning "No certificate thumbprint provided. Skipping HTTPS binding creation."
                Write-Host "To add HTTPS later: import a cert to LocalMachine\\My and re-run this script or use IIS Manager to add an https binding and select the certificate."
            }
            else {
                try {
                    Import-Module WebAdministration -ErrorAction Stop
                    Write-Host "Creating HTTPS binding on port $httpsPort..."
                    # Create HTTPS binding
                    New-WebBinding -Name $SiteName -Protocol https -Port $httpsPort -IPAddress * -ErrorAction Stop
                    # Bind certificate to the port
                    $thumb = $certThumb -replace '\s',''
                    $cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Thumbprint -eq $thumb }
                    if (-not $cert) {
                        Write-Warning "Certificate with thumbprint $thumb not found in LocalMachine\\My. Import certificate and re-run."
                    }
                    else {
                        # Use SSL bindings provider to set the certificate
                        $sslPath = "IIS:\SslBindings\0.0.0.0!$httpsPort"
                        if (Test-Path $sslPath) { Remove-Item $sslPath -ErrorAction SilentlyContinue }
                        New-Item $sslPath -Value $cert.Thumbprint | Out-Null
                        Write-Host "HTTPS binding created and certificate assigned."
                    }
                }
                catch {
                    Write-Warning "Failed to create HTTPS binding: $_"
                }
            }
        }
    }
    else {
        Write-Warning "Failed to create or update IIS site."
    }
}
else {
    Write-Host "IIS is available but ARR is not installed. The script created a static site placeholder and printed installation instructions for ARR. After installing ARR, re-run this script to enable reverse proxy."
}

Write-Host "Done."
