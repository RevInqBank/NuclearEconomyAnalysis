
import pandas as pd
import networkx as nx
import os

def detect_cycle():
    # Construct path to SOURCE_DATA.xlsx
    current_directory = os.getcwd()
    source_file = os.path.join(current_directory, "input", "data", "SOURCE_DATA.xlsx")
    
    print(f"Reading from: {source_file}")
    
    # Read the sheet name corresponding to reactorType from user attempt
    # Based on previous output, reactorType was AP1000. 
    # Let's check AP1000 sheet first, but might need to read input.yaml to be sure.
    # For now, I'll assume AP1000 as seen in the logs.
    sheet_name = 'AP1000' 
    
    try:
        df = pd.read_excel(source_file, sheet_name=sheet_name)
        print(f"Successfully read sheet: {sheet_name}")
    except Exception as e:
        print(f"Error reading sheet {sheet_name}: {e}")
        return

    # Build graph
    G = nx.DiGraph()
    
    # Normalize task names
    task_mapping = {}
    for task in df['NAME']:
        if pd.notna(task):
            normalized_task = str(task).strip().lower()
            if normalized_task not in task_mapping:
                task_mapping[normalized_task] = str(task)
            G.add_node(task_mapping[normalized_task])
            
    # Add edges
    for idx, row in df.iterrows():
        if isinstance(row['PREDECESSOR'], str) and pd.notna(row['NAME']):
            predecessors = row['PREDECESSOR'].split(',')
            for pred in predecessors:
                pred_normalized = pred.strip().lower()
                task_normalized = str(row['NAME']).strip().lower()
                
                if pred_normalized in task_mapping and task_normalized in task_mapping:
                    G.add_edge(task_mapping[pred_normalized], task_mapping[task_normalized])
    
    # Check for cycles
    try:
        cycle = nx.find_cycle(G, orientation='original')
        print("\n!!! CYCLE DETECTED !!!")
        print("The following tasks form a cycle (Circular Dependency):")
        for u, v, direction in cycle:
            print(f"  {u} -> {v}")
    except nx.NetworkXNoCycle:
        print("\nNo cycles detected in the graph.")

if __name__ == "__main__":
    detect_cycle()
