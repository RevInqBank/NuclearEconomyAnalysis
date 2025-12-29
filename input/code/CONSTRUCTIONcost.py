def scaling(df_CP_List, df_scaling_power, df_country_specific, 
                        Country, moduleNumber, ElectricCapacityPerModule):
    """
    Labor Cost 계산 함수 (EQ Cost Scaling과 유사하지만 차이점 있음)
    
    Parameters:
    - df_CP_List: CP 리스트 데이터
    - df_scaling_power: SCALING_POWER_EXPONENT 데이터
    - df_country_specific: COUNTRY_SPECIFIC 데이터  
    - Country: 국가명
    - moduleNumber: 모듈 수
    - ElectricCapacityPerModule: 모듈당 전기 용량
    
    Returns:
    - scaled_APR1400_CONSTRUCTIONcost_2025USD 열이 추가된 데이터프레임
    """
    
    result_df = df_CP_List.copy()
    
    # 1) Power scaling exponent 딕셔너리 생성
    power_scaling_dict = dict(zip(df_scaling_power.iloc[:, 0], df_scaling_power.iloc[:, 1]))
    
    # 2) Country factor 딕셔너리 생성 (LABOR 열 사용)
    country_labor_dict = dict(zip(df_country_specific['Country'], df_country_specific['LABOR']))
    
    # 3) Total Power 계산
    total_power = moduleNumber * ElectricCapacityPerModule
    
    scaling_factors = []
    
    for idx, row in result_df.iterrows():
        # 4-1) Power Scaling Factor
        power_description = row['POWER_SCALING']
        exponent = power_scaling_dict.get(power_description, 1.0)
        
        # POWER_SCALING_CAPACITY에 따라 분기
        capacity_type = row['POWER_SCALING_CAPACITY']
        if capacity_type == 'TOTAL':
            power_factor = (total_power / 1400) ** exponent
        else:  # 'MODULE'인 경우
            power_factor = (ElectricCapacityPerModule / 1400) ** exponent
        
        # 4-2) Module Factor (EQ.scaling과 동일)
        module_description = row['MODULE_FACTOR']
        if module_description == 'O':
            module_factor = moduleNumber/2 # 기준이 2모듈이므로 2로 나눔
        else:  # 'X'인 경우
            module_factor = 2/2        # 기준이 2모듈이므로 2로 나눔
        
        # 4-3) Country Factor (LABOR 열 사용)
        country_description = row['COUNTRY-SPECIFIC']
        if country_description == 'X':
            country_factor = 1.0
        else:  # 'O'인 경우
            country_factor = country_labor_dict.get(Country, 1.0)
        
        # 총 스케일링 계수
        total_scaling = power_factor * module_factor * country_factor/1000000 # million USD로 변환
        scaling_factors.append(total_scaling)
    
    # 새로운 scaled 열 생성
    result_df['scaled_APR1400_CONSTRUCTIONcost_2025USD'] = (
        result_df['APR1400_CONSTRUCTIONcost_2025USD'] * scaling_factors
    )
    
    return result_df
