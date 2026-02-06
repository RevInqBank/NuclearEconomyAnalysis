
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
    
    # Map ThermalCapacityPerModule to MWth if MWth doesn't exist
    if "ThermalCapacityPerModule" in df_results.columns and "MWth" not in df_results.columns:
        df_results["MWth"] = df_results["ThermalCapacityPerModule"]
    
    # --- Reference Loading ---
    base_csv = os.path.join(output_dir, "base_case_summary.csv")
    ref_results = {}
    
    if os.path.exists(base_csv):
        print(f"Loading reference data from {base_csv}...")
        df_base = pd.read_csv(base_csv)
        
        # Map ThermalCapacityPerModule to MWth in base data too
        if "ThermalCapacityPerModule" in df_base.columns and "MWth" not in df_base.columns:
            df_base["MWth"] = df_base["ThermalCapacityPerModule"]
            
        for _, row in df_base.iterrows():
            reactor = row['Reactor']
            lcoe_total = row['LCOE_TOTAL']
            mwth = row['MWth']
            ref_results[reactor] = {"lcoe": lcoe_total, "mwth": mwth}
            print(f"Reference {reactor}: {lcoe_total:.2f} ($/MWh), {mwth:.2f} MWth")
    else:
        print(f"Warning: {base_csv} not found. Reference lines will be skipped.")

    colors = {
        "APR1400": "tab:blue",
        "AP1000": "tab:orange",
        "NuScale": "tab:green", 
        "SMART": "tab:pink",
        "SNU": "tab:purple"
    }

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
        
        # Colors defined in parent scope
        
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

    # --- Additional Plotting Functions ---
    def generate_burnup_plot():
        print(f"\nGenerating Plot: burnup_vs_mwth.png...")
        plt.figure(figsize=(12, 8))
        
        reactors = df_results['Reactor'].unique()
        
        # Track max MWth for x-axis limit
        max_mwth = 2000 
        
        for reactor in reactors:
            df_r = df_results[df_results['Reactor'] == reactor]
            if df_r.empty: continue
            
            df_r = df_r.sort_values(by="MWth")
            x_data = df_r['MWth']
            if reactor == "NuScale": x_data = x_data * 12
            
            local_max = x_data.max()
            if local_max > max_mwth: max_mwth = local_max
            
            color = colors.get(reactor, 'black')
            plt.plot(x_data, df_r['Average Discharged_BU'], label=reactor, color=color, linewidth=2, marker='o')

        # Reference Points for Burnup
        for reactor, data in ref_results.items():
            if 'df_base' in locals() and not df_base[df_base['Reactor'] == reactor].empty:
                row = df_base[df_base['Reactor'] == reactor].iloc[0]
                bu_val = row['Average Discharged_BU']
                mwth_val = row['MWth']
                
                # Correct MWth for NuScale display
                plot_mwth = mwth_val
                if reactor == "NuScale": plot_mwth = mwth_val * 12
                # Use user-specified display value for SNU
                if reactor == "SNU": plot_mwth = 330.8
                
                if plot_mwth > max_mwth: max_mwth = plot_mwth
                
                color = colors.get(reactor, 'black')
                plt.scatter(plot_mwth, bu_val, color=color, s=150, marker='*', zorder=10)
                
                # Smart Label Placement to avoid overlap
                # Default offset
                xytext = (5, 5)
                ha = 'left'
                va = 'bottom'
                
                if reactor == "AP1000":
                    xytext = (0, -10)
                    ha = 'right'
                    va = 'top'
                elif reactor == "APR1400":
                    xytext = (0, 10)
                    ha = 'right'
                    va = 'bottom'
                elif reactor == "NuScale":
                    xytext = (5, 15)
                    ha = 'left'
                    va = 'top'
                elif reactor == "SMART":
                    # SMART and SNU are close, adjust SMART
                    xytext = (0, 20) 
                    ha = 'left'
                    va = 'bottom'
                elif reactor == "SNU":
                    xytext = (5, -5)
                    ha = 'left'
                    va = 'top'

                plt.annotate(f"{bu_val:.1f}", (plot_mwth, bu_val), xytext=xytext, textcoords='offset points', 
                             fontsize=11, fontweight='bold', color=color, ha=ha, va=va)

        plt.xlabel("Total Power (MWth)", fontsize=14, fontweight='bold')
        plt.ylabel("Average Discharged Burnup (MWd/kgU)", fontsize=14, fontweight='bold')
        plt.title("Discharged Burnup vs Thermal Power", fontsize=16, fontweight='bold')
        
        # Set x-limit dynamically with some buffer
        plt.xlim(0, max_mwth * 1.1)
        
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend(fontsize=12, loc='upper left')
        
        plot_path = os.path.join(output_dir, "burnup_vs_mwth.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {plot_path}")

    def generate_fuel_cost_plot():
        print(f"\nGenerating Plot: fuel_cost_vs_mwth.png...")
        plt.figure(figsize=(12, 8))
        
        reactors = df_results['Reactor'].unique()
        for reactor in reactors:
            df_r = df_results[df_results['Reactor'] == reactor]
            if df_r.empty: continue
            
            df_r = df_r.sort_values(by="MWth")
            x_data = df_r['MWth']
            if reactor == "NuScale": x_data = x_data * 12
            
            # Total Fuel Cost = Front-end + Back-end (Interim)
            y_data = df_r['LCOE_FUEL'] + df_r['LCOE_FUEL_IS']
            
            color = colors.get(reactor, 'black')
            plt.plot(x_data, y_data, label=reactor, color=color, linewidth=2, marker='s')

        plt.xlabel("Total Power (MWth)", fontsize=14, fontweight='bold')
        plt.ylabel("Total Fuel Cost ($/MWh)", fontsize=14, fontweight='bold')
        plt.title("Fuel Cost vs Thermal Power", fontsize=16, fontweight='bold')
        plt.xlim(0, 2000)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend(fontsize=12)
        
        plot_path = os.path.join(output_dir, "fuel_cost_vs_mwth.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {plot_path}")

    def generate_fuel_breakdown_plot():
        print(f"\nGenerating Fuel Breakdown Plots per Reactor...")
        
        fuel_components = [
            "LCOE_U3O8",
            "LCOE_Conversion",
            "LCOE_Enrichment",
            "LCOE_Fabrication",
            "LCOE_FUEL_IS"
        ]
        
        comp_colors = [
            '#e41a1c', # U3O8 (Red)
            '#377eb8', # Conversion (Blue)
            '#4daf4a', # Enrichment (Green)
            '#984ea3', # Fabrication (Purple)
            '#ff7f00'  # Interim Storage (Orange)
        ]
        
        comp_labels = [
            "U3O8", "Conversion", "Enrichment", "Fabrication", "Interim Storage"
        ]

        reactors = df_results['Reactor'].unique()
        for reactor in reactors:
            df_r = df_results[df_results['Reactor'] == reactor]
            if df_r.empty: continue
            
            df_r = df_r.sort_values(by="MWth")
            x_data = df_r['MWth']
            if reactor == "NuScale": x_data = x_data * 12
            
            plt.figure(figsize=(10, 6))
            
            # Prepare Stack Data
            y_stack = []
            for comp in fuel_components:
                # Check if component exists, else 0
                if comp in df_r.columns:
                    y_stack.append(df_r[comp].values)
                else:
                    y_stack.append(np.zeros(len(df_r)))
            
            plt.stackplot(x_data, y_stack, labels=comp_labels, colors=comp_colors, alpha=0.8)
            
            plt.xlabel("Total Power (MWth)", fontsize=12, fontweight='bold')
            plt.ylabel("Fuel Cost ($/MWh)", fontsize=12, fontweight='bold')
            plt.title(f"Fuel Cost Breakdown: {reactor}", fontsize=14, fontweight='bold')
            
            if reactor == "NuScale":
                 plt.xlim(0, 4000) # NuScale range
            else:
                 plt.xlim(0, max(x_data) * 1.1)
                 
            plt.grid(True, linestyle='--', alpha=0.3)
            plt.legend(loc='upper right')
            
            filename = f"fuel_breakdown_{reactor}.png"
            plot_path = os.path.join(output_dir, filename)
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"  Saved {filename}")

    # Generate both plots
    generate_single_plot(show_breakdown=True, filename="lcoe_vs_mwth_breakdown.png")
    generate_single_plot(show_breakdown=False, filename="lcoe_vs_mwth_no_breakdown.png")
    
    # Generate new plots
    generate_burnup_plot()
    generate_fuel_cost_plot()
    generate_fuel_breakdown_plot()

if __name__ == "__main__":
    plot_sweep()
