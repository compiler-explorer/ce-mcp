# Claude Code Setup Script for Compiler Explorer MCP Server
# This script sets up the MCP server for use with Claude Code on Windows

param(
    [string]$ProjectDir = "",
    [switch]$Global,
    [switch]$GlobalMcp,
    [switch]$NonInteractive,
    [switch]$Quiet,
    [string]$Language = "c++",
    [string]$Compiler = "",
    [switch]$Uninstall,
    [switch]$Help
)

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Remember the directory where the script is located (ce-mcp source directory)
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Colors for output
function Write-Header {
    if (-not $Quiet) {
        Write-Host "================================================" -ForegroundColor Blue
        Write-Host "  Compiler Explorer MCP Setup for Claude Code  " -ForegroundColor Blue
        Write-Host "================================================" -ForegroundColor Blue
        Write-Host ""
    }
}

function Write-Step {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host "[STEP]" -ForegroundColor Green -NoNewline
        Write-Host " $Message"
    }
}

function Write-Info {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host "[INFO]" -ForegroundColor Yellow -NoNewline
        Write-Host " $Message"
    }
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR]" -ForegroundColor Red -NoNewline
    Write-Host " $Message"
}

function Write-Success {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host "[SUCCESS]" -ForegroundColor Green -NoNewline
        Write-Host " $Message"
    }
}

# Check if command exists
function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Show help
function Show-Help {
    Write-Host @"
Usage: .\setup-claude-code.ps1 [OPTIONS]

Setup or uninstall Compiler Explorer MCP server for Claude Code

Options:
  -ProjectDir DIR       Target project directory (default: current directory)
  -Global              Install ce-mcp globally with pipx instead of project-local
  -GlobalMcp           Register MCP server globally (available in all projects)
  -NonInteractive      Skip interactive prompts, use defaults
  -Quiet               Quiet mode: no output except errors
  -Language LANG       Default language (c++, c, rust, go, python)
  -Compiler COMP       Default compiler (g++, clang++, rustc, etc.)
  -Uninstall           Uninstall ce-mcp and remove configuration
  -Help                Show this help message

Examples:
  .\setup-claude-code.ps1                                    # Setup in current directory
  .\setup-claude-code.ps1 -ProjectDir C:\my-cpp-project      # Setup in specific project
  .\setup-claude-code.ps1 -Global                            # Install ce-mcp globally
  .\setup-claude-code.ps1 -GlobalMcp                         # Register MCP globally (all projects)
  .\setup-claude-code.ps1 -NonInteractive                    # Use defaults without prompts
  .\setup-claude-code.ps1 -Quiet                             # Quiet setup with no output
  .\setup-claude-code.ps1 -Language rust -Compiler rustc     # Setup for Rust
  .\setup-claude-code.ps1 -Uninstall                         # Uninstall ce-mcp

The script will:
  1. Install the ce-mcp Python package
  2. Create project configuration (.ce-mcp-config.yaml)
  3. Register the MCP server with Claude using 'claude mcp add'
  4. Verify the installation

After setup, the MCP server will be available in Claude Code via @ce-mcp
"@
    exit 0
}

# Check prerequisites
function Test-Prerequisites {
    Write-Step "Checking prerequisites..."

    # Check for Claude CLI (required)
    if (-not (Test-Command "claude")) {
        Write-ErrorMsg "Claude CLI is required but not found"
        if (-not $Quiet) {
            Write-Host ""
            Write-Info "Please install Claude Code from: https://claude.ai/download"
        }
        exit 1
    }

    # Check for UV, and install if missing
    if (-not (Test-Command "uv")) {
        Write-Info "UV not found, installing it now..."
        try {
            # Install UV using the official command
            powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

            # Verify UV is now available
            if (-not (Test-Command "uv")) {
                Write-ErrorMsg "UV installation failed or PATH not updated"
                Write-Info "You may need to restart your terminal or manually install UV"
                Write-Info "Install command: powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
                exit 1
            }
            Write-Success "UV installed successfully"
        }
        catch {
            Write-ErrorMsg "Failed to install UV automatically: $_"
            Write-Info "Please install UV manually using:"
            Write-Host "  powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
            exit 1
        }
    }

    # UV will handle Python installation when needed
    Write-Success "All prerequisites found"
}

# Get Python command
function Get-PythonCommand {
    # UV provides Python, so we can use uv's Python
    if (Test-Command "uv") {
        return "uv python"
    }
    elseif (Test-Command "python") {
        return "python"
    }
    elseif (Test-Command "python3") {
        return "python3"
    }
    else {
        throw "Python not found"
    }
}

