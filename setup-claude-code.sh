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
    if [[ "$QUIET" != true ]]; then
        echo -e "${BLUE}================================================${NC}"
        echo -e "${BLUE}  Compiler Explorer MCP Setup for Claude Code  ${NC}"
        echo -e "${BLUE}================================================${NC}"
        echo ""
    fi
}

print_step() {
    if [[ "$QUIET" != true ]]; then
        echo -e "${GREEN}[STEP]${NC} $1"
    fi
}

print_info() {
    if [[ "$QUIET" != true ]]; then
        echo -e "${YELLOW}[INFO]${NC} $1"
    fi
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_success() {
    if [[ "$QUIET" != true ]]; then
        echo -e "${GREEN}[SUCCESS]${NC} $1"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    # Remember the directory where the script is located (ce-mcp source directory)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Parse command line arguments
    PROJECT_DIR=""
    GLOBAL_INSTALL=false
    GLOBAL_MCP=false
    NON_INTERACTIVE=false
    QUIET=false
    DEFAULT_LANG="c++"
    DEFAULT_COMPILER="g++"
    UNINSTALL=false
    MCP_NAME="ce-mcp"

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
            --non-interactive)
                NON_INTERACTIVE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
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
            --uninstall)
                UNINSTALL=true
                shift
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

    print_header

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
    if [[ -d "$PROJECT_DIR" ]]; then
        PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
    else
        mkdir -p "$PROJECT_DIR"
        PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
    fi

    # Handle uninstall if requested
    if [[ "$UNINSTALL" == true ]]; then
        uninstall_mcp_server
        exit 0
    fi

    print_info "Setting up Compiler Explorer MCP for Claude Code"
    print_info "Project directory: $PROJECT_DIR"
    print_info "Source directory: $SCRIPT_DIR"
    if [[ "$QUIET" != true ]]; then
        echo ""
    fi

    # Step 1: Check prerequisites
    print_step "Checking prerequisites..."
    check_prerequisites

    # Step 2: Install the MCP server
    print_step "Installing Compiler Explorer MCP server..."
    install_mcp_server

    # Step 3: Create project configuration
    print_step "Creating project configuration..."
    create_project_config

    # Step 4: Register MCP server with Claude
    print_step "Registering MCP server with Claude..."
    register_mcp_server

    # Step 5: Verify installation
    print_step "Verifying installation..."
    verify_installation

    # Step 6: Show success message and next steps
    show_completion_message
}

check_prerequisites() {
    local missing_deps=()

    # Check for Python
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi

    # Check for Claude CLI
    if ! command_exists claude; then
        missing_deps+=("claude")
    fi

    # Check for UV or pip
    if ! command_exists uv && ! command_exists pip; then
        missing_deps+=("uv or pip")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        if [[ "$QUIET" != true ]]; then
            echo ""
        fi
        print_info "Please install the missing dependencies:"
        if [[ "$QUIET" != true ]]; then
            for dep in "${missing_deps[@]}"; do
                case $dep in
                    "python3")
                        echo "  - Python 3.8+: https://python.org/downloads"
                        ;;
                    "claude")
                        echo "  - Claude Code: https://claude.ai/download"
                        ;;
                    "uv or pip")
                        echo "  - UV: curl -LsSf https://astral.sh/uv/install.sh | sh"
                        echo "  - Or use pip (comes with Python)"
                        ;;
                esac
            done
        fi
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
                    python3 -m pipx ensurepath
                fi
            fi

            # Install with pipx
            pipx install "$SCRIPT_DIR"
            CE_MCP_COMMAND="ce-mcp"

        else
            print_info "Installing in project environment from source: $SCRIPT_DIR"
            cd "$PROJECT_DIR"

            # Create virtual environment if it doesn't exist
            if [[ ! -d ".venv" ]]; then
                if command_exists uv; then
                    if [[ "$QUIET" == true ]]; then
                        uv venv --seed >/dev/null 2>&1
                    else
                        uv venv --seed
                    fi
                else
                    if [[ "$QUIET" == true ]]; then
                        python3 -m venv .venv >/dev/null 2>&1
                    else
                        python3 -m venv .venv
                    fi
                fi
            fi

            # Install ce-mcp in the virtual environment
            if command_exists uv; then
                source .venv/bin/activate
                if [[ "$QUIET" == true ]]; then
                    uv pip install -e "$SCRIPT_DIR" >/dev/null 2>&1
                else
                    uv pip install -e "$SCRIPT_DIR"
                fi
                deactivate
            else
                source .venv/bin/activate
                if [[ "$QUIET" == true ]]; then
                    pip install -e "$SCRIPT_DIR" >/dev/null 2>&1
                else
                    pip install -e "$SCRIPT_DIR"
                fi
                deactivate
            fi

            # Use a wrapper script that activates venv first
            CE_MCP_WRAPPER="$PROJECT_DIR/.ce-mcp-wrapper.sh"
            cat > "$CE_MCP_WRAPPER" << 'EOF'
