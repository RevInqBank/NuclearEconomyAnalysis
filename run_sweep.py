
import subprocess
import pandas as pd
import sys
import os

def run_sweep():
    reactors = ["APR1400", "AP1000", "NuScale", "SMART", "SNU"]
    mwe_targets = list(range(100, 1100, 100))
    
    results = []

    print("Starting Sweep...")
    
    for reactor in reactors:
        for mwe in mwe_targets:
            print(f"Running {reactor} at {mwe} MWe...")
            try:
                # Run main_for_loop.py with arguments
                # Assuming main_for_loop.py is in the current directory or provide full path
                cmd = [sys.executable, "main_for_loop.py", "--reactor", reactor, "--target_mwe", str(mwe)]
                
                # Capture output
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"Error running {reactor} {mwe}: {result.stderr}")
                    continue
                
                output = result.stdout
                
                # Parse output
                # We expect the block:
                # --------------------------------
                # LCOE_TOTAL
                # LCOE_CON
                # LCOE_OM
                # LCOE_FUEL
                # LCOE_FUEL_IS
                # --------------------------------
                
                lines = output.splitlines()
                # Find the separator line "--------------------------------"
                # There might be multiple. We look for the one before the 5 numbers.
                # Actually, the code prints:
                # --------------------------------
                # val
                # val
                # val
                # val
                # val
                # --------------------------------
                
                # Let's search for this pattern from the end or just scan
                found_block = False
                values = []
                
                # Reverse iterate to find the last block if there are multiple
                for i in range(len(lines) - 1, -1, -1):
                    if "--------------------------------" in lines[i]:
                        # Check if we have enough lines above
                        if i >= 6 and "--------------------------------" in lines[i-6]:
                            # Potential block found
                            block = lines[i-5:i]
                            try:
                                values = [float(x.strip()) for x in block]
                                found_block = True
                                break
                            except ValueError:
                                continue
                
                # Capture Thermal Capacity
                mwth = 0
                for line in lines:
                    if "ThermalCapacityPerModule:" in line:
                        try:
                            mwth = float(line.split(":")[1].strip())
                        except:
                            pass

                if found_block:
                    lcoe_total, lcoe_con, lcoe_om, lcoe_fuel, lcoe_fuel_is = values
                    results.append({
                        "Reactor": reactor,
                        "MWe": mwe,
                        "MWth": mwth,
                        "LCOE_TOTAL": lcoe_total,
                        "LCOE_CON": lcoe_con,
                        "LCOE_OM": lcoe_om,
                        "LCOE_FUEL": lcoe_fuel,
                        "LCOE_FUEL_IS": lcoe_fuel_is
                    })
                else:
                    print(f"Could not parse output for {reactor} {mwe}")

            except Exception as e:
                print(f"Exception for {reactor} {mwe}: {e}")

    # Process results into tables
    if not results:
        print("No results collected.")
        return

    df_results = pd.DataFrame(results)
    
    # 1. Total LCOE Table with MWth rows
    # Expected format:
    # MWe      100 200 ...
    # Reactor
    # APR1400  LCOE...
    # MWth     val ...
    # AP1000   LCOE...
    # MWth     val ...
    
    mwe_cols = sorted(list(set(df_results['MWe'])))
    
    print("\n[ LCOE TOTAL SUMMARY ]")
    # Print Header
    header = ["Reactor / MWe"] + [str(m) for m in mwe_cols]
    print("\t".join(header))
    
    rows_for_csv = [header]

    for reactor in reactors:
        df_r = df_results[df_results['Reactor'] == reactor]
        
        # LCOE Row
        lcoe_vals = []
        mwth_vals = []
        for mwe in mwe_cols:
            row = df_r[df_r['MWe'] == mwe]
            if not row.empty:
                lcoe_vals.append(f"{row.iloc[0]['LCOE_TOTAL']:.2f}")
                mwth_vals.append(f"{row.iloc[0]['MWth']:.2f}")
            else:
                lcoe_vals.append("-")
                mwth_vals.append("-")
        
        lcoe_line = [reactor] + lcoe_vals
        mwth_line = ["MWth"] + mwth_vals
        
        print("\t".join(mwth_line))
        print("\t".join(lcoe_line))
        
        rows_for_csv.append(mwth_line)
        rows_for_csv.append(lcoe_line)

    # Define output directory
    output_dir = "output/lcoe_power"
    os.makedirs(output_dir, exist_ok=True)

    # Save to CSV manually to control structure
    with open(os.path.join(output_dir, "sweep_summary_formatted.csv"), "w") as f:
        for row in rows_for_csv:
            f.write(",".join(row) + "\n")
    
    # 2. Component Tables (Simple Pivot)
    components = ["LCOE_CON", "LCOE_OM", "LCOE_FUEL", "LCOE_FUEL_IS"]
    for comp in components:
        pivot_comp = df_results.pivot(index="Reactor", columns="MWe", values=comp)
        print(f"\n[ {comp} ]")
        print(pivot_comp)
        pivot_comp.to_csv(os.path.join(output_dir, f"sweep_{comp.lower()}.csv"))

    # Save raw results
    df_results.to_csv(os.path.join(output_dir, "sweep_results_raw.csv"), index=False)
    print(f"\nSweep completed. Results saved to CSV files in {output_dir}.")

if __name__ == "__main__":
    run_sweep()