# Install MCP Server
function Install-MCPServer {
    Write-Step "Installing Compiler Explorer MCP server..."

    # Check if we're running the script from the ce-mcp development directory
    $pyprojectPath = Join-Path $SCRIPT_DIR "pyproject.toml"
    if ((Test-Path $pyprojectPath) -and (Get-Content $pyprojectPath | Select-String "ce-mcp")) {
        Write-Info "Found ce-mcp development directory at: $SCRIPT_DIR"

        if ($Global) {
            Write-Info "Installing globally with pipx..."
            if (-not (Test-Command "pipx")) {
                Write-Info "Installing pipx first..."
                $python = Get-PythonCommand
                if (Test-Command "uv") {
                    uv tool install pipx
                }
                else {
                    & $python -m pip install --user pipx
                    & $python -m pipx ensurepath
                    # Refresh PATH
                    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                }
            }

            # Install with pipx
            pipx install $SCRIPT_DIR
            $script:CE_MCP_COMMAND = "ce-mcp"

            # For global installation, we should use global registration by default
            if (-not $PSBoundParameters.ContainsKey('GlobalMcp')) {
                $script:GlobalMcp = $true
                Write-Info "Global installation detected, will use global MCP registration"
            }
        }
        else {
            Write-Info "Installing in project environment from source: $SCRIPT_DIR"
            Push-Location $ProjectDir

            # Create virtual environment if it doesn't exist
            $venvPath = Join-Path $ProjectDir ".venv"
            if (-not (Test-Path $venvPath)) {
                $python = Get-PythonCommand
                if (Test-Command "uv") {
                    if ($Quiet) {
                        uv venv --seed 2>&1 | Out-Null
                    }
                    else {
                        uv venv --seed
                    }
                }
                else {
                    if ($Quiet) {
                        & $python -m venv .venv 2>&1 | Out-Null
                    }
                    else {
                        & $python -m venv .venv
                    }
                }
            }

            # Install ce-mcp in the virtual environment
            $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
            & $activateScript

            if (Test-Command "uv") {
                if ($Quiet) {
                    uv pip install -e $SCRIPT_DIR 2>&1 | Out-Null
                }
                else {
                    uv pip install -e $SCRIPT_DIR
                }
            }
            else {
                if ($Quiet) {
                    pip install -e $SCRIPT_DIR 2>&1 | Out-Null
                }
                else {
                    pip install -e $SCRIPT_DIR
                }
            }
            deactivate

            # Create a wrapper batch file that activates venv first
            $wrapperPath = Join-Path $ProjectDir ".ce-mcp-wrapper.bat"
            @"
@echo off
rem Wrapper script for ce-mcp that activates the virtual environment
call "%~dp0.venv\Scripts\activate.bat"
ce-mcp %*
"@ | Set-Content -Path $wrapperPath

            # Also create a PowerShell wrapper
            $psWrapperPath = Join-Path $ProjectDir ".ce-mcp-wrapper.ps1"
            @"
# Wrapper script for ce-mcp that activates the virtual environment
& "$venvPath\Scripts\Activate.ps1"
ce-mcp @args
"@ | Set-Content -Path $psWrapperPath

            $script:CE_MCP_COMMAND = $wrapperPath
            Pop-Location
        }
    }
    else {
        Write-ErrorMsg "Cannot find ce-mcp source at: $SCRIPT_DIR"
        Write-ErrorMsg "Please ensure the script is in the ce-mcp directory with pyproject.toml"
        exit 1
    }

    Write-Success "MCP server installed successfully"
}