#!/bin/bash
# Wrapper script for ce-mcp that activates the virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
exec ce-mcp "$@"
EOF
            chmod +x "$CE_MCP_WRAPPER"
            CE_MCP_COMMAND="$CE_MCP_WRAPPER"
        fi
    else
        print_error "Cannot find ce-mcp source at: $SCRIPT_DIR"
        print_error "Please ensure the script is in the ce-mcp directory with pyproject.toml"
        exit 1
    fi

    print_success "MCP server installed successfully"
}

create_project_config() {
    cd "$PROJECT_DIR"

    # Create .ce-mcp-config.yaml with interactive prompts
    print_info "Creating project configuration..."

    if [[ "$NON_INTERACTIVE" == false ]] && [[ "$QUIET" != true ]]; then
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
    cat > "$PROJECT_DIR/.ce-mcp-config.yaml" << EOF
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

    print_success "Configuration file created: .ce-mcp-config.yaml"
}

register_mcp_server() {
    # First remove any existing ce-mcp server
    print_info "Checking for existing ce-mcp server..."
    if claude mcp list 2>/dev/null | grep -q "$MCP_NAME"; then
        print_info "Removing existing $MCP_NAME server..."
        claude mcp remove "$MCP_NAME" >/dev/null 2>&1 || true
    fi

    # Register the MCP server using claude mcp add
    # The arguments after the command are passed to the MCP server
    CONFIG_PATH="$PROJECT_DIR/.ce-mcp-config.yaml"

    # Determine scope message
    if [[ "$GLOBAL_MCP" == true ]]; then
        print_info "Registering MCP server globally..."
    else
        print_info "Registering MCP server for this project..."
    fi

    # Register with claude mcp add
    # Use -- to separate claude mcp options from MCP server arguments
    if [[ "$QUIET" == true ]]; then
        if claude mcp add "$MCP_NAME" "$CE_MCP_COMMAND" -- "--config" "$CONFIG_PATH" >/dev/null 2>&1; then
            print_success "MCP server registered successfully with Claude"
        else
            print_error "Failed to register MCP server"
            print_info "You can try manually registering with:"
            echo "  claude mcp add \"$MCP_NAME\" \"$CE_MCP_COMMAND\" -- --config \"$CONFIG_PATH\""
            exit 1
        fi
    else
        if claude mcp add "$MCP_NAME" "$CE_MCP_COMMAND" -- "--config" "$CONFIG_PATH"; then
            print_success "MCP server registered successfully with Claude"
        else
            print_error "Failed to register MCP server"
            print_info "You can try manually registering with:"
            echo "  claude mcp add \"$MCP_NAME\" \"$CE_MCP_COMMAND\" -- --config \"$CONFIG_PATH\""
            exit 1
        fi
    fi
}

