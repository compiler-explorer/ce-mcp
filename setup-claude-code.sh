#!/bin/bash
# Claude Code Setup Script for Compiler Explorer MCP Server
# This script sets up the MCP server for use with Claude Code

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Compiler Explorer MCP Setup for Claude Code  ${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    print_header
    
    # Remember the directory where the script is located (ce-mcp source directory)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Parse command line arguments
    PROJECT_DIR=""
    GLOBAL_INSTALL=false
    GLOBAL_MCP=false
    REMOVE_OLD_MCP=false
    NON_INTERACTIVE=false
    DEFAULT_LANG="c++"
    DEFAULT_COMPILER="g++"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project-dir)
                PROJECT_DIR="$2"
                shift 2
                ;;
            --global)
                GLOBAL_INSTALL=true
                shift
                ;;
            --global-mcp)
                GLOBAL_MCP=true
                shift
                ;;
            --remove-old-mcp)
                REMOVE_OLD_MCP=true
                shift
                ;;
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            --language)
                DEFAULT_LANG="$2"
                shift 2
                ;;
            --compiler)
                DEFAULT_COMPILER="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # If no project directory specified, ask user (unless non-interactive)
    if [[ -z "$PROJECT_DIR" ]]; then
        if [[ "$NON_INTERACTIVE" == false ]]; then
            echo -e "${YELLOW}Enter the path to your C++/coding project (or press Enter for current directory):${NC}"
            read -r PROJECT_DIR
        fi
        if [[ -z "$PROJECT_DIR" ]]; then
            PROJECT_DIR="$(pwd)"
        fi
    fi
    
    # Convert to absolute path
    PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
    
    print_info "Setting up Compiler Explorer MCP for Claude Code"
    print_info "Project directory: $PROJECT_DIR"
    print_info "Source directory: $SCRIPT_DIR"
    echo ""
    
    # Step 1: Check prerequisites
    print_step "Checking prerequisites..."
    check_prerequisites
    
    # Step 2: Install the MCP server
    print_step "Installing Compiler Explorer MCP server..."
    install_mcp_server
    
    # Step 3: Create project configuration
    print_step "Creating Claude Code configuration..."
    create_claude_config
    
    # Step 4: Verify installation
    print_step "Verifying installation..."
    verify_installation
    
    # Step 5: Show success message and next steps
    show_completion_message
}

check_prerequisites() {
    local missing_deps=()
    
    # Check for Python
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    # Check for UV or pip
    if ! command_exists uv && ! command_exists pip; then
        missing_deps+=("uv or pip")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        echo ""
        print_info "Please install the missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            case $dep in
                "python3")
                    echo "  - Python 3.8+: https://python.org/downloads"
                    ;;
                "uv or pip")
                    echo "  - UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
                    echo "  - Or use pip (comes with Python)"
                    ;;
            esac
        done
        exit 1
    fi
    
    print_success "All prerequisites found"
}

install_mcp_server() {
    # Check if we're running the script from the ce-mcp development directory
    if [[ -f "$SCRIPT_DIR/pyproject.toml" ]] && grep -q "ce-mcp" "$SCRIPT_DIR/pyproject.toml"; then
        print_info "Found ce-mcp development directory at: $SCRIPT_DIR"
        
        if [[ "$GLOBAL_INSTALL" == true ]]; then
            print_info "Installing globally with pipx..."
            if ! command_exists pipx; then
                print_info "Installing pipx first..."
                if command_exists uv; then
                    uv tool install pipx
                else
                    python3 -m pip install --user pipx
                fi
            fi
            
            pipx install "$SCRIPT_DIR"
            CE_MCP_COMMAND="ce-mcp"
        else
            # Check if we're already in the source directory
            if [[ "$PROJECT_DIR" == "$SCRIPT_DIR" ]]; then
                print_info "Installing in development mode in source directory..."
                cd "$SCRIPT_DIR"
                
                if command_exists uv; then
                    if [[ ! -d ".venv" ]]; then
                        uv venv --seed
                    fi
                    source .venv/bin/activate
                    uv pip install -e .
                else
                    if [[ ! -d ".venv" ]]; then
                        python3 -m venv .venv
                    fi
                    source .venv/bin/activate
                    pip install -e .
                fi
                
                CE_MCP_COMMAND="$SCRIPT_DIR/.venv/bin/ce-mcp"
            else
                print_info "Installing in project environment from source: $SCRIPT_DIR"
                cd "$PROJECT_DIR"
                
                if command_exists uv; then
                    if [[ ! -d ".venv" ]]; then
                        uv venv --seed
                    fi
                    source .venv/bin/activate
                    uv pip install -e "$SCRIPT_DIR"
                else
                    if [[ ! -d ".venv" ]]; then
                        python3 -m venv .venv
                    fi
                    source .venv/bin/activate
                    pip install -e "$SCRIPT_DIR"
                fi
                
                CE_MCP_COMMAND="ce-mcp"
            fi
        fi
    else
        print_error "Cannot find ce-mcp source at: $SCRIPT_DIR"
        print_error "Please ensure the script is in the ce-mcp directory with pyproject.toml"
        exit 1
    fi
    
    print_success "MCP server installed successfully"
}

