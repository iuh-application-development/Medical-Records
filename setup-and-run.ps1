# Medical Records Management System Setup Script
# Filename: setup-and-run.ps1
# Date: May 25, 2025
# This script automates the setup and running of the Medical Records Management System with Conda

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

# Initialize database if it doesn't exist
Write-Step "Checking database..."
$initDatabase = $true
if (Test-Path $dbPath) {
    $response = Read-Host "Database already exists. Do you want to recreate it? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Remove-Item $dbPath -Force
        Write-Success "Existing database removed"
    }
    else {
        $initDatabase = $false
        Write-Success "Using existing database"
    }
}

if ($initDatabase) {
    Write-Step "Initializing database..."
    try {
        # Create a temporary Python script to initialize the database
        $initScript = @"
from app import create_app, db
from app.models.user import User
from app.config import DevelopmentConfig
import os

# Create app with development configuration
app = create_app(DevelopmentConfig)

# Ensure instance folder exists
os.makedirs('instance', exist_ok=True)

# Initialize database
with app.app_context():
    db.create_all()
    
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', role='admin', phone='0123456789')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: username='admin', password='admin'")
    else:
        print("Admin user already exists")

    print("Database initialized successfully")
"@

        $initScriptPath = Join-Path $projectPath "init_db.py"
        $initScript | Out-File -FilePath $initScriptPath -Encoding utf8
        # Create a batch script to activate environment and run the initialization
        $batchScript = @"
@echo off
CALL conda.bat activate $condaEnvName
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
python "$initScriptPath"
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
"@
        
        $batchPath = Join-Path $projectPath "init_db.bat"
        $batchScript | Out-File -FilePath $batchPath -Encoding ascii
        
        # Run the batch script
        cmd /c $batchPath
        
        if ($LASTEXITCODE -ne 0) {
            Remove-Item $initScriptPath -Force
            Remove-Item $batchPath -Force
            throw "Database initialization failed with error code: $LASTEXITCODE"
        }
        
        # Remove the temporary scripts
        Remove-Item $initScriptPath -Force
        Remove-Item $batchPath -Force
        
        Write-Success "Database initialized successfully"
    }
    catch {
        Write-Error "Failed to initialize database. Error: $_"
        exit 1
    }
}

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
