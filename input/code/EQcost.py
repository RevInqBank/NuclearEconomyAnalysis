
""""
1. 엑셀 읽어서 Dataframe 생성하기
2. Scaling Factors 적용하기 
3. 예외사항 검증하기 
"""

# input_reader.py
import pandas as pd
import inspect
import numpy as np


# 환율 적용 ############################################################################################################
def convert_currency(df_EQcost_original, df_currency):
    """
    procurement_SK34 열의 원화 비용을 달러로 변환
    
    Parameters:
    - df_EQcost_original: 원본 데이터 (contractDate_SK34, procurement_SK34 포함)
    - df_currency: 환율 데이터 (DATE, CURRENCY 포함)
    
    Returns:
    - procurement_SK34_USD 열이 추가된 데이터프레임
    """
    
    result_df = df_EQcost_original.copy()
    
    # 원본 데이터 열 확인
    #print("원본 데이터 열:", result_df.columns.tolist())
    
    # procurement 열 데이터 타입과 샘플 확인
    
    '''''
    if 'procurement_SK34' in result_df.columns:
        print(f"procurement_SK34 데이터 타입: {result_df['procurement_SK34'].dtype}")
        print(f"procurement_SK34 샘플 값: {result_df['procurement_SK34'].head()}")
        print(f"NaN 개수: {result_df['procurement_SK34'].isna().sum()}")
    '''''

    # 환율 딕셔너리 생성
    currency_dict = dict(zip(df_currency['DATE'], df_currency['CURRENCY']))
    
    # 처리할 열 목록
    columns_to_convert = [
        ('procurement_SK34', 'contractDate_SK34', 'procurement_SK34_USD'),
        ('procurement_SH12', 'contractDate_SH12', 'procurement_SH12_USD'),
        ('procurement_SK56', 'contractDate_SK56', 'procurement_SK56_USD'),
        ('procurement_SH34', 'contractDate_SH34', 'procurement_SH34_USD')
    ]
    
    for procurement_col, contract_col, usd_col in columns_to_convert:
        if procurement_col in result_df.columns and contract_col in result_df.columns:
            def convert_row(row):
                try:
                    procurement_val = float(row[procurement_col])
                    exchange_rate = currency_dict.get(row[contract_col], 1)
                    return (procurement_val / exchange_rate) / 1000000
                except (ValueError, TypeError):
                    return 0  # 숫자가 아닌 경우 0으로 처리
            
            result_df[usd_col] = result_df.apply(convert_row, axis=1)
            #print(f"{usd_col} 열 추가 완료")
        else:
            None
            #print(f"{procurement_col} 또는 {contract_col} 열이 존재하지 않음")


    #print(f"변환 완료: {len(result_df)}개 행")
    #print("새로 추가된 열: procurement_SK34_USD")
    
    return result_df



# 달러가치 적용 ############################################################################################################
def adjust_dollar_value(df_original, df_dollarValue):
    """
    연도 기준으로 달러 가치 인덱스를 적용하여 실질 달러로 변환
    
    Parameters:
    - df_original: 원본 데이터 (USD 열들과 연도 정보 포함)
    - df_dollarValue: 달러 가치 데이터 (연도, 인덱스 포함)
    
    Returns:
    - 실질 달러 열들이 추가된 데이터프레임
    """
    
    result_df = df_original.copy()
    
    # 달러 가치 딕셔너리 생성 (연도 -> 변환계수)
    #print("달러 가치 데이터 열:", df_dollarValue.columns.tolist())
    
    # YEAR와 2025USD 열 사용
    dollar_value_dict = dict(zip(df_dollarValue['YEAR'], df_dollarValue['2025USD']))
    
    # USD 열들을 찾아서 실질 달러로 변환
    usd_columns = [col for col in result_df.columns if col.endswith('_USD')]
    #print(f"처리할 USD 열: {usd_columns}")
    
    for usd_col in usd_columns:
        # 계약 날짜 열 이름 생성
        contract_date_col = usd_col.replace('procurement_', 'contractDate_').replace('_USD', '')
        
        if contract_date_col in result_df.columns:
            def convert_to_real_dollar(row):
                try:
                    # 계약일에서 연도 추출
                    if hasattr(row[contract_date_col], 'year'):
                        contract_year = row[contract_date_col].year
                    else:
                        contract_year = int(row[contract_date_col])
                    
                    # 해당 연도의 달러 가치 인덱스 적용
                    dollar_index = dollar_value_dict.get(contract_year, 1.0)
                    
                    return row[usd_col] / dollar_index
                except:
                    return row[usd_col]
            
            real_dollar_col = usd_col + '_2025'
            result_df[real_dollar_col] = result_df.apply(convert_to_real_dollar, axis=1)
            #print(f"{real_dollar_col} 열 추가 완료")
        else:
            None
            #print(f"{contract_date_col} 열이 존재하지 않음")
    
    return result_df



# EQ List 별 Min/Max/AVG 구하기 ###########################################################################################
def mergeEQcost(df_EQcost_original):
    # 4개 열 선택
    cost_columns = ['procurement_SK34_USD_2025', 'procurement_SK56_USD_2025', 
                    'procurement_SH12_USD_2025', 'procurement_SH34_USD_2025']
    # 각 행별 min, mean, max 계산하여 새로운 열 추가
    df_EQcost_original['APR1400_EQcost_2025USD_min'] = df_EQcost_original[cost_columns].min(axis=1)
    df_EQcost_original['APR1400_EQcost_2025USD_Mean'] = df_EQcost_original[cost_columns].mean(axis=1)
    df_EQcost_original['APR1400_EQcost_2025USD_MAX'] = df_EQcost_original[cost_columns].max(axis=1)

    return df_EQcost_original