create_claude_config() {
    cd "$PROJECT_DIR"
    
    # Use absolute path to ce-mcp command
    if [[ -f "$PROJECT_DIR/.venv/bin/ce-mcp" ]]; then
        CE_MCP_PATH="$PROJECT_DIR/.venv/bin/ce-mcp"
    else
        CE_MCP_PATH="ce-mcp"
    fi
    
    CLAUDE_DIR="$HOME/.claude"
    CLAUDE_GLOBAL_CONFIG="$HOME/.claude.json"
    CLAUDE_SETTINGS="$CLAUDE_DIR/settings.json"
    
    mkdir -p "$CLAUDE_DIR"
    
    if [[ "$GLOBAL_MCP" == true ]]; then
        print_info "Creating global Claude Code MCP configuration..."
        
        # Create backup of global config if it exists
        if [[ -f "$CLAUDE_GLOBAL_CONFIG" ]]; then
            cp "$CLAUDE_GLOBAL_CONFIG" "$CLAUDE_GLOBAL_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
            print_info "Backup created: $CLAUDE_GLOBAL_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Install MCP server globally in ~/.claude.json
        python3 -c "
import json
import os

config_file = '$CLAUDE_GLOBAL_CONFIG'
config = {}

# Load existing config if it exists
if os.path.exists(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except:
        config = {}

# Add or update mcpServers
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Remove old compiler-explorer MCP if requested
remove_old = '$REMOVE_OLD_MCP' == 'true'
if remove_old and 'compiler-explorer' in config['mcpServers']:
    print('Removing old compiler-explorer MCP server...')
    del config['mcpServers']['compiler-explorer']

config['mcpServers']['ce-mcp'] = {
    'command': '$CE_MCP_PATH',
    'args': ['--config', '$PROJECT_DIR/.ce-mcp-config.yaml']
}

# Save updated config
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

if remove_old:
    print('Old compiler-explorer MCP removed and ce-mcp added successfully')
else:
    print('Global MCP server configuration added successfully')
"
        
        print_success "Global MCP configuration created"
        print_info "  - $CLAUDE_GLOBAL_CONFIG (global MCP server configuration)"
        
    else
        print_info "Creating Claude Code project configuration..."
        
        # Create project-specific .claude.json file for Claude Code
        cat > .claude.json << EOF
{
  "mcp_servers": {
    "ce-mcp": {
      "command": "$CE_MCP_PATH",
      "args": ["--config", "./.ce-mcp-config.yaml"]
    }
  }
}
EOF
        
        # Configure global settings for auto-approval
        print_info "Configuring Claude Code global settings for MCP auto-approval..."
        
        # Check if settings file exists and merge, otherwise create new
        if [[ -f "$CLAUDE_SETTINGS" ]]; then
            print_info "Found existing Claude Code settings, updating..."
            
            # Create backup
            cp "$CLAUDE_SETTINGS" "$CLAUDE_SETTINGS.backup.$(date +%Y%m%d_%H%M%S)"
            print_info "Backup created: $CLAUDE_SETTINGS.backup.$(date +%Y%m%d_%H%M%S)"
            
            # Use Python to safely update JSON
            python3 -c "
import json
try:
    with open('$CLAUDE_SETTINGS') as f:
        data = json.load(f)
    data['enableAllProjectMcpServers'] = True
    with open('$CLAUDE_SETTINGS', 'w') as f:
        json.dump(data, f, indent=2)
except:
    # Fallback if parsing fails
    with open('$CLAUDE_SETTINGS', 'w') as f:
        f.write('{\"enableAllProjectMcpServers\": true}')
"
        else
            print_info "Creating new Claude Code settings file..."
            cat > "$CLAUDE_SETTINGS" << EOF
{
  "enableAllProjectMcpServers": true
}
EOF
        fi
        
        print_success "Project MCP configuration created"
        print_info "  - .claude.json (project MCP server configuration)"
    fi
    
    # Create .ce-mcp-config.yaml with interactive prompts
    print_info "Creating .ce-mcp-config.yaml..."
    
    if [[ "$NON_INTERACTIVE" == false ]]; then
        # Ask for default language
        echo -e "${YELLOW}What's your primary programming language? (c++/c/rust/go/python) [c++]:${NC}"
        read -r INPUT_LANG
        DEFAULT_LANG=${INPUT_LANG:-"c++"}
        
        # Ask for default compiler
        case $DEFAULT_LANG in
            "c++"|"c")
                echo -e "${YELLOW}Preferred compiler? (g++/clang++) [g++]:${NC}"
                read -r INPUT_COMPILER
                DEFAULT_COMPILER=${INPUT_COMPILER:-"g++"}
                ;;
            "rust")
                DEFAULT_COMPILER="rustc"
                ;;
            "go")
                DEFAULT_COMPILER="go"
                ;;
            "python")
                DEFAULT_COMPILER="python311"
                ;;
            *)
                DEFAULT_COMPILER="g++"
                ;;
        esac
    else
        # Set compiler based on language for non-interactive mode
        case $DEFAULT_LANG in
            "c++"|"c")
                DEFAULT_COMPILER=${DEFAULT_COMPILER:-"g++"}
                ;;
            "rust")
                DEFAULT_COMPILER="rustc"
                ;;
            "go")
                DEFAULT_COMPILER="go"
                ;;
            "python")
                DEFAULT_COMPILER="python311"
                ;;
            *)
                DEFAULT_COMPILER="g++"
                ;;
        esac
        print_info "Using language: $DEFAULT_LANG, compiler: $DEFAULT_COMPILER"
    fi
    
    # Create configuration file
    cat > .ce-mcp-config.yaml << EOF
