# input_reader.py
import pandas as pd
import inspect
import numpy as np


def Input(excel_file):
    """
    Excel 파일에서 변수를 읽어와 호출한 모듈의 전역변수로 생성
    """
    df = pd.read_excel(excel_file, header=None)
    
    # 호출한 모듈의 globals() 찾기
    caller_globals = inspect.currentframe().f_back.f_globals
    
    for i in range(len(df)):
        var_name = df.iloc[i, 1]    # 2열: 변수 이름
        var_value = df.iloc[i, 2]   # 3열: 변수 값
        
        # 호출한 모듈의 전역변수로 생성
        caller_globals[var_name] = var_value
        #print(f"{var_name} = {var_value}")
    
    #print(f"총 {len(df)}개 변수가 생성되었습니다.")
    # return 없음 - None 반환
