
import subprocess
import pandas as pd
import sys
import os

def run_single_simulation(reactor, mwe):
    """Runs a single simulation and returns the parsed result dict."""
    print(f"Running {reactor} at {mwe} MWe...")
    try:
        # Run main_for_loop.py with arguments
        cmd = [sys.executable, "main_for_loop.py", "--reactor", reactor, "--target_mwe", str(mwe)]
        
        # Capture output
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running {reactor} {mwe}: {result.stderr}")
            return None
        
        output = result.stdout
        
        # Parse output
        # Capture key-value pairs from the entire output
        # We expect lines like "Key: Value"
        parsed_data = {}
        
        lines = output.splitlines()
        
        # We want to capture specific keys from the config dump at the start
        # and the result metrics at the end.
        
        # List of config keys we want to ensure we capture if present
        config_keys = ["powerDensity", "capacityFactor", "plantLifetime", "BatchNumber", "BatchCycleLength", "totalFuelQty", "U3O8Price", "EnrichmentPrice", "FabricationPrice", "ConversionPrice"]
        
        # List of result keys we definitely want
        result_keys = [
            "LCOE_TOTAL", "LCOE_CON", "LCOE_OM", "LCOE_FUEL", "LCOE_FUEL_IS",
            "LCOE_U3O8", "LCOE_Conversion", "LCOE_Enrichment", "LCOE_Fabrication",
            "Average EFPD", "Average Discharged_BU", "ThermalCapacityPerModule",
            "ElectricCapacityPerModule", "BaseMWe", "ModifiedPowerDensity"
        ]

        for line in lines:
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val_str = parts[1].strip().split()[0] # Take first token (remove units like [days])
                    
                    try:
                        val = float(val_str)
                        parsed_data[key] = val
                    except ValueError:
                        # Keep string values for some config items if needed, mostly we care about numbers
                        parsed_data[key] = val_str

        # Check if we successfully parsed LCOE_TOTAL (indicator of success)
        if "LCOE_TOTAL" in parsed_data:
            row = {
                "Reactor": reactor,
                "MWe": mwe,
            }
            
            # Add strictly defined result keys
            for k in result_keys:
                if k in parsed_data:
                    row[k] = parsed_data[k]
                else:
                    row[k] = None
                    
            # Add interesting config keys
            for k in config_keys:
                 if k in parsed_data:
                    row[k] = parsed_data[k]

            return row
        else:
            print(f"Could not parse LCOE output for {reactor} {mwe}")
            return None

    except Exception as e:
        print(f"Exception for {reactor} {mwe}: {e}")
        return None

def run_sweep():
    reactors = ["APR1400", "AP1000", "NuScale", "SMART", "SNU"]
    mwe_targets = list(range(100, 1100, 100))
    
    results = []

    print("Starting Sweep...")
    
    for reactor in reactors:
        for mwe in mwe_targets:
            res = run_single_simulation(reactor, mwe)
            if res:
                results.append(res)
    
    # Process results into tables
    if not results:
        print("No results collected.")
        return

    df_results = pd.DataFrame(results)
    
    # Define output directory
    output_dir = "output/lcoe_power"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save raw results first (contains everything including defaults)
    df_results.to_csv(os.path.join(output_dir, "sweep_results_raw.csv"), index=False)

    # 1. Total LCOE Table with MWth rows (Formatted)
    mwe_cols = sorted(list(set(df_results['MWe'])))
    
    print("\n[ LCOE TOTAL SUMMARY ]")
    header = ["Reactor / MWe"] + [str(m) for m in mwe_cols]
    print("\t".join(header))
    
    rows_for_csv = [header]

    for reactor in reactors:
        df_r = df_results[df_results['Reactor'] == reactor]
        
        # LCOE Row and MWth Row
        lcoe_vals = []
        mwth_vals = []
        for mwe in mwe_cols:
            row = df_r[df_r['MWe'] == mwe]
            if not row.empty:
                val = row.iloc[0]['LCOE_TOTAL']
                mwth = row.iloc[0]['ThermalCapacityPerModule']
                lcoe_vals.append(f"{val:.2f}" if pd.notnull(val) else "-")
                mwth_vals.append(f"{mwth:.2f}" if pd.notnull(mwth) else "-")
            else:
                lcoe_vals.append("-")
                mwth_vals.append("-")
        
        lcoe_line = [reactor] + lcoe_vals
        mwth_line = ["MWth"] + mwth_vals
        
        print("\t".join(mwth_line))
        print("\t".join(lcoe_line))
        
        rows_for_csv.append(mwth_line)
        rows_for_csv.append(lcoe_line)

    with open(os.path.join(output_dir, "sweep_summary_formatted.csv"), "w") as f:
        for row in rows_for_csv:
            f.write(",".join(row) + "\n")
    
    # 2. Component Tables (Pivot) - Now including detailed Fuel components
    components = [
        "LCOE_CON", "LCOE_OM", "LCOE_FUEL", "LCOE_FUEL_IS",
        "LCOE_U3O8", "LCOE_Conversion", "LCOE_Enrichment", "LCOE_Fabrication",
        "Average Discharged_BU", "Average EFPD",
        "ModifiedPowerDensity", "BaseMWe"
    ]
    
    for comp in components:
        if comp in df_results.columns:
            pivot_comp = df_results.pivot(index="Reactor", columns="MWe", values=comp)
            print(f"\n[ {comp} ]")
            print(pivot_comp)
            pivot_comp.to_csv(os.path.join(output_dir, f"sweep_{comp.lower()}.csv"))
            
    print(f"\nSweep completed. Results saved to CSV files in {output_dir}.")

def run_base_cases():
    """Runs Base Case simulations for each reactor at their design MWe."""
    print("\nStarting Base Case Simulations...")
    
    base_cases = {
        "APR1400": 1400,
        "AP1000": 1027,
        "NuScale": 876, # Assuming this is for 12 modules total (73*12) or as per user's "base" logic 
                        # Wait, base_mwe_map in main_for_loop.py has:
                        # "NuScale": 876
                        # "SNU": 60.45508316034181
                        # "SMART": 109.5
        "SMART": 109.5,
        "SNU": 100
    }
    
    results = []
    
    for reactor, mwe in base_cases.items():
        res = run_single_simulation(reactor, mwe)
        if res:
            results.append(res)
            
    if not results:
        print("No base case results collected.")
        return

    df_base = pd.DataFrame(results)
    
    # Define output directory
    output_dir = "output/lcoe_power"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    output_path = os.path.join(output_dir, "base_case_summary.csv")
    df_base.to_csv(output_path, index=False)
    
    print(f"\nBase Case Simulations completed. Results saved to {output_path}.")


if __name__ == "__main__":
    run_sweep()
    run_base_cases()
