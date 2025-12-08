#Start Transcript 

$transcriptPath = "C:\Logs\Install-Transcript-$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
Start-Transcript -Path $transcriptPath -Append

# Define paths to the installers

$virtio = "virtio-win-gt-x64.msi"
$qemuGuestAgent = "qemu-ga-x86_64.msi"
$logDirectory = "C:\Logs\"

# Ensure the log directory exists
if (-not (Test-Path -Path $logDirectory)) {
    New-Item -ItemType Directory -Path $logDirectory -Force
}

# Function to install MSI packages
function Install-MSI {
    param (
        [string]$msiPath,
        [string]$logFile
    )

    if (Test-Path -Path $msiPath) {
        Write-Output "Installing $msiPath"
        Start-Process msiexec -Wait -ArgumentList @('/i', $msiPath, '/log', $logFile, '/qn', '/passive', '/norestart', 'ADDLOCAL=ALL')
        if ($LASTEXITCODE -eq 0) {
            Write-Output "$msiPath installed successfully."
        } else {
            Write-Output "Failed to install $msiPath. Check log file: $logFile"
        }
    } else {
        Write-Output "MSI path $msiPath not found."
    }
}
function Find-DriverFile {
    param (
        [string]$fileName
    )

    # --- 1. Try D: first ---
    $path = Get-ChildItem -Path "D:\" -Recurse -Filter $fileName -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName -First 1

    if ($path) {
        return $path
    }

    Write-Output "File '$fileName' not found on D:. Searching all drives..."

    # --- 2. Search ALL drives except D: ---
    $allDrives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -ne 'D' }

    foreach ($drive in $allDrives) {
        $path = Get-ChildItem -Path ($drive.Root) -Recurse -Filter $fileName -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName -First 1

        if ($path) {
            return $path
        }
    }

    return $null
}
# Install Virtio Drivers
$virtioDriverPath = Find-DriverFile -fileName $virtio
$qemuGuestAgentPath = Find-DriverFile -fileName $qemuGuestAgent

$qemuGuestAgentPath = "D:\guest-agent\qemu-ga-x86_64.msi"
Install-MSI -msiPath $virtioDriverPath -logFile "$logDirectory\qemu-drivers.log"

# Install QEMU Guest Agent
Install-MSI -msiPath $qemuGuestAgentPath -logFile "$logDirectory\qemu-guest-agent.log"

Stop-Transcript