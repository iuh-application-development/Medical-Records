# Script Configuration
$appName = "Medical Records Management System"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$condaEnvName = "medical-records-env"
$pythonVersion = "3.10.11"
$requirementsFile = Join-Path $projectPath "requirements.txt"
$appModule = Join-Path $projectPath "run.py"
$dbPath = Join-Path $projectPath "instance\medical_records.db"

# Output formatting functions
function Write-Header {
    param (
        [string]$text
    )
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-Step {
    param (
        [string]$text
    )
    Write-Host "`n>> $text" -ForegroundColor Yellow
}

function Write-Success {
    param (
        [string]$text
    )
    Write-Host $text -ForegroundColor Green
}

function Write-Error {
    param (
        [string]$text
    )
    Write-Host $text -ForegroundColor Red
}

# Main script execution
Write-Header "Welcome to $appName Setup and Run Script"

# Step 1: Check if Python/Miniconda is installed
Write-Step "Checking Python and Miniconda installation..."
try {
    $condaVersion = conda --version
    Write-Success "Miniconda/Anaconda is installed: $condaVersion"
}
catch {
    Write-Host "Miniconda is not installed. We need to install it first." -ForegroundColor Yellow
    
    # Offer to install Miniconda using winget
    $installConda = Read-Host "Do you want to install Miniconda using winget? (y/n)"
    if ($installConda -eq "y" -or $installConda -eq "Y") {
        Write-Host "Installing Miniconda using winget..." -ForegroundColor Yellow
        try {
            winget install Anaconda.Miniconda3
            if ($LASTEXITCODE -ne 0) {
                throw "Winget installation failed with exit code $LASTEXITCODE"
            }
            Write-Success "Miniconda installed successfully!"
            Write-Host "Please restart this script after installation completes for the PATH changes to take effect." -ForegroundColor Yellow
            exit 0
        }
        catch {
            Write-Error "Failed to install Miniconda. Error: $_"
            Write-Host "Please download and install Miniconda manually from: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
            exit 1
        }
    }
    else {
        Write-Host "Please install Miniconda manually from: https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Yellow
        exit 1
    }
}

# Step 2: Create and set up conda environment
Write-Step "Setting up conda environment with Python $pythonVersion..."

# Initialize conda for PowerShell
Write-Host "Initializing conda for PowerShell..." -ForegroundColor Yellow
conda init powershell

# Check if the environment already exists
$envList = conda env list
$envExists = $envList -match $condaEnvName

if (-not $envExists) {
    Write-Host "Creating new conda environment '$condaEnvName' with Python $pythonVersion..." -ForegroundColor Yellow
    conda create -n $condaEnvName python=$pythonVersion -y
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create conda environment. Error code: $LASTEXITCODE"
        exit 1
    }
    Write-Success "Conda environment created successfully"
}
else {
    Write-Success "Conda environment '$condaEnvName' already exists"
}

# Install dependencies in the conda environment
Write-Step "Installing project dependencies..."
if (Test-Path $requirementsFile) {
    # Create a batch script to activate the environment and install dependencies
    $batchScript = @"
@echo off
CALL conda.bat activate $condaEnvName
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python -m pip install -r "$requirementsFile"
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
"@
    
    $batchPath = Join-Path $projectPath "install_deps.bat"
    $batchScript | Out-File -FilePath $batchPath -Encoding ascii
    
    Write-Host "Activating conda environment and installing dependencies..." -ForegroundColor Yellow
    cmd /c $batchPath
    
    if ($LASTEXITCODE -ne 0) {
        Remove-Item $batchPath -Force
        Write-Error "Failed to install dependencies. Error code: $LASTEXITCODE"
        exit 1
    }
    
    Remove-Item $batchPath -Force
    Write-Success "Dependencies installed successfully"
}
else {
    Write-Error "Requirements file not found at: $requirementsFile"
    exit 1
}

# Database will be initialized automatically when the application starts

# Step 3: Run the application
Write-Header "Starting $appName"
Write-Host "The application will be available at: http://localhost:5000"
Write-Host "Press Ctrl+C to stop the server`n"

try {
    # Create a batch script to activate environment and run the application
    $batchScript = @"
@echo off
CALL conda.bat activate $condaEnvName
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python "$appModule"
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
"@
    
    $batchPath = Join-Path $projectPath "run_app.bat"
    $batchScript | Out-File -FilePath $batchPath -Encoding ascii
    
    # Run the batch script
    cmd /c $batchPath
    
    # Remove the temporary batch file
    Remove-Item $batchPath -Force
}
catch {
    Write-Error "Error running the application: $_"
    exit 1
}