# EQ Cost Scaling 작업
def scaling(Country, df_EQcost_original, df_scaling_power, df_country_specific, ElectricCapacityPerModule, ModuleNumber, 
                 DesignSimplification_safetyPIPING, DesignSimplification_safetyVALVES, 
                 DesignSimplification_safetyPUMPS, DesignSimplification_safetyCABLES, 
                 DesignSimplification_safetyMECH):
    """
    EQ Cost 스케일링 함수
    """
    
    result_df = df_EQcost_original.copy()
    
    # Power scaling exponent 딕셔너리 생성
    power_scaling_dict = dict(zip(df_scaling_power.iloc[:, 0], df_scaling_power.iloc[:, 1]))
    
    # Country factor 딕셔너리 생성
    country_factor_dict = dict(zip(df_country_specific['Country'], df_country_specific['EQ']))
    
    # Design simplification 변수들
    design_factors = {
        'PIPING': DesignSimplification_safetyPIPING,
        'VALVES': DesignSimplification_safetyVALVES,
        'PUMPS': DesignSimplification_safetyPUMPS,
        'CABLES': DesignSimplification_safetyCABLES,
        'MECH': DesignSimplification_safetyMECH
    }
    
    # 각 행별로 스케일링 계수 계산
    scaling_factors = []
    
    for idx, row in result_df.iterrows():
        # 1) Power scaling factor
        power_description = row['POWER_SCALING']
        exponent = power_scaling_dict.get(power_description, 1.0)
        power_factor = (ElectricCapacityPerModule / 1400) ** exponent
        
        # 2) Module factor
        module_description = row['MODULE_FACTOR']
        if module_description == 'O':
            module_factor = ModuleNumber/2  # 기준이 2모듈이므로 2로 나눔
        else:  # 'X'인 경우
            module_factor = 2/2   # 기준이 2모듈이므로 2로 나눔
        
        # 3) Design simplification factor
        design_description = row['DESIGN_SIMPLIFICATIONS']
        if design_description == 'X':
            design_factor = 1.0
        else:
            design_factor = design_factors.get(design_description, 1.0)
        
        # 4) Country factor
        country_description = row['COUNTRY-SPECIFIC']
        if country_description == 'X':
            country_factor = 1.0
        else:  # 'O'인 경우
            country_factor = country_factor_dict.get(Country, 1.0)
        

        # 디버깅 출력
        #print(f"Row {idx}: power_factor={power_factor}, module_factor={module_factor}, design_factor={design_factor}, country_factor={country_factor}")
        
        # None 체크
        if power_factor is None or module_factor is None or design_factor is None or country_factor is None:
            print(f"None 발견! power_description='{power_description}', module_description='{module_description}', design_description='{design_description}', country_description='{country_description}'")
            total_scaling = 1.0  # 기본값 사용
        else:
            total_scaling = power_factor * module_factor * design_factor * country_factor
        

        scaling_factors.append(total_scaling)
    
    
    # print(f"Scaling factors: {scaling_factors}")
    # print(f"Scaling factors length: {len(scaling_factors)}")
    # print(f"Scaling factors type: {type(scaling_factors)}")
    # print(f"result_df:{result_df}")
    # exit()
    # 새로운 scaled 열들 생성
    result_df['scaled_APR1400_EQcost_2025USD_min'] = result_df['APR1400_EQcost_2025USD_min'] * scaling_factors
    result_df['scaled_APR1400_EQcost_2025USD_Mean'] = result_df['APR1400_EQcost_2025USD_Mean'] * scaling_factors
    result_df['scaled_APR1400_EQcost_2025USD_MAX'] = result_df['APR1400_EQcost_2025USD_MAX'] * scaling_factors
    
    return result_df



# CP별 합산한 값 반환 ######################################################################################################
def sum_by_CP(df_eqcost_processed, df_cp_list, minMeanMAX):

    #colname = 'APR1400_EQcost_2025USD_'+ minMeanMAX
    colname = 'scaled_APR1400_EQcost_2025USD_'+ minMeanMAX

    # Step 1: pandas pivot_table로 피벗 테이블 구성
    pivot_table = pd.pivot_table(df_eqcost_processed,
                                index='CP',                           # 행: CP
                                values=colname,   # 값: 지정된 열
                                aggfunc='sum').reset_index()          # 집계: 합계
    
    # Step 2: CP_List 기준으로 피벗 테이블을 입혀서 반환
    cp_col = df_cp_list.columns[0]  # CP-XX 열
    desc_col = df_cp_list.columns[1]  # 설명 열
    
    # CP_List를 기준으로 left join (모든 CP-XX 포함)
    result = pd.merge(df_cp_list, pivot_table, left_on=cp_col, right_on='CP', how='left')
    
    # 합계가 없는 경우 0으로 채우기
    result[colname] = result[colname].fillna(0)
    
    # 최종 결과: CP-XX, 설명, 합계
    final_result = result[[cp_col, desc_col, colname]].copy()
    final_result.columns = ['CP', 'Description', 'EQ_Cost_2025USD']  # 열 이름 변경
    
    return final_result