# Create project configuration
function New-ProjectConfig {
    Write-Step "Creating configuration..."

    # Determine config location based on scope
    if ($GlobalMcp) {
        # Use user's home directory for global config
        $configDir = Join-Path $env:USERPROFILE ".config\compiler_explorer_mcp"
        if (-not (Test-Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }
        $script:ConfigPath = Join-Path $configDir "config.yaml"
        Write-Info "Creating global configuration in user directory..."
    }
    else {
        # Use project directory for local config
        Push-Location $ProjectDir
        $script:ConfigPath = Join-Path $ProjectDir ".ce-mcp-config.yaml"
        Write-Info "Creating project configuration..."
    }

    # Set default compiler based on language
    if ([string]::IsNullOrEmpty($Compiler)) {
        switch ($Language) {
            "c++" { $Compiler = "g++" }
            "c" { $Compiler = "gcc" }
            "rust" { $Compiler = "rustc" }
            "go" { $Compiler = "go" }
            "python" { $Compiler = "python311" }
            default { $Compiler = "g++" }
        }
    }

    if (-not $NonInteractive -and -not $Quiet) {
        # Ask for default language
        $inputLang = Read-Host "What's your primary programming language? (c++/c/rust/go/python) [c++]"
        if (-not [string]::IsNullOrEmpty($inputLang)) {
            $Language = $inputLang
        }

        # Ask for default compiler
        switch ($Language) {
            { $_ -in "c++", "c" } {
                $inputCompiler = Read-Host "Preferred compiler? (g++/clang++) [g++]"
                if (-not [string]::IsNullOrEmpty($inputCompiler)) {
                    $Compiler = $inputCompiler
                }
                else {
                    $Compiler = "g++"
                }
            }
            "rust" { $Compiler = "rustc" }
            "go" { $Compiler = "go" }
            "python" { $Compiler = "python311" }
            default { $Compiler = "g++" }
        }
    }
    else {
        Write-Info "Using language: $Language, compiler: $Compiler"
    }

    # Create configuration file at the determined location
    @"
# Project-specific Compiler Explorer MCP configuration
compiler_explorer_mcp:
  api:
    timeout: 30

  defaults:
    language: "$Language"
    compiler: "$Compiler"
    extract_args_from_source: true

  filters:
    commentOnly: true
    demangle: true
    intel: true
    labels: true

  output_limits:
    max_stdout_lines: 50
    max_stderr_lines: 25
    max_assembly_lines: 100
    max_line_length: 120

  compiler_mappings:
    "g++": "g132"
    "gcc": "g132"
    "clang++": "clang1700"
    "clang": "clang1700"
    "rustc": "r1740"
    "go": "gccgo132"
    "python": "python311"
"@ | Set-Content -Path $script:ConfigPath

    if ($GlobalMcp) {
        Write-Success "Configuration file created: $script:ConfigPath"
    }
    else {
        Write-Success "Configuration file created: .ce-mcp-config.yaml"
        Pop-Location
    }
}

# Register MCP Server
function Register-MCPServer {
    Write-Step "Registering MCP server with Claude..."

    $mcpName = "ce-mcp"

    # First remove any existing ce-mcp server
    Write-Info "Checking for existing ce-mcp server..."
    $existingServers = claude mcp list 2>$null
    if ($existingServers -match $mcpName) {
        Write-Info "Removing existing $mcpName server..."
        claude mcp remove $mcpName 2>&1 | Out-Null
    }

    # Use the config path determined by New-ProjectConfig

    # Determine scope message
    if ($GlobalMcp) {
        Write-Info "Registering MCP server globally (user scope)..."
    }
    else {
        Write-Info "Registering MCP server for this project (local scope)..."
    }

    # Register with claude mcp add
    try {
        if ($Quiet) {
            if ($GlobalMcp) {
                claude mcp add --scope user $mcpName $CE_MCP_COMMAND -- --config $script:ConfigPath 2>&1 | Out-Null
            }
            else {
                claude mcp add $mcpName $CE_MCP_COMMAND -- --config $script:ConfigPath 2>&1 | Out-Null
            }
        }
        else {
            if ($GlobalMcp) {
                claude mcp add --scope user $mcpName $CE_MCP_COMMAND -- --config $script:ConfigPath
            }
            else {
                claude mcp add $mcpName $CE_MCP_COMMAND -- --config $script:ConfigPath
            }
        }
        Write-Success "MCP server registered successfully with Claude"
    }
    catch {
        Write-ErrorMsg "Failed to register MCP server"
        Write-Info "You can try manually registering with:"
        if ($GlobalMcp) {
            Write-Host "  claude mcp add --scope user `"$mcpName`" `"$CE_MCP_COMMAND`" -- --config `"$script:ConfigPath`""
        }
        else {
            Write-Host "  claude mcp add `"$mcpName`" `"$CE_MCP_COMMAND`" -- --config `"$script:ConfigPath`""
        }
        exit 1
    }
}

# Verify installation
function Test-Installation {
    Write-Step "Verifying installation..."
    Push-Location $ProjectDir

    # Test that the MCP command works
    Write-Info "Testing MCP server command..."

    $wrapperBat = Join-Path $ProjectDir ".ce-mcp-wrapper.bat"
    $wrapperPs1 = Join-Path $ProjectDir ".ce-mcp-wrapper.ps1"

    if (Test-Path $wrapperBat) {
        # Test wrapper script
        try {
            & $wrapperBat --help 2>&1 | Out-Null
            Write-Success "MCP wrapper script works correctly"
        }
        catch {
            Write-ErrorMsg "MCP wrapper script failed"
            exit 1
        }
    }
    elseif (Test-Command "ce-mcp") {
        # Test global installation
        try {
            ce-mcp --help 2>&1 | Out-Null
            Write-Success "ce-mcp command works correctly"
        }
        catch {
            Write-ErrorMsg "ce-mcp command failed"
            exit 1
        }
    }
    else {
        Write-ErrorMsg "ce-mcp command not found"
        exit 1
    }

    # Check that MCP server is registered with Claude
    Write-Info "Verifying MCP registration..."
    $mcpList = claude mcp list 2>$null
    if ($mcpList -match "ce-mcp") {
        Write-Success "MCP server is registered with Claude"

        # Show MCP server details
        if (-not $Quiet) {
            Write-Host ""
            Write-Info "MCP server details:"
            claude mcp get ce-mcp 2>$null
        }
    }
    else {
        Write-ErrorMsg "MCP server not found in Claude configuration"
        exit 1
    }

    # Check configuration file
    if (Test-Path $script:ConfigPath) {
        if ($GlobalMcp) {
            Write-Success "Global configuration file exists: $script:ConfigPath"
        }
        else {
            Write-Success "Configuration file exists: .ce-mcp-config.yaml"
        }
    }
    else {
        Write-ErrorMsg "Configuration file missing at: $script:ConfigPath"
        exit 1
    }

    Pop-Location
}

# Show completion message
function Show-CompletionMessage {
    if (-not $Quiet) {
        Write-Host ""
        Write-Success "Setup complete!"
        Write-Host ""
        Write-Host "Your project is now configured for Claude Code with Compiler Explorer MCP!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Restart Claude Code (or reload the window)"
        Write-Host "2. The MCP server should be automatically available"
        Write-Host "3. Try using the MCP tools with @ce-mcp:"
        Write-Host ""
        Write-Host "Example usage:" -ForegroundColor Yellow
        Write-Host "  Ask Claude: `"@ce-mcp compile and run this code: int main(){return 0;}`""
        Write-Host ""
        Write-Host "Configuration:" -ForegroundColor Yellow
        if ($GlobalMcp) {
            Write-Host "  * MCP server registered globally (available in all projects)"
        }
        else {
            Write-Host "  * MCP server registered for this project"
        }
        Write-Host "  * .ce-mcp-config.yaml - Project-specific settings"
        Write-Host ""
        Write-Host "Available tools via @ce-mcp:" -ForegroundColor Yellow
        Write-Host "  * compile_check_tool - Quick syntax validation"
        Write-Host "  * compile_and_run_tool - Compile and execute code"
        Write-Host "  * compile_with_diagnostics_tool - Detailed error analysis"
        Write-Host "  * analyze_optimization_tool - Assembly optimization analysis"
        Write-Host "  * generate_share_url_tool - Create shareable links"
        Write-Host "  * compare_compilers_tool - Side-by-side compiler comparison"
        Write-Host ""
        Write-Host "Managing the MCP server:" -ForegroundColor Yellow
        Write-Host "  claude mcp list              - List all MCP servers"
        Write-Host "  claude mcp get ce-mcp        - Show server details"
        Write-Host "  claude mcp remove ce-mcp     - Remove the server"
        Write-Host ""
        Write-Host "Happy coding!" -ForegroundColor Blue
    }
}

# Uninstall MCP Server
function Uninstall-MCPServer {
    Write-Header
    Write-Info "Uninstalling Compiler Explorer MCP server..."
    Write-Host ""

    $mcpName = "ce-mcp"

    # Remove MCP server from Claude
    if (Test-Command "claude") {
        Push-Location $ProjectDir -ErrorAction SilentlyContinue
        $mcpList = claude mcp list 2>$null
        if ($mcpList -match $mcpName) {
            Write-Info "Removing $mcpName from Claude..."
            claude mcp remove $mcpName 2>&1 | Out-Null
            Write-Success "Removed $mcpName from Claude configuration"
        }
        Pop-Location -ErrorAction SilentlyContinue
    }

    # Remove from project directory
    if (Test-Path $ProjectDir) {
        Push-Location $ProjectDir

        # Remove wrapper scripts
        $wrapperBat = Join-Path $ProjectDir ".ce-mcp-wrapper.bat"
        $wrapperPs1 = Join-Path $ProjectDir ".ce-mcp-wrapper.ps1"

        if (Test-Path $wrapperBat) {
            Write-Info "Removing wrapper script..."
            Remove-Item $wrapperBat -Force
            Write-Success "Removed .ce-mcp-wrapper.bat"
        }

        if (Test-Path $wrapperPs1) {
            Remove-Item $wrapperPs1 -Force
            Write-Success "Removed .ce-mcp-wrapper.ps1"
        }

        # Remove virtual environment if it contains ce-mcp
        $venvPath = Join-Path $ProjectDir ".venv"
        $ceMcpInVenv = Join-Path $venvPath "Scripts\ce-mcp.exe"

        if ((Test-Path $venvPath) -and (Test-Path $ceMcpInVenv)) {
            if (-not $NonInteractive) {
                $removeVenv = Read-Host "Remove virtual environment? (y/N)"
                if ($removeVenv -eq 'y' -or $removeVenv -eq 'Y') {
                    Remove-Item $venvPath -Recurse -Force
                    Write-Success "Removed virtual environment"
                }
                else {
                    # Just uninstall ce-mcp from venv
                    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
                    & $activateScript
                    pip uninstall ce-mcp -y 2>&1 | Out-Null
                    deactivate
                    Write-Success "Removed ce-mcp from virtual environment"
                }
            }
            else {
                # Just uninstall ce-mcp from venv
                $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
                & $activateScript
                pip uninstall ce-mcp -y 2>&1 | Out-Null
                deactivate
                Write-Success "Removed ce-mcp from virtual environment"
            }
        }

        # Remove configuration file
        $configPath = Join-Path $ProjectDir ".ce-mcp-config.yaml"
        if (Test-Path $configPath) {
            Write-Info "Removing .ce-mcp-config.yaml..."
            Remove-Item $configPath -Force
            Write-Success "Removed .ce-mcp-config.yaml"
        }

        Pop-Location
    }

    # Check for global installation
    if (Test-Command "pipx") {
        $pipxList = pipx list 2>$null
        if ($pipxList -match "ce-mcp") {
            Write-Info "Removing global pipx installation..."
            pipx uninstall ce-mcp 2>&1 | Out-Null
            Write-Success "Removed global ce-mcp installation"
        }
    }

    Write-Host ""
    Write-Success "Uninstall complete!"
    Write-Host ""
    Write-Host "Removed:" -ForegroundColor Yellow
    Write-Host "  [OK] ce-mcp from Claude MCP servers"
    Write-Host "  [OK] ce-mcp package from virtual environment (if present)"
    Write-Host "  [OK] Project configuration files (.ce-mcp-config.yaml, wrapper scripts)"
    Write-Host "  [OK] Global ce-mcp installation (if present)"
    Write-Host ""
    Write-Host "The ce-mcp source code remains at: $SCRIPT_DIR" -ForegroundColor Blue
}

# Main function
function Main {
    # Show help if requested
    if ($Help) {
        Show-Help
    }

    # Set project directory
    if ([string]::IsNullOrEmpty($ProjectDir)) {
        if (-not $NonInteractive) {
            Write-Header
            $inputDir = Read-Host "Enter the path to your C++/coding project (or press Enter for current directory)"
            if (-not [string]::IsNullOrEmpty($inputDir)) {
                $ProjectDir = $inputDir
            }
            else {
                $ProjectDir = Get-Location
            }
        }
        else {
            $ProjectDir = Get-Location
        }
    }

    # Convert to absolute path
    if (Test-Path $ProjectDir) {
        $ProjectDir = Resolve-Path $ProjectDir
    }
    else {
        New-Item -ItemType Directory -Path $ProjectDir -Force | Out-Null
        $ProjectDir = Resolve-Path $ProjectDir
    }

    # Handle uninstall if requested
    if ($Uninstall) {
        Uninstall-MCPServer
        exit 0
    }

    Write-Header
    Write-Info "Setting up Compiler Explorer MCP for Claude Code"
    Write-Info "Project directory: $ProjectDir "
    Write-Info "Source directory: $SCRIPT_DIR"
    if (-not $Quiet) {
        Write-Host ""
    }

    # Run setup steps
    Test-Prerequisites
    Install-MCPServer
    New-ProjectConfig
    Register-MCPServer
    Test-Installation
    Show-CompletionMessage
}

# Run main function
Main