verify_installation() {
    cd "$PROJECT_DIR"

    # Test that the MCP command works
    print_info "Testing MCP server command..."

    if [[ -f "$CE_MCP_WRAPPER" ]]; then
        # Test wrapper script
        if "$CE_MCP_WRAPPER" --help > /dev/null 2>&1; then
            print_success "MCP wrapper script works correctly"
        else
            print_error "MCP wrapper script failed"
            exit 1
        fi
    elif command_exists ce-mcp; then
        # Test global installation
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

    # Check that MCP server is registered with Claude
    print_info "Verifying MCP registration..."
    if claude mcp list 2>/dev/null | grep -q "$MCP_NAME"; then
        print_success "MCP server is registered with Claude"

        # Show MCP server details
        if [[ "$QUIET" != true ]]; then
            echo ""
            print_info "MCP server details:"
            claude mcp get "$MCP_NAME" 2>/dev/null || true
        fi
    else
        print_error "MCP server not found in Claude configuration"
        exit 1
    fi

    # Check configuration file
    if [[ -f "$PROJECT_DIR/.ce-mcp-config.yaml" ]]; then
        print_success "Configuration file exists: .ce-mcp-config.yaml"
    else
        print_error "Configuration file missing"
        exit 1
    fi
}

show_completion_message() {
    if [[ "$QUIET" != true ]]; then
        echo ""
        print_success "🎉 Setup complete!"
        echo ""
        echo -e "${GREEN}Your project is now configured for Claude Code with Compiler Explorer MCP!${NC}"
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Restart Claude Code (or reload the window)"
        echo "2. The MCP server should be automatically available"
        echo "3. Try using the MCP tools with @$MCP_NAME:"
        echo ""
        echo -e "${YELLOW}Example usage:${NC}"
        echo "  Ask Claude: \"@$MCP_NAME compile and run this code: int main(){return 0;}\""
        echo ""
        echo -e "${YELLOW}Configuration:${NC}"
        if [[ "$GLOBAL_MCP" == true ]]; then
            echo "  📄 MCP server registered globally (available in all projects)"
        else
            echo "  📄 MCP server registered for this project"
        fi
        echo "  ⚙️  .ce-mcp-config.yaml - Project-specific settings"
        echo ""
        echo -e "${YELLOW}Available tools via @$MCP_NAME:${NC}"
        echo "  🔍 compile_check_tool - Quick syntax validation"
        echo "  🚀 compile_and_run_tool - Compile and execute code"
        echo "  🐛 compile_with_diagnostics_tool - Detailed error analysis"
        echo "  ⚡ analyze_optimization_tool - Assembly optimization analysis"
        echo "  🔗 generate_share_url_tool - Create shareable links"
        echo "  📊 compare_compilers_tool - Side-by-side compiler comparison"
        echo ""
        echo -e "${YELLOW}Managing the MCP server:${NC}"
        echo "  claude mcp list              - List all MCP servers"
        echo "  claude mcp get $MCP_NAME     - Show server details"
        echo "  claude mcp remove $MCP_NAME  - Remove the server"
        echo ""
        echo -e "${BLUE}Happy coding! 🚀${NC}"
    fi
}

