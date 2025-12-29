import pandas as pd
import numpy as np
import math

def CAPEX_w0_schedule(CPpivot, CPconst):
    """
    CP별 EQ Cost와 Construction Cost를 결합한 DataFrame 생성
    
    Parameters:
    - CPpivot: CP별 EQ Cost 피벗 테이블
    - CPconst: CP별 Construction Cost 데이터
    
    Returns:
    - 3개 열로 구성된 새로운 DataFrame
    """
    
    # 1단계: 각 DataFrame에서 필요한 열들 추출
    cp_list = CPpivot['CP']
    eq_cost = CPpivot['EQ_Cost_2025USD'] 
    construction_cost = CPconst['scaled_APR1400_CONSTRUCTIONcost_2025USD']
    
    # 2단계: 새로운 DataFrame 생성 (열 이름 동시 설정)
    result_df = pd.DataFrame({
        'CPlist': cp_list,
        'EQ_Cost_2025USD': eq_cost,
        'CONSTRUCTION_Cost_2025USD': construction_cost
    })
    
    return result_df


def addSCHEDULE(CAPEX, df_schedule):
    """
    CAPEX DataFrame에 schedule 정보 추가
    
    Parameters:
    - CAPEX: 기존 CAPEX 데이터프레임
    - df_schedule: START, END 열이 있는 스케줄 데이터프레임
    
    Returns:
    - START, END 열이 추가된 CAPEX 데이터프레임
    """
    
    # 1단계: CAPEX 데이터프레임 복사
    result_df = CAPEX.copy()
    
    # 2단계: df_schedule의 'START' 열을 CAPEX 맨 오른쪽에 추가
    result_df['START'] = df_schedule['START']
    
    # 3단계: df_schedule의 'END' 열을 CAPEX 맨 오른쪽에 추가
    result_df['END'] = df_schedule['END']
    
    return result_df



def CAPEX(df_CAPEX, prep_period, construction_period, operation_period,
          escalationNSSS, escalationTG, escalationBOP, escalationLabor):
    """
    CAPEX 데이터를 Cash Flow 형태로 변환 (ESCALATION 적용)
    
    Parameters:
    - df_CAPEX: CP별 비용과 START, END 정보가 있는 데이터프레임
    - prep_period: 건설 준비 기간
    - construction_period: 건설 기간
    - operation_period: 운영 기간
    - escalationNSSS, escalationTG, escalationBOP, escalationLabor: escalation 비율들
    
    Returns:
    - df_afterESCALATION: escalation이 적용된 총 비용 Cash Flow
    """
    
    # 1단계: CF.YEARS와 동일한 방식으로 연도 생성
    start_year = -math.ceil(prep_period)
    end_year = math.ceil(construction_period + operation_period)
    years = list(range(start_year, end_year + 1))
    
    # 2단계: EQ Cost와 Construction Cost 분리해서 처리할 DataFrame 생성
    cp_list = df_CAPEX['CPlist'].tolist()
    df_EQ = pd.DataFrame(0.0, index=cp_list, columns=years)
    df_CONSTRUCTION = pd.DataFrame(0.0, index=cp_list, columns=years)
    
    # 3단계: 각 CP별로 비용 분배 (EQ Cost와 Construction Cost 따로)
    for idx, row in df_CAPEX.iterrows():
        cp = row['CPlist']
        start_time = row['START']
        end_time = row['END']
        eq_cost = row['EQ_Cost_2025USD']
        construction_cost = row['CONSTRUCTION_Cost_2025USD']
        
        total_duration = end_time - start_time
        if total_duration <= 0:
            continue
            
        # 시작/종료 연도의 정수 부분과 소수 부분 계산
        start_year_int = math.ceil(start_time)
        start_fraction = start_year_int - start_time
        end_year_int = math.floor(end_time)
        end_fraction = end_time - end_year_int
        
        # 첫 번째 연도 (부분 기간)
        if start_year_int in years:
            df_EQ.loc[cp, start_year_int] = eq_cost * start_fraction / total_duration
            df_CONSTRUCTION.loc[cp, start_year_int] = construction_cost * start_fraction / total_duration
        
        # 중간 연도들 (완전 기간)
        for year in range(start_year_int + 1, end_year_int + 1):
            if year in years:
                df_EQ.loc[cp, year] = eq_cost * 1.0 / total_duration
                df_CONSTRUCTION.loc[cp, year] = construction_cost * 1.0 / total_duration
        
        # 마지막 연도 (부분 기간)
        if end_fraction > 0 and (end_year_int + 1) in years:
            df_EQ.loc[cp, end_year_int + 1] = eq_cost * end_fraction / total_duration
            df_CONSTRUCTION.loc[cp, end_year_int + 1] = construction_cost * end_fraction / total_duration
    
    # 4단계: EQ Cost에 CP별 ESCALATION 적용
    df_EQ_escalated = df_EQ.copy()
    
    for cp in cp_list:
        for year in years:
            year_index = year  # year 자체를 인덱스로 사용 (음수면 할인, 양수면 할증)
            
            if cp == 'CP-M3':
                df_EQ_escalated.loc[cp, year] *= (1 + escalationTG) ** year_index
            elif cp == 'CP-M5':
                df_EQ_escalated.loc[cp, year] *= (1 + escalationNSSS) ** year_index
            else:  # 나머지 CP들
                df_EQ_escalated.loc[cp, year] *= (1 + escalationBOP) ** year_index
    
    # 5단계: CONSTRUCTION Cost에 ESCALATION 적용 (모든 CP에 동일)
    df_CONSTRUCTION_escalated = df_CONSTRUCTION.copy()
    
    # 모든 Construction Cost에 escalationLabor 적용
    for year in years:
        year_index = year  # year 자체를 인덱스로 사용
        df_CONSTRUCTION_escalated[year] *= (1 + escalationLabor) ** year_index
    
    # 6단계: EQ Cost (escalated) + Construction Cost (escalated) 합계
    df_afterESCALATION = df_EQ_escalated + df_CONSTRUCTION_escalated
    
    return df_afterESCALATION
