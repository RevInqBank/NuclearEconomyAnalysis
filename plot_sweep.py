
import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import subprocess

def plot_sweep():
    output_dir = "output/lcoe_power"
    raw_csv = os.path.join(output_dir, "sweep_results_raw.csv")
    
    if not os.path.exists(raw_csv):
        print(f"Error: {raw_csv} not found. Please run run_sweep.py first.")
        return

    print(f"Loading data from {raw_csv}...")
    df_results = pd.read_csv(raw_csv)
    
    # --- Reference Calculation ---
    reference_data = {
        # "APR1400": 1400, # User requested to remove APR1400 reference
        "AP1000": 1027,
        "NuScale": 876, 
        "SMART": 109.5,
        "SNU": 100
    }
    
    ref_results = {}
    print("\nCalculating Reference LCOE...")
    
    for reactor, ref_mwe in reference_data.items():
        print(f"Running Reference {reactor} at {ref_mwe} MWe...")
        try:
            # Assuming main_for_loop.py is in the current directory
            cmd = [sys.executable, "main_for_loop.py", "--reactor", reactor, "--target_mwe", str(ref_mwe)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error running Ref {reactor}: {result.stderr}")
                continue
                
            output = result.stdout
            lines = output.splitlines()
            
             # Find LCOE block
            found_block = False
            lcoe_total = 0
            
            # Capture Thermal Capacity
            mwth = 0
            for line in lines:
                if "ThermalCapacityPerModule:" in line:
                    try:
                        mwth = float(line.split(":")[1].strip())
                    except:
                        pass
                        
            for i in range(len(lines) - 1, -1, -1):
                if "--------------------------------" in lines[i]:
                    if i >= 6 and "--------------------------------" in lines[i-6]:
                        block = lines[i-5:i]
                        try:
                            values = [float(x.strip()) for x in block]
                            lcoe_total = values[0] # LCOE_TOTAL is first
                            found_block = True
                            break
                        except ValueError:
                            continue
            
            if found_block:
                ref_results[reactor] = {"lcoe": lcoe_total, "mwth": mwth}
                print(f"Reference {reactor} ({ref_mwe} MWe): {lcoe_total:.2f}, {mwth:.2f} MWth")
            else:
                print(f"Could not parse output for Ref {reactor}")
                
        except Exception as e:
            print(f"Ref Exception {reactor}: {e}")


    # --- Plotting Wrapper Function ---
    def generate_single_plot(show_breakdown, filename):
        import numpy as np
        from matplotlib.ticker import MultipleLocator, AutoMinorLocator
        
        print(f"\nGenerating Plot: {filename} (Breakdown={show_breakdown})...")
        
        # Font settings
        plt.rcParams['font.family'] = 'serif'
        plt.rcParams['font.weight'] = 'bold'
        plt.rcParams['axes.labelweight'] = 'bold'
        plt.rcParams['axes.titleweight'] = 'bold'
        
        plt.figure(figsize=(12, 8))
        
        colors = {
            "APR1400": "tab:blue",
            "AP1000": "tab:orange",
            "NuScale": "tab:green", 
            "SMART": "tab:pink",
            "SNU": "tab:purple"
        }

        reactors = df_results['Reactor'].unique()
        
        # Plot curves
        for reactor in reactors:
            df_r = df_results[df_results['Reactor'] == reactor]
            if df_r.empty: continue
            
            df_r = df_r.sort_values(by="MWth")
            x_data = df_r['MWth']
            if reactor == "NuScale":
                 x_data = x_data * 12
            
            color = colors.get(reactor, 'black')
            plt.plot(x_data, df_r['LCOE_TOTAL'], label=reactor, color=color, linewidth=2)
            
            # Curve Labels for "No Breakdown" (Left side)
            if not show_breakdown and not df_r.empty:
                lbl_x = x_data.iloc[0]
                lbl_y = df_r['LCOE_TOTAL'].iloc[0]
                
                # Move to the left of the curve start
                # Use ha='right' and subtract from x
                x_offset = -30
                
                if reactor == "NuScale":
                     plt.text(lbl_x + x_offset, lbl_y, reactor, color=color, fontsize=12, fontweight='bold', va='center', ha='right')
                elif reactor == "APR1400":
                     plt.text(lbl_x + x_offset, lbl_y + 10, reactor, color=color, fontsize=12, fontweight='bold', va='bottom', ha='right')
                elif reactor == "AP1000":
                     plt.text(lbl_x + x_offset, lbl_y + 10, reactor, color=color, fontsize=12, fontweight='bold', va='bottom', ha='right')
                elif reactor == "SMART":
                     plt.text(lbl_x + x_offset, lbl_y + 25, reactor, color=color, fontsize=12, fontweight='bold', va='bottom', ha='right')
                elif reactor == "SNU":
                     plt.text(lbl_x + x_offset, lbl_y - 25, reactor, color=color, fontsize=12, fontweight='bold', va='top', ha='right')
                else:
                     plt.text(lbl_x + x_offset, lbl_y, reactor, color=color, fontsize=12, fontweight='bold', va='center', ha='right')
        
        # Visualizing Components (Conditional)
        if show_breakdown:
            comp_configs = [
                {"Reactor": "NuScale", "x_pos": 100, "width": 100}, 
                {"Reactor": "AP1000", "x_pos": 250, "width": 100},
                {"Reactor": "SNU", "x_pos": 550, "width": 100}
            ]
            
            for config in comp_configs:
                reactor = config["Reactor"]
                df_r = df_results[df_results['Reactor'] == reactor]
                if df_r.empty: continue
                
                df_r = df_r.sort_values(by="MWth")
                row = df_r.iloc[0]
                
                val_con = row['LCOE_CON']
                val_om = row['LCOE_OM']
                val_fuel = row['LCOE_FUEL'] + row['LCOE_FUEL_IS']
                total = row['LCOE_TOTAL']
                
                h1 = val_con
                h2 = val_con + val_om
                h3 = total 
                
                c = colors.get(reactor, 'black')
                x = config["x_pos"]
                w = config["width"]
                
                # Draw Bars
                plt.fill_betweenx([0, h1], x - w/2, x + w/2, color=c, alpha=0.3, edgecolor=None)
                plt.fill_betweenx([h1, h2], x - w/2, x + w/2, color=c, alpha=0.6, edgecolor=None)
                plt.fill_betweenx([h2, h3], x - w/2, x + w/2, color=c, alpha=0.9, edgecolor=None)
                
                # Labels inside bars (smaller font)
                mid_cap_loc = h1 / 2
                mid_om_loc = (h1 + h2) / 2
                mid_fuel_loc = (h2 + h3) / 2
                
                lbl_list = [
                    ("Capital", mid_cap_loc),
                    ("O&M", mid_om_loc),
                    ("Fuel", mid_fuel_loc)
                ]
                
                for label_text, y_pos in lbl_list:
                     plt.text(x, y_pos, label_text, ha='center', va='center', fontsize=8, fontweight='bold', color='black') # Reduced fontsize
                
                # Reactor Label
                plt.text(x, h3 + 5, f"{reactor}\n(100 MWe)", ha='center', va='bottom', fontsize=9, fontweight='bold', color=c)

            # Legend for "With Breakdown" - Upper Right
            plt.legend(loc='upper right', fontsize=12)

        # else: NO LEGEND for No Breakdown (handled by text above)

        # Set Y Limit
        plt.ylim(0, 420)

        # Reference Lines
        for reactor, data in ref_results.items():
            if reactor in colors:
                color = colors[reactor]
            else:
                color = 'black'
            
            lcoe_val = data["lcoe"]
            mwth_val = data["mwth"]
            
            if reactor == "NuScale":
                mwth_val = mwth_val * 12
            
            # Use user-specified value for SNU display
            if reactor == "SNU":
                mwth_val = 330.8
                
            plt.axhline(y=lcoe_val, color=color, linestyle='--', alpha=0.4, linewidth=1.5)
            
            # Adjust offsets to prevent overlap
            text_y_offset = 10
            if reactor == "AP1000": text_y_offset = -20
            if reactor == "NuScale": text_y_offset = -10
            # Separate SMART and SNU more
            if reactor == "SMART": text_y_offset = 5 # Lower slightly towards line
            if reactor == "SNU": text_y_offset = 35  # Raise higher
            
            label_str = f"{reactor}, {mwth_val:.0f} MWth ({lcoe_val:.1f})"
            if reactor == "SNU": 
                 label_str = f"{reactor}, {mwth_val:.1f} MWth ({lcoe_val:.1f})"
            
            plt.annotate(
                label_str, 
                xy=(1800, lcoe_val),  
                xytext=(1600, lcoe_val + text_y_offset), 
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
                fontsize=12,
                fontweight='bold',
                ha='center'
                # backgroundcolor removed
            )

        plt.xlabel("Total Power (MWth)", fontsize=14, fontweight='bold')
        plt.ylabel("LCOE ($/MWh)", fontsize=14, fontweight='bold')
        plt.xlim(0, 2000)
        
        ax = plt.gca()
        ax.xaxis.set_major_locator(MultipleLocator(500))
        ax.xaxis.set_minor_locator(MultipleLocator(100))
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(which='major', length=7, width=2, labelsize=12)
        ax.tick_params(which='minor', length=4, width=1.5)
        
        plt.grid(True, axis='x', which='both', linestyle='--', color='gray', alpha=0.5)
        plt.grid(True, axis='y', which='major', linestyle='--', color='gray', alpha=0.5)
        
        plot_path = os.path.join(output_dir, filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {plot_path}")

    # Generate both plots
    generate_single_plot(show_breakdown=True, filename="lcoe_vs_mwth_breakdown.png")
    generate_single_plot(show_breakdown=False, filename="lcoe_vs_mwth_no_breakdown.png")

if __name__ == "__main__":
    plot_sweep()
