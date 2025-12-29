# Economic Analysis Code

This project provides a Python-based tool for performing economic analysis of nuclear reactor projects. It calculates Levelized Cost of Electricity (LCOE), cash flows, and other financial metrics based on reactor configurations and economic parameters.

## Features

- **Reactor Configuration**: Flexible configuration via YAML.
- **Cost Estimation**: Calculates Equilibrium (EQ) costs and Construction costs.
- **Financial modeling**: Generates detailed Cash Flow Statements (CFS), LCOE, IRR, and Break-Even Point (BEP) analysis.
- **Scenario Analysis**: Supports different countries and scaling factors.

## Project Structure

```text
econ_code/
├── main.py                 # Main entry point for the analysis
├── requirements.txt        # Python dependencies
├── input/
│   ├── code/               # Logic modules (Reactor selection, Fuel cost, etc.)
│   └── data/
│       ├── input.yaml      # User configuration (Reactor specs, Financial params)
│       └── SOURCE_DATA.xlsx # Base cost data, curves, and parameters
└── output/
    └── CFS.xlsx            # Generated Cash Flow Statement and results
```

## Installation

1.  **Prerequisites**: Python 3.8+ recommended.
2.  **Install Dependencies**:
    It is recommended to use a virtual environment.

    ```bash
    pip install -r requirements.txt
    ```

    *Note: Dependencies include `pandas`, `numpy`, `matplotlib`, `numpy-financial`, and `openpyxl`.*

## Usage

1.  **Configure the Analysis**:
    Edit `input/data/input.yaml` to set your reactor parameters (Power Density, Core size, etc.) and financial assumptions (Interest rate, Loan tenor, etc.).

2.  **Run the Script**:
    Execute the main script from the project root:

    ```bash
    python main.py
    ```

3.  **View Results**:
    The results will be printed to the console (LCOE summary) and saved to:
    - `output/CFS.xlsx`: Detailed Cash Flow Statement.

## Logic Overview

The analysis moves through specific steps defined in `main.py`:
1.  **Read Inputs**: Loads YAML config and Excel source data.
2.  **Reactor Selection**: Calculates physical core parameters.
3.  **EQ Cost & Construction Cost**: Scales costs based on module number and capacity.
4.  **CAPEX**: Distributes costs over the construction schedule.
5.  **Cash Flow**: Generates the full financial model (Revenue, O&M, Fuel, Service Debt, Tax).
6.  **Analysis**: Computes final metrics (LCOE, IRR).