uninstall_mcp_server() {
    print_header
    print_info "Uninstalling Compiler Explorer MCP server..."
    echo ""

    # Remove MCP server from Claude (try all scopes)
    if command_exists claude; then
        # Check and remove from project scope
        cd "$PROJECT_DIR" 2>/dev/null || true
        if claude mcp list 2>/dev/null | grep -q "$MCP_NAME"; then
            print_info "Removing $MCP_NAME from Claude (project scope)..."
            claude mcp remove "$MCP_NAME" 2>/dev/null || true
            print_success "Removed $MCP_NAME from Claude project configuration"
        fi

        # Note: Current Claude CLI doesn't support scope option
        # Global removal would need to be done manually if needed
    fi

    # Remove from project directory
    if [[ -d "$PROJECT_DIR" ]]; then
        cd "$PROJECT_DIR"

        # Remove wrapper script
        if [[ -f ".ce-mcp-wrapper.sh" ]]; then
            print_info "Removing wrapper script..."
            rm -f .ce-mcp-wrapper.sh
            print_success "Removed .ce-mcp-wrapper.sh"
        fi

        # Remove virtual environment if it contains ce-mcp
        if [[ -d ".venv" ]] && [[ -f ".venv/bin/ce-mcp" ]]; then
            if [[ "$NON_INTERACTIVE" == false ]]; then
                echo -e "${YELLOW}Remove virtual environment? (y/N):${NC}"
                read -r REMOVE_VENV
                if [[ "$REMOVE_VENV" =~ ^[Yy]$ ]]; then
                    rm -rf .venv
                    print_success "Removed virtual environment"
                else
                    # Just uninstall ce-mcp from venv
                    source .venv/bin/activate
                    pip uninstall ce-mcp -y 2>/dev/null || true
                    deactivate
                    print_success "Removed ce-mcp from virtual environment"
                fi
            else
                # Just uninstall ce-mcp from venv
                source .venv/bin/activate
                pip uninstall ce-mcp -y 2>/dev/null || true
                deactivate
                print_success "Removed ce-mcp from virtual environment"
            fi
        fi

        # Remove configuration file
        if [[ -f ".ce-mcp-config.yaml" ]]; then
            print_info "Removing .ce-mcp-config.yaml..."
            rm -f .ce-mcp-config.yaml
            print_success "Removed .ce-mcp-config.yaml"
        fi

        # Remove old .claude.json if it exists and contains ce-mcp
        if [[ -f ".claude.json" ]] && grep -q "ce-mcp" .claude.json 2>/dev/null; then
            print_info "Found old .claude.json with ce-mcp configuration..."
            if [[ "$NON_INTERACTIVE" == false ]]; then
                echo -e "${YELLOW}Remove .claude.json? (y/N):${NC}"
                read -r REMOVE_CONFIG
                if [[ "$REMOVE_CONFIG" =~ ^[Yy]$ ]]; then
                    rm -f .claude.json
                    print_success "Removed .claude.json"
                fi
            else
                rm -f .claude.json
                print_success "Removed .claude.json"
            fi
        fi
    fi

    # Check for global installation
    if command_exists pipx; then
        if pipx list 2>/dev/null | grep -q "ce-mcp"; then
            print_info "Removing global pipx installation..."
            pipx uninstall ce-mcp 2>/dev/null || true
            print_success "Removed global ce-mcp installation"
        fi
    fi

    echo ""
    print_success "Uninstall complete!"
    echo ""
    echo -e "${YELLOW}Removed:${NC}"
    echo "  ✓ $MCP_NAME from Claude MCP servers"
    echo "  ✓ ce-mcp package from virtual environment (if present)"
    echo "  ✓ Project configuration files (.ce-mcp-config.yaml, wrapper script)"
    echo "  ✓ Global ce-mcp installation (if present)"
    echo ""
    echo -e "${BLUE}The ce-mcp source code remains at: $SCRIPT_DIR${NC}"
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Setup or uninstall Compiler Explorer MCP server for Claude Code"
    echo ""
    echo "Options:"
    echo "  --project-dir DIR    Target project directory (default: current directory)"
    echo "  --global            Install ce-mcp globally with pipx instead of project-local"
    echo "  --global-mcp        Register MCP server globally (available in all projects)"
    echo "  --non-interactive   Skip interactive prompts, use defaults"
    echo "  -q, --quiet         Quiet mode: no output except errors"
    echo "  --language LANG     Default language (c++, c, rust, go, python)"
    echo "  --compiler COMP     Default compiler (g++, clang++, rustc, etc.)"
    echo "  --uninstall         Uninstall ce-mcp and remove configuration"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Setup in current directory"
    echo "  $0 --project-dir ~/my-cpp-project    # Setup in specific project"
    echo "  $0 --global                          # Install ce-mcp globally"
    echo "  $0 --global-mcp                      # Register MCP globally (all projects)"
    echo "  $0 --non-interactive                 # Use defaults without prompts"
    echo "  $0 -q                                # Quiet setup with no output"
    echo "  $0 --language rust --compiler rustc  # Setup for Rust"
    echo "  $0 --uninstall                       # Uninstall ce-mcp"
    echo ""
    echo "The script will:"
    echo "  1. Install the ce-mcp Python package"
    echo "  2. Create project configuration (.ce-mcp-config.yaml)"
    echo "  3. Register the MCP server with Claude using 'claude mcp add'"
    echo "  4. Verify the installation"
    echo ""
    echo "After setup, the MCP server will be available in Claude Code via @ce-mcp"
}

# Run main function
main "$@"