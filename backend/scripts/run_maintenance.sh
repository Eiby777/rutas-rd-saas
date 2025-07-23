#!/bin/bash
# Maintenance script for Rutas RD SaaS
# Usage: ./run_maintenance.sh [cleanup|reminders|backup|all]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE_DIR"

# Activate virtual environment if exists
VENV_PATH="${VENV_PATH:-$BASE_DIR/venv}"
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓${NC} Activated virtual environment: $VENV_PATH"
fi

# Set Django settings module
export DJANGO_SETTINGS_MODULE="config.settings.local"

# Log directory
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

# Function to run a maintenance command
run_command() {
    local cmd=$1
    local log_file="$LOG_DIR/$(date +%Y%m%d)_${cmd}.log"
    
    echo -e "\n${YELLOW}Running $cmd...${NC}"
    echo "Started at: $(date)" | tee -a "$log_file"
    
    if [ "$cmd" = "backup" ]; then
        python -m scripts.maintenance backup --output-dir "$BASE_DIR/backups" 2>&1 | tee -a "$log_file"
    else
        python -m scripts.maintenance "$cmd" 2>&1 | tee -a "$log_file"
    fi
    
    local status=${PIPESTATUS[0]}
    echo "Completed at: $(date)" | tee -a "$log_file"
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $cmd completed successfully"
        return 0
    else
        echo -e "❌ $cmd failed with status $status"
        return $status
    fi
}

# Process command line arguments
case "$1" in
    cleanup|reminders|backup)
        run_command "$1"
        ;;
    all)
        run_command "cleanup"
        run_command "reminders"
        run_command "backup"
        ;;
    *)
        echo "Usage: $0 [cleanup|reminders|backup|all]"
        exit 1
        ;;
esac

exit 0
