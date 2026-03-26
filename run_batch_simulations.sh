#!/bin/bash

# Configuration
PROJECT_DIR="/home/sonOfMaaJo/project_memory/cergy_simulation"
VENV_PATH="/home/sonOfMaaJo/.venv/bin/python3"
RESULTS_DIR="$PROJECT_DIR/results"
DATE=$(date '+%Y-%m-%d_%H-%M-%S')

# Create results directory
mkdir -p "$RESULTS_DIR"

# Usage check
if [ "$1" != "test" ] && [ "$1" != "prod" ]; then
    echo "Usage: ./run_batch_simulations.sh [test|prod]"
    echo "  test: Runs a quick simulation with 1,000 passengers"
    echo "  prod: Runs the full simulation with 1,000,000 passengers"
    exit 1
fi

MODE=$1
LOG_FILE="$RESULTS_DIR/sim_${MODE}_$DATE.log"

if [ "$MODE" == "test" ]; then
    PASSENGERS=1000
    DRIVERS=200
    echo "--- STARTING TEST SIMULATION (1,000 agents) ---" | tee -a "$LOG_FILE"
else
    PASSENGERS=1000000
    DRIVERS=200000
    echo "--- STARTING PRODUCTION SIMULATION (1,000,000 agents) ---" | tee -a "$LOG_FILE"
    echo "WARNING: This will take several hours and require ~12GB+ of RAM." | tee -a "$LOG_FILE"
fi

# Function to run a city
run_sim() {
    CITY=$1
    STATE=$2
    
    echo "[$(date '+%H:%M:%S')] Running $CITY..." | tee -a "$LOG_FILE"
    
    export PYTHONPATH=$PYTHONPATH:$PROJECT_DIR
    $VENV_PATH "$PROJECT_DIR/main.py" \
        --city "$CITY" \
        --state "$STATE" \
        --country "USA" \
        --passengers "$PASSENGERS" \
        --drivers "$DRIVERS" >> "$LOG_FILE" 2>&1
        
    echo "[$(date '+%H:%M:%S')] Finished $CITY." | tee -a "$LOG_FILE"
}

# EXECUTION (Example with Chicago)
run_sim "Chicago" "IL"

echo "--- PROCESS COMPLETED ($MODE) ---" | tee -a "$LOG_FILE"
echo "Results and logs are available in: $LOG_FILE"