# Project-specific Compiler Explorer MCP configuration
compiler_explorer_mcp:
  api:
    timeout: 30
    
  defaults:
    language: "$DEFAULT_LANG"
    compiler: "$DEFAULT_COMPILER"
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
EOF
    
    print_success "Configuration files created"
    print_info "  - .claude.json (MCP server configuration)"
    print_info "  - .ce-mcp-config.yaml (project settings)"
}

verify_installation() {
    cd "$PROJECT_DIR"
    
    # Test that ce-mcp command works
    if [[ -f ".venv/bin/ce-mcp" ]]; then
        print_info "Testing local installation..."
        source .venv/bin/activate
        if .venv/bin/ce-mcp --help > /dev/null 2>&1; then
            print_success "ce-mcp command works correctly"
        else
            print_error "ce-mcp command failed"
            exit 1
        fi
    elif command_exists ce-mcp; then
        print_info "Testing global installation..."
        if ce-mcp --help > /dev/null 2>&1; then
            print_success "ce-mcp command works correctly"
        else
            print_error "ce-mcp command failed"
            exit 1
        fi
    else
        print_error "ce-mcp command not found"
        exit 1
    fi
    
    # Check configuration files
    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
    if [[ -f "$PROJECT_DIR/.claude.json" ]] && [[ -f "$PROJECT_DIR/.ce-mcp-config.yaml" ]]; then
        print_success "Configuration files created successfully"
        print_info "  - $PROJECT_DIR/.claude.json (project MCP configuration)"
        print_info "  - $PROJECT_DIR/.ce-mcp-config.yaml (project settings)"
        if [[ -f "$CLAUDE_SETTINGS" ]]; then
            print_info "  - $CLAUDE_SETTINGS (global settings with auto-approval)"
        fi
    else
        print_error "Configuration files missing"
        exit 1
    fi
}

show_completion_message() {
    echo ""
    print_success "🎉 Setup complete!"
    echo ""
    echo -e "${GREEN}Your project is now configured for Claude Code with Compiler Explorer MCP!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Open your project in Claude Code"
    echo "2. Try using the MCP tools:"
    echo "   @compiler-explorer compile_check_tool source=\"int main(){return 0;}\" language=\"$DEFAULT_LANG\" compiler=\"$DEFAULT_COMPILER\""
    echo ""
    echo -e "${YELLOW}Configuration files created:${NC}"
    echo "  📄 .claude.json - Project MCP server configuration"
    echo "  ⚙️  .ce-mcp-config.yaml - Project-specific settings"
    echo "  🌐 ~/.claude/settings.json - Global settings with auto-approval"
    echo ""
    echo -e "${YELLOW}Available tools:${NC}"
    echo "  🔍 compile_check_tool - Quick syntax validation"
    echo "  🚀 compile_and_run_tool - Compile and execute code"
    echo "  🐛 compile_with_diagnostics_tool - Detailed error analysis"
    echo "  ⚡ analyze_optimization_tool - Assembly optimization analysis"
    echo "  🔗 generate_share_url_tool - Create shareable links"
    echo "  📊 compare_compilers_tool - Side-by-side compiler comparison"
    echo ""
    echo -e "${BLUE}Happy coding! 🚀${NC}"
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Setup Compiler Explorer MCP server for Claude Code"
    echo ""
    echo "Options:"
    echo "  --project-dir DIR    Target project directory (default: current directory)"
    echo "  --global            Install globally with pipx instead of project-local"
    echo "  --global-mcp        Install MCP server globally instead of per-project"
    echo "  --remove-old-mcp    Remove existing 'compiler-explorer' MCP server"
    echo "  --non-interactive   Skip interactive prompts, use defaults"
    echo "  --language LANG     Default language (c++, c, rust, go, python)"
    echo "  --compiler COMP     Default compiler (g++, clang++, rustc, etc.)"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Setup in current directory"
    echo "  $0 --project-dir ~/my-cpp-project    # Setup in specific project"
    echo "  $0 --global                          # Install globally"
    echo "  $0 --global-mcp                      # Install MCP globally (available everywhere)"
    echo "  $0 --global-mcp --remove-old-mcp     # Replace old MCP with new one"
    echo "  $0 --non-interactive                 # Use defaults without prompts"
    echo "  $0 --language rust --compiler rustc  # Setup for Rust"
}

# Run main function
main "$@"