

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

def visualize_task_network(df):
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes (tasks)
    for task in df['NAME']:
        G.add_node(task)
    
    # Add edges (dependencies)
    for idx, row in df.iterrows():
        if isinstance(row['PREDECESSOR'], str):
            predecessors = row['PREDECESSOR'].split(',')
            for pred in predecessors:
                pred = pred.strip()
                G.add_edge(pred, row['NAME'])
    
    # Create plot
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=2000, arrowsize=20, font_size=10,
            font_weight='bold')
    
    plt.title("Task Dependencies Network")
    plt.show()

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# 현재 작업 디렉토리 구하기
current_directory = os.getcwd()

#source_file = current_directory / "input" / "data" / "SOURCE_DATA.xlsx"
source_file =  os.path.join(current_directory, "input", "data", "SOURCE_DATA.xlsx")

df_scheduling = pd.read_excel(source_file, sheet_name='APR1400') # EQ Cost 원본 데이터
#visualize_task_network(df_scheduling)
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""





def visualize_task_network_improved(df):
    G = nx.DiGraph()
    
    # Normalize task names and add nodes
    task_mapping = {}
    for task in df['NAME']:
        normalized_task = str(task).strip().lower()
        if normalized_task not in task_mapping:
            task_mapping[normalized_task] = str(task)
        G.add_node(task_mapping[normalized_task])
    
    # Add edges with normalized names
    for idx, row in df.iterrows():
        if isinstance(row['PREDECESSOR'], str):
            predecessors = row['PREDECESSOR'].split(',')
            for pred in predecessors:
                pred_normalized = pred.strip().lower()
                if pred_normalized in task_mapping:
                    G.add_edge(task_mapping[pred_normalized], task_mapping[row['NAME'].strip().lower()])

    # Assign hierarchical levels to nodes
    levels = {}
    for node in G.nodes():
        levels[node] = len(nx.ancestors(G, node))
        nx.set_node_attributes(G, {node: levels[node]}, 'subset')
    
    plt.figure(figsize=(15, 10))
    
    # Use hierarchical layout
    pos = nx.kamada_kawai_layout(G)
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, 
                          node_color='lightblue',
                          node_size=2500,
                          alpha=0.7)
    
    # Draw edges with curved arrows
    nx.draw_networkx_edges(G, pos,
                          edge_color='gray',
                          arrows=True,
                          arrowsize=20,
                          connectionstyle='arc3,rad=0.2')
    
    # Draw labels with white background for better readability
    labels = nx.draw_networkx_labels(G, pos,
                                   font_size=8,
                                   font_weight='bold')
    
    # Add white backgrounds to labels
    for label in labels.values():
        label.set_bbox(dict(facecolor='white', edgecolor='none', alpha=0.7))
    
    #plt.title("Task Dependencies Network")
    #plt.axis('off')
    #plt.tight_layout()
    #plt.show()


# Test the improved visualization
visualize_task_network_improved(df_scheduling)



