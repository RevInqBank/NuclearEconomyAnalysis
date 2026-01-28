import time
import functools
import sys
import os

# Add the current directory to sys.path so we can import from main
sys.path.append(os.getcwd())

import main
import input.code.EQcost as EQ
import input.code.Scheduling as SCHEDULING

def time_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"Function '{func.__name__}' took {duration:.4f} seconds")
        return result
    return wrapper

# Monkey-patch main.economic_analysis methods
print("Patching main.economic_analysis methods...")
main.economic_analysis.step_1_read_yaml = time_execution(main.economic_analysis.step_1_read_yaml)
main.economic_analysis.step_2_read_source_excel = time_execution(main.economic_analysis.step_2_read_source_excel)
main.economic_analysis.step_3_calculate_eq_cost = time_execution(main.economic_analysis.step_3_calculate_eq_cost)
main.economic_analysis.step_5_calculate_capex = time_execution(main.economic_analysis.step_5_calculate_capex)
main.economic_analysis.step_6_calculate_cash_flow = time_execution(main.economic_analysis.step_6_calculate_cash_flow)
main.economic_analysis.step_7_analysis = time_execution(main.economic_analysis.step_7_analysis)
main.economic_analysis.run = time_execution(main.economic_analysis.run)

# Monkey-patch internal heavy functions
print("Patching internal heavy functions...")
EQ.convert_currency = time_execution(EQ.convert_currency)
EQ.adjust_dollar_value = time_execution(EQ.adjust_dollar_value)
EQ.scaling = time_execution(EQ.scaling)
SCHEDULING.Rate = time_execution(SCHEDULING.Rate)


if __name__ == "__main__":
    print("Starting profiling...")
    start_total = time.time()
    app = main.economic_analysis()
    app.run()
    end_total = time.time()
    print(f"Total execution time: {end_total - start_total:.4f} seconds")
    print("Profiling finished.")
