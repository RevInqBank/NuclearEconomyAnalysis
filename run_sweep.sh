#!/bin/bash

# Activate 'econ' environment
# Using hook to ensure conda command is available in script
eval "$(conda shell.bash hook)"
conda activate econ

# Verify python env
echo "Using Python: $(which python)"

echo "Starting Parameter Sweep..."
python run_sweep.py
echo "Sweep Finished. Check sweep_summary_formatted.csv and other csv files."