def Rate(df, Rate_BASEMAT, Rate_INCV, Rate_CNT):
    """
    Calculate DURATION for each task based on Concrete Volume and Rate
    Then perform CPM analysis to find the critical path (최장 경로)

    Parameters:
    df: DataFrame - SOURCE_DATA 엑셀 파일
    Rate_BASEMAT: float - BASEMAT 작업용 Rate
    Rate_INCV: float - IN-CV 작업용 Rate
    Rate_CNT: float - CNT 작업용 Rate

    Returns:
    df: DataFrame - DURATION 열이 업데이트된 DataFrame
    critical_path_duration: float - 최장 경로의 총 기간 (CPM)
    """

    # Make a copy to avoid modifying original
    df = df.copy()

    # Calculate DURATION based on Sub-Class
    for idx, row in df.iterrows():
        sub_class = row['Sub-Class']
        concrete_volume = row['Concrete Volume (CY)']

        # Skip if no concrete volume or sub-class
        if pd.isna(concrete_volume) or pd.isna(sub_class):
            continue

        # Convert concrete_volume to float if it's a string
        try:
            concrete_volume = float(concrete_volume)
        except (ValueError, TypeError):
            continue  # Skip if conversion fails

        # Determine which rate to use based on Sub-Class
        # Calculate duration in years (divide by 12 to convert months to years)
        if 'BASEMAT' in str(sub_class).upper():
            duration = (concrete_volume / Rate_BASEMAT) / 12
        elif 'IN-CV' in str(sub_class).upper():
            duration = (concrete_volume / Rate_INCV) / 12
        elif 'CNT' in str(sub_class).upper():
            duration = (concrete_volume / Rate_CNT) / 12
        else:
            continue  # Skip other types

        # Update DURATION column (now in years)
        df.at[idx, 'DURATION'] = duration

    # Build directed graph using same logic as visualize_task_network_improved
    G = nx.DiGraph()

    # Normalize task names and add nodes with duration
    task_mapping = {}
    task_durations = {}  # Store durations for each normalized task

    for idx, row in df.iterrows():
        task = row['NAME']
        if pd.notna(task):
            normalized_task = str(task).strip().lower()
            if normalized_task not in task_mapping:
                task_mapping[normalized_task] = str(task)

                # Store duration for this task
                duration = row['DURATION']
                if pd.notna(duration):
                    task_durations[normalized_task] = duration
                    G.add_node(task_mapping[normalized_task], duration=duration)

    # Add edges with normalized names
    for idx, row in df.iterrows():
        if isinstance(row['PREDECESSOR'], str) and pd.notna(row['NAME']):
            predecessors = row['PREDECESSOR'].split(',')
            for pred in predecessors:
                pred_normalized = pred.strip().lower()
                task_normalized = str(row['NAME']).strip().lower()

                # Only add edge if both nodes exist in graph (have durations)
                if (pred_normalized in task_mapping and
                    task_normalized in task_mapping and
                    pred_normalized in task_durations and
                    task_normalized in task_durations):
                    G.add_edge(task_mapping[pred_normalized], task_mapping[task_normalized])

    # Calculate earliest finish times using topological sort (CPM forward pass)
    earliest_start = {}
    earliest_finish = {}

    try:
        # Topological sort ensures we process nodes in dependency order
        for node in nx.topological_sort(G):
            # Find maximum earliest finish time of all predecessors
            pred_finish_times = [earliest_finish.get(pred, 0) for pred in G.predecessors(node)]

            if pred_finish_times:
                earliest_start[node] = max(pred_finish_times)
            else:
                earliest_start[node] = 0  # Start node

            # Calculate earliest finish time
            node_duration = G.nodes[node]['duration']
            earliest_finish[node] = earliest_start[node] + node_duration

        # Critical path duration is the maximum earliest finish time
        if earliest_finish:
            critical_path_duration = max(earliest_finish.values())
        else:
            critical_path_duration = 0

    except nx.NetworkXError as e:
        print(f"Error in topological sort: {e}")
        print("Graph may contain cycles or other issues")
        critical_path_duration = 0


    # Create DataFrame with start time, finish time, and duration for each task (in years)
    schedule_data = []
    for node in G.nodes():
        schedule_data.append({
            'Task': node,
            'Start Time (Year)': earliest_start.get(node, 0),
            'Finish Time (Year)': earliest_finish.get(node, 0),
            'Duration (Year)': G.nodes[node].get('duration', 0)
        })

    df_schedule = pd.DataFrame(schedule_data)
    df_schedule = df_schedule.sort_values('Start Time (Year)').reset_index(drop=True)



    # Print the schedule DataFrame
    #print("\n=== Task Schedule (in Years) ===")
    #print(df_schedule.to_string(index=False))
    #print(f"\nCritical Path Duration: {critical_path_duration:.4f} years")


    return df, critical_path_duration







"""""

def process_excel_cpm(file_path):
    # Read Excel
    df = pd.read_excel(file_path)
    
    # Create graph
    G = nx.DiGraph()
    
    # Add activities and their durations
    for _, row in df.iterrows():
        activity = row.iloc[0]
        duration = row.iloc[1]
        G.add_node(activity, weight=duration)
    
    # Add dependencies
    for _, row in df.iterrows():
        activity = row.iloc[0]
        if isinstance(row.iloc[2], str):
            deps = row.iloc[2].split(',')
            for dep in deps:
                dep = dep.strip()
                G.add_edge(dep, activity)
    
    # Calculate start and finish dates using topological sort
    start_dates = {}
    finish_dates = {}
    
    for node in nx.topological_sort(G):
        pred_finish = 0
        for pred in G.predecessors(node):
            pred_finish = max(pred_finish, finish_dates.get(pred, 0))
        
        start_dates[node] = pred_finish
        finish_dates[node] = pred_finish + G.nodes[node]['weight']
    
    # Add results to dataframe
    df['Start Date'] = df.iloc[:, 0].map(start_dates)
    df['Finish Date'] = df.iloc[:, 0].map(finish_dates)
    
    # Write results to Excel
    df.to_excel(file_path.replace('.xlsx', '_results.xlsx'), index=False)
    
    project_duration = max(finish_dates.values())
    print(f"전체 공기: {project_duration}일")
    
    return df, project_duration

if __name__ == "__main__":
    results, duration = process_excel_cpm('project_schedule.xlsx')
    print(results)

"""""