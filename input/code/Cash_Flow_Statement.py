import pandas as pd
import math
import input.code.Fuel_Cost_Input as Fuel


def YEARS(prep_period, construction_period, operation_period):
    """
    Cash Flow Statement의 연도 행(YEAR) 생성
    """
    
    # 시작년도: -(건설준비기간 올림)
    start_year = -math.ceil(prep_period)
    
    # 종료년도: (건설기간 + 운영기간 올림)
    end_year = math.ceil(construction_period + operation_period)
    
    # 연도 리스트 생성
    years = list(range(start_year, end_year + 1))
    
    # DataFrame 생성 (연도들을 열로, YEAR 행 추가)
    cashflow_df = pd.DataFrame(index=['YEAR'], columns=years)
    
    # YEAR 행에 'Year' + 연도 값 입력
    cashflow_df.loc['YEAR'] = ['Year ' + str(year) for year in years]
    
    #print(cashflow_df)  # 디버깅용 출력
    
    return cashflow_df



def REVENUE(cashflow_df, ElectricCapacityPerModule, moduleNumber, electricityPrice, salesToRevenueRatio, capacityFactor, year_start, year_end):
    """
    Revenue를 Cash Flow에 매핑 (소수점 고려한 분배)
    
    Parameters:
    - cashflow_df: 연도별 Cash Flow DataFrame (YEAR 행 있는 상태)
    - ElectricCapacityPerModule, moduleNumber, electricityPrice, salesToRevenueRatio, capacityFactor: 수익 계산 변수들
    - year_start: 운영 시작 시점 (소수점 가능)
    - year_end: 운영 종료 시점 (소수점 가능)
    
    Returns:
    - REVENUE 행이 추가된 Cash Flow DataFrame
    """
    annual_revenue = ElectricCapacityPerModule * moduleNumber * electricityPrice * salesToRevenueRatio * capacityFactor * 8760 / 1000000  # in million USD
    # 기존 DataFrame에 REVENUE 행 추가 (YEAR 행은 유지)
    cashflow_df.loc['REVENUE'] = 0.0
    
    # 운영 시작 연도의 정수 부분과 소수 부분
    start_year_int = math.ceil(year_start)
    start_fraction = start_year_int - year_start  # 첫 해 운영 비율
    
    # 운영 종료 연도의 정수 부분과 소수 부분  
    end_year_int = math.floor(year_end)
    end_fraction = year_end - end_year_int  # 마지막 해 운영 비율
    
    # 첫 번째 운영 연도 (부분 운영)
    if start_year_int in cashflow_df.columns:
        cashflow_df.loc['REVENUE', start_year_int] = annual_revenue * start_fraction
    
    # 중간 완전 운영 연도들
    for year in range(start_year_int + 1, end_year_int + 1):
        if year in cashflow_df.columns:
            cashflow_df.loc['REVENUE', year] = annual_revenue
    
    # 마지막 운영 연도 (부분 운영)
    if end_fraction > 0 and (end_year_int + 1) in cashflow_df.columns:
        cashflow_df.loc['REVENUE', end_year_int + 1] = annual_revenue * end_fraction
    
    return cashflow_df



def OM_ANNUAL(SNU, cashflow_df, year_start, year_end,ElectricCapacityPerModule, moduleNumber):
    """
    OM Cost를 Cash Flow에 매핑 (연도별 상관식 적용)
    
    Parameters:
    - cashflow_df: 기존 Cash Flow DataFrame
    - year_start: 운영 시작 시점 (소수점 가능)
    - year_end: 운영 종료 시점 (소수점 가능)
    
    Returns:
    - 'OM Cost' 행이 추가된 Cash Flow DataFrame
    """
    
    # 기존 DataFrame에 OM Cost 행 추가
    cashflow_df.loc['Annual OM Cost'] = 0.0
    
    # 운영 시작 연도의 정수 부분과 소수 부분
    start_year_int = math.ceil(year_start)
    start_fraction = start_year_int - year_start
    
    # 운영 종료 연도의 정수 부분과 소수 부분
    end_year_int = math.floor(year_end)
    end_fraction = year_end - end_year_int
    
    # 첫 번째 운영 연도 (부분 운영)
    if start_year_int in cashflow_df.columns:
        age = start_fraction  # 첫 해는 부분 연도만큼의 AGE
        om_cost = (116 + 0.56 * age)*ElectricCapacityPerModule*moduleNumber/1000 if age <= 50 else (91 + 0.56 * age)*ElectricCapacityPerModule*moduleNumber/1000 # in million USD
        if SNU:
            om_cost = om_cost * 0.9
        cashflow_df.loc['Annual OM Cost', start_year_int] = -1* om_cost * start_fraction
    
    # 중간 완전 운영 연도들
    current_age = 1.0  # 두 번째 해부터는 AGE=1부터 시작
    for year in range(start_year_int + 1, end_year_int + 1):
        if year in cashflow_df.columns:
            om_cost = (116 + 0.56 * current_age)*ElectricCapacityPerModule*moduleNumber/1000 if current_age <= 50 else (91 + 0.56 * current_age)*ElectricCapacityPerModule*moduleNumber/1000
            if SNU:
                om_cost = om_cost * 0.9
            cashflow_df.loc['Annual OM Cost', year] = -1* om_cost
            current_age += 1.0
    
    # 마지막 운영 연도 (부분 운영)
    if end_fraction > 0 and (end_year_int + 1) in cashflow_df.columns:
        om_cost = (116 + 0.56 * current_age)*ElectricCapacityPerModule*moduleNumber/1000 if current_age <= 50 else (91 + 0.56 * current_age)*ElectricCapacityPerModule*moduleNumber/1000
        if SNU:
            om_cost = om_cost * 0.9
        cashflow_df.loc['Annual OM Cost', end_year_int + 1] = -1* om_cost * end_fraction
    
    return cashflow_df



def FUEL_FRONTEND(cashflow_df,year_start, year_end, Feed, Product, Tail, totalFuelQty, U3O8Price, EnrichmentPrice, FabricationPrice, ConversionPrice,moduleNumber,BatchNumber, BatchCycleLength, CoreDesignFactor):
    """
    Fuel Cost를 Cash Flow에 매핑 (소수점 고려한 분배)
    
    Parameters:
    - cashflow_df: 기존 Cash Flow DataFrame
    - annual_fuel_cost: 연간 연료 비용
    - year_start: 운영 시작 시점 (소수점 가능)
    - year_end: 운영 종료 시점 (소수점 가능)
    
    Returns:
    - 'FUEL_FRONTEND' 행이 추가된 Cash Flow DataFrame
    """
    
    annual_fuel_cost, ratio = Fuel.FrontEnd(Feed, Product, Tail, totalFuelQty, U3O8Price, EnrichmentPrice, FabricationPrice, ConversionPrice,moduleNumber,BatchNumber, BatchCycleLength, CoreDesignFactor)

    # 기존 DataFrame에 FUEL_FRONTEND 행 추가
    cashflow_df.loc['FUEL (Front-end)'] = 0.0
    
    # 운영 시작 연도의 정수 부분과 소수 부분
    start_year_int = math.ceil(year_start)
    start_fraction = start_year_int - year_start  # 첫 해 운영 비율
    
    # 운영 종료 연도의 정수 부분과 소수 부분  
    end_year_int = math.floor(year_end)
    end_fraction = year_end - end_year_int  # 마지막 해 운영 비율
    
    # 첫 번째 운영 연도 (부분 운영)
    if start_year_int in cashflow_df.columns:
        cashflow_df.loc['FUEL (Front-end)', start_year_int] = -1* annual_fuel_cost * start_fraction
    
    # 중간 완전 운영 연도들
    for year in range(start_year_int + 1, end_year_int + 1):
        if year in cashflow_df.columns:
            cashflow_df.loc['FUEL (Front-end)', year] = -1* annual_fuel_cost
    
    # 마지막 운영 연도 (부분 운영)
    if end_fraction > 0 and (end_year_int + 1) in cashflow_df.columns:
        cashflow_df.loc['FUEL (Front-end)', end_year_int + 1] = -1* annual_fuel_cost * end_fraction
    
    return cashflow_df, ratio



def FUEL_INTERIM_STORAGE(CFS, initial_investment, annual_cask_cost, annual_om_cost, operation_start, operation_end, dry_storage_period, batch_length):
    """
    Fuel Interim Storage 비용을 Cash Flow Statement에 추가
    
    Parameters:
    - CFS: 기존 Cash Flow Statement
    - initial_investment: 초기 투자비
    - annual_cask_cost: 연간 Cask 비용  
    - annual_om_cost: 연간 OM 비용
    - operation_start: 원전 운영 시작 시점
    - operation_end: 원전 운영 종료 시점
    - dry_storage_period: 건식저장 보관 기간
    - batch_length: 배치 길이
    
    Returns:
    - FUEL (Interim Storage) 행이 추가된 CFS
    """
    
    result_CFS = CFS.copy()
    years = CFS.columns.tolist()
    
    # FUEL (Interim Storage) 행 초기화
    fuel_interim_values = pd.Series(0.0, index=years)
    
    # 1. 초기 투자비: 원전 운영 시작 시점에 1회성
    start_year_int = math.ceil(operation_start)
    if start_year_int in years:
        fuel_interim_values[start_year_int] += -initial_investment  # 비용이므로 음수
    
    # 2. 연간 Cask 비용: 운영 시작 + batch_length부터 운영 종료까지
    cask_start = operation_start + batch_length/12  # batch_length는 개월 단위이므로 12로 나눔
    cask_start_int = math.ceil(cask_start)
    operation_end_int = math.floor(operation_end)
    
    for year in range(cask_start_int, operation_end_int + 1):
        if year in years:
            fuel_interim_values[year] += -annual_cask_cost  # 비용이므로 음수
    
    # 3. 연간 OM 비용: 운영 시작부터 운영 종료 + 건식저장 기간까지
    om_end = operation_end + dry_storage_period
    om_end_int = math.floor(om_end)
    
    for year in range(start_year_int, om_end_int + 1):
        if year in years:
            fuel_interim_values[year] += -annual_om_cost  # 비용이므로 음수
    
    # 4. 'FUEL (Front-end)' 행 아래에 'FUEL (Interim Storage)' 행 삽입
    current_index = result_CFS.index.tolist()
    
    try:
        fuel_frontend_idx = current_index.index('FUEL_FRONTEND')
        fuel_interim_row = pd.DataFrame([fuel_interim_values], index=['FUEL (Interim Storage)'])
        
        # FUEL_FRONTEND 다음에 삽입
        top_part = result_CFS.iloc[:fuel_frontend_idx + 1]
        bottom_part = result_CFS.iloc[fuel_frontend_idx + 1:]
        result_CFS = pd.concat([top_part, fuel_interim_row, bottom_part], axis=0)
        
    except ValueError:
        # FUEL_FRONTEND 행이 없는 경우 맨 뒤에 추가
        fuel_interim_row = pd.DataFrame([fuel_interim_values], index=['FUEL (Interim Storage)'])
        result_CFS = pd.concat([result_CFS, fuel_interim_row], axis=0)
    
    return result_CFS



def GROSS_PROFIT(cashflow_df):
    """
    Gross Profit 행을 Cash Flow에 추가
    Gross Profit = REVENUE - OM Cost - FUEL_FRONTEND
    
    Parameters:
    - cashflow_df: 기존 Cash Flow DataFrame (REVENUE, OM Cost, FUEL_FRONTEND 행 포함)
    
    Returns:
    - 'Gross Profit' 행이 추가된 Cash Flow DataFrame
    """
    
    # Gross Profit 행 추가
    cashflow_df.loc['GROSS PROFIT'] = (
        cashflow_df.loc['REVENUE'] + 
        cashflow_df.loc['Annual OM Cost'] + 
        cashflow_df.loc['FUEL (Front-end)'] + 
        cashflow_df.loc['FUEL (Interim Storage)']
    )
    
    return cashflow_df



def OM_CAPITAL(cashflow_df, year_start, year_end, ElectricCapacityPerModule, moduleNumber):
    """
    Capital OM Cost를 Cash Flow에 매핑 (연도별 상관식 적용)
    
    Parameters:
    - cashflow_df: 기존 Cash Flow DataFrame
    - year_start: 운영 시작 시점 (소수점 가능)
    - year_end: 운영 종료 시점 (소수점 가능)
    
    Returns:
    - 'Capital OM Cost' 행이 추가된 Cash Flow DataFrame
    """
    
    # 기존 DataFrame에 Capital OM Cost 행 추가
    cashflow_df.loc['Capital OM Cost'] = 0.0
    
    # 운영 시작 연도의 정수 부분과 소수 부분
    start_year_int = math.ceil(year_start)
    start_fraction = start_year_int - year_start
    
    # 운영 종료 연도의 정수 부분과 소수 부분
    end_year_int = math.floor(year_end)
    end_fraction = year_end - end_year_int
    
    # 첫 번째 운영 연도 (부분 운영)
    if start_year_int in cashflow_df.columns:
        age = start_fraction  # 첫 해는 부분 연도만큼의 AGE
        capital_om_cost = (17 + 1.25 * age)*ElectricCapacityPerModule*moduleNumber/1000 # in million USD
        cashflow_df.loc['Capital OM Cost', start_year_int] = -1* capital_om_cost * start_fraction
    
    # 중간 완전 운영 연도들
    current_age = 1.0  # 두 번째 해부터는 AGE=1부터 시작
    for year in range(start_year_int + 1, end_year_int + 1):
        if year in cashflow_df.columns:
            capital_om_cost = (17 + 1.25 * current_age)*ElectricCapacityPerModule*moduleNumber/1000
            cashflow_df.loc['Capital OM Cost', year] = -1* capital_om_cost
            current_age += 1.0
    
    # 마지막 운영 연도 (부분 운영)
    if end_fraction > 0 and (end_year_int + 1) in cashflow_df.columns:
        capital_om_cost = (17 + 1.25 * current_age)*ElectricCapacityPerModule*moduleNumber/1000
        cashflow_df.loc['Capital OM Cost', end_year_int + 1] = -1* capital_om_cost * end_fraction
    
    return cashflow_df



def CAPEX(CFS, df_afterESCALATION):
    """
    CAPEX 데이터를 Cash Flow Statement에 추가
    
    Parameters:
    - CFS: 기존 Cash Flow Statement DataFrame
    - df_afterESCALATION: CAPEX 함수의 반환값 (CP별 연도별 비용)
    
    Returns:
    - CAPEX 행이 추가된 Cash Flow Statement
    """
    
    # 1단계: CAPEX 데이터를 열방향으로 sum하여 1행 DataFrame 생성
    capex_sum = df_afterESCALATION.sum(axis=0)  # 각 열(연도)별 합계
    
    # 2단계: 1행 DataFrame 생성 (행 인덱스는 'CAPEX')
    capex_row = pd.DataFrame([-1*capex_sum], index=['CAPEX'])
    
    # 3단계: CFS 하단에 CAPEX 행 추가
    result_CFS = pd.concat([CFS, capex_row], axis=0)
    
    return result_CFS



def CAPEX_DEBT(debtToEquityRatio, CFS_with_CAPEX):
    """
    CAPEX의 부채 부분을 Cash Flow Statement에 추가
    
    Parameters:
    - debtToEquityRatio: 부채/자기자본 비율
    - CFS_with_CAPEX: CAPEX 행이 포함된 Cash Flow Statement
    
    Returns:
    - 'CAPEX (DEBT portion)' 행이 추가된 Cash Flow Statement
    """
    
    # 1단계: 기존 CFS 복사
    result_CFS = CFS_with_CAPEX.copy()
    
    # 2단계: CAPEX 행의 값들 가져오기
    capex_values = CFS_with_CAPEX.loc['CAPEX']
    
    # 3단계: debtToEquityRatio와 -1을 곱한 값 계산
    capex_debt_values = capex_values * debtToEquityRatio * (-1)
    
    # 4단계: 새로운 행 생성 (인덱스 이름: 'CAPEX (DEBT portion)')
    capex_debt_row = pd.DataFrame([capex_debt_values], index=['CAPEX (DEBT portion)'])
    
    # 5단계: CFS 맨 아래에 추가
    result_CFS = pd.concat([result_CFS, capex_debt_row], axis=0)
    
    return result_CFS



def INTERESTnDEBTrepayment(CFS, interestRate, loanTenor, constructionPeriod):
    """
    Interest 및 Debt Repayment를 Cash Flow Statement에 추가
    """
    
    result_CFS = CFS.copy()
    years = CFS.columns.tolist()
    
    # 건설기간과 운영기간 구분
    construction_end = constructionPeriod
    construction_years = [year for year in years if year <= construction_end]
    operation_years = [year for year in years if year > construction_end]
    
    # CAPEX (DEBT portion) 행 가져오기
    capex_debt_values = CFS.loc['CAPEX (DEBT portion)']
    
    # 1단계: 건설기간 중 이자 계산
    interest_values = pd.Series(0.0, index=years)
    cumulative_debt = 0.0
    
    for i, year in enumerate(construction_years):
        current_debt = capex_debt_values[year] if capex_debt_values[year] > 0 else 0
        
        if cumulative_debt > 0:
            current_year_interest = cumulative_debt * interestRate
            interest_values[year] = -current_year_interest
        
        cumulative_debt = cumulative_debt * (1 + interestRate) + current_debt
    
    total_debt = cumulative_debt
    
    # 3단계: 운영기간 중 상환 계산
    debt_repayment_values = pd.Series(0.0, index=years)
    
    if len(operation_years) > 0 and total_debt > 0:
        repayment_years = operation_years[:loanTenor] if len(operation_years) >= loanTenor else operation_years
        
        if len(repayment_years) > 0:
            annual_repayment = total_debt / len(repayment_years)
            
            for year in repayment_years:
                debt_repayment_values[year] = -annual_repayment
        
        # 운영기간 중 이자 계산
        remaining_debt = total_debt
        for year in operation_years:
            if remaining_debt > 0:
                current_year_interest = remaining_debt * interestRate
                interest_values[year] = -current_year_interest
                
                if year in repayment_years:
                    remaining_debt -= annual_repayment
                    if remaining_debt < 0:
                        remaining_debt = 0
    
    # INTEREST 행을 'Gross Profit'과 'Capital OM Cost' 사이에 삽입
    current_index = result_CFS.index.tolist()
    
    try:
        capital_om_idx = current_index.index('Capital OM Cost')
        interest_row = pd.DataFrame([interest_values], index=['INTEREST'])
        
        # Capital OM Cost 앞에 INTEREST 삽입
        top_part = result_CFS.iloc[:capital_om_idx]
        bottom_part = result_CFS.iloc[capital_om_idx:]
        result_CFS = pd.concat([top_part, interest_row, bottom_part], axis=0)
        
    except ValueError:
        # Capital OM Cost 행이 없는 경우 맨 뒤에 추가
        interest_row = pd.DataFrame([interest_values], index=['INTEREST'])
        result_CFS = pd.concat([result_CFS, interest_row], axis=0)
    
    debt_repayment_row = pd.DataFrame([debt_repayment_values], index=['DEBT repayment'])
    result_CFS = pd.concat([result_CFS, debt_repayment_row], axis=0)
    
    return result_CFS



def DEPRECIATIONandAMORTIZATION(CFS, constructionPeriod, plantLifetime):
    """
    Depreciation and Amortization을 Cash Flow Statement에 추가
    
    Parameters:
    - CFS: 기존 Cash Flow Statement
    - constructionPeriod: 건설 기간 (운영 시작점)
    - plantLifetime: 발전소 운영 기간
    
    Returns:
    - DnA (sub), DnA (add) 행이 추가된 CFS
    """
    
    result_CFS = CFS.copy()
    years = CFS.columns.tolist()
    
    # 1단계: CAPEX 행의 총합 계산
    capex_values = CFS.loc['CAPEX']
    total_capex = capex_values.sum()  # 음수가 될 것
    
    # 2단계: 운영기간 설정 (REVENUE 함수와 동일)
    operation_start = constructionPeriod
    operation_end = constructionPeriod + plantLifetime
    
    # 3단계: DnA 값을 운영기간에 균등 분배 (소수점 고려)
    dna_sub_values = pd.Series(0.0, index=years)
    
    # 운영 시작 연도의 정수 부분과 소수 부분
    start_year_int = math.ceil(operation_start)
    start_fraction = start_year_int - operation_start
    
    # 운영 종료 연도의 정수 부분과 소수 부분  
    end_year_int = math.floor(operation_end)
    end_fraction = operation_end - end_year_int
    
    # 총 운영기간
    total_operation_period = operation_end - operation_start
    annual_dna = total_capex / total_operation_period if total_operation_period > 0 else 0
    
    # 첫 번째 운영 연도 (부분 운영)
    if start_year_int in years:
        dna_sub_values[start_year_int] = annual_dna * start_fraction
    
    # 중간 완전 운영 연도들
    for year in range(start_year_int + 1, end_year_int + 1):
        if year in years:
            dna_sub_values[year] = annual_dna
    
    # 마지막 운영 연도 (부분 운영)
    if end_fraction > 0 and (end_year_int + 1) in years:
        dna_sub_values[end_year_int + 1] = annual_dna * end_fraction
    
    # 4단계: DnA (add) 값 생성 (sub의 -1배)
    dna_add_values = -dna_sub_values
    
    # 5단계: 행 삽입
    current_index = result_CFS.index.tolist()
    
    # 'Depreciation and Amortization (sub)'를 'GROSS PROFIT'과 'INTEREST' 사이에 삽입
    try:
        interest_idx = current_index.index('INTEREST')
        dna_sub_row = pd.DataFrame([dna_sub_values], index=['Depreciation and Amortization (sub)'])
        
        # INTEREST 앞에 삽입
        top_part = result_CFS.iloc[:interest_idx]
        bottom_part = result_CFS.iloc[interest_idx:]
        result_CFS = pd.concat([top_part, dna_sub_row, bottom_part], axis=0)
        
        # 인덱스 업데이트 (새로운 행이 추가되었으므로)
        current_index = result_CFS.index.tolist()
        
    except ValueError:
        # INTEREST 행이 없는 경우 맨 뒤에 추가
        dna_sub_row = pd.DataFrame([dna_sub_values], index=['Depreciation and Amortization (sub)'])
        result_CFS = pd.concat([result_CFS, dna_sub_row], axis=0)
        current_index = result_CFS.index.tolist()
    
    # 'Depreciation and Amortization (add)'를 'INTEREST'와 'Capital OM Cost' 사이에 삽입
    try:
        capital_om_idx = current_index.index('Capital OM Cost')
        dna_add_row = pd.DataFrame([dna_add_values], index=['Depreciation and Amortization (add)'])
        
        # Capital OM Cost 앞에 삽입
        top_part = result_CFS.iloc[:capital_om_idx]
        bottom_part = result_CFS.iloc[capital_om_idx:]
        result_CFS = pd.concat([top_part, dna_add_row, bottom_part], axis=0)
        
    except ValueError:
        # Capital OM Cost 행이 없는 경우 맨 뒤에 추가
        dna_add_row = pd.DataFrame([dna_add_values], index=['Depreciation and Amortization (add)'])
        result_CFS = pd.concat([result_CFS, dna_add_row], axis=0)
    
    return result_CFS



def EBIT(CFS):
    """
    GROSS PROFIT와 Depreciation and Amortization (sub)을 합산해 EBIT 행을 만들고,
    'Depreciation and Amortization (sub)'과 'INTEREST' 사이에 삽입한다.

    Parameters
    ----------
    CFS : pd.DataFrame
        Cash Flow Statement DataFrame (행 인덱스: 항목, 열: 기간)

    Returns
    -------
    pd.DataFrame
        EBIT 행이 추가 또는 갱신된 DataFrame
    """
    df = CFS.copy()

    # 필요한 행 존재 여부 체크
    if "GROSS PROFIT" not in df.index:
        raise KeyError("'GROSS PROFIT' 행이 없습니다.")
    if "Depreciation and Amortization (sub)" not in df.index:
        raise KeyError("'Depreciation and Amortization (sub)' 행이 없습니다.")

    # EBIT 계산
    ebit_values = df.loc["GROSS PROFIT"] + df.loc["Depreciation and Amortization (sub)"]
    ebit_row = pd.DataFrame([ebit_values], index=["EBIT"])

    # 기존 EBIT가 있으면 제거 후 교체
    if "EBIT" in df.index:
        df = df.drop(index="EBIT")

    idx_list = df.index.tolist()

    # 삽입 위치 결정
    if "INTEREST" in idx_list and "Depreciation and Amortization (sub)" in idx_list:
        insert_pos = idx_list.index("INTEREST")
    elif "Depreciation and Amortization (sub)" in idx_list:
        insert_pos = idx_list.index("Depreciation and Amortization (sub)") + 1
    elif "INTEREST" in idx_list:
        insert_pos = idx_list.index("INTEREST")
    else:
        insert_pos = len(idx_list)

    # 삽입
    top = df.iloc[:insert_pos]
    bottom = df.iloc[insert_pos:]
    result = pd.concat([top, ebit_row, bottom], axis=0)

    return result



def EBT(CFS):
    """
    EBIT와 INTEREST를 합산해 'EBT (Taxable Income)' 행을 만들고,
    'Depreciation and Amortization (add)' 위에 삽입한다.

    Parameters
    ----------
    CFS : pd.DataFrame
        Cash Flow Statement DataFrame (행 인덱스: 항목, 열: 기간)

    Returns
    -------
    pd.DataFrame
        'EBT (Taxable Income)' 행이 추가 또는 갱신된 DataFrame
    """
    df = CFS.copy()

    # 필요한 행 존재 여부 체크
    if "EBIT" not in df.index:
        raise KeyError("'EBIT' 행이 없습니다.")
    if "INTEREST" not in df.index:
        raise KeyError("'INTEREST' 행이 없습니다.")

    # EBT 계산
    ebt_values = df.loc["EBIT"] + df.loc["INTEREST"]
    ebt_row = pd.DataFrame([ebt_values], index=["EBT (Taxable Income)"])

    # 기존 EBT가 있으면 제거 후 교체
    if "EBT (Taxable Income)" in df.index:
        df = df.drop(index="EBT (Taxable Income)")

    idx_list = df.index.tolist()

    # 삽입 위치 결정
    if "Depreciation and Amortization (add)" in idx_list:
        insert_pos = idx_list.index("Depreciation and Amortization (add)")
    else:
        insert_pos = len(idx_list)  # 없으면 맨 뒤에 추가

    # 삽입
    top = df.iloc[:insert_pos]
    bottom = df.iloc[insert_pos:]
    result = pd.concat([top, ebt_row, bottom], axis=0)

    return result



def TAX(CFS, taxRate):
    """
    'EBT (Taxable Income)'에 -1*taxRate를 곱해 'TAX' 행을 만들고,
    'Depreciation and Amortization (add)' 위에 삽입한다.
    단, EBT가 음수일 경우 세금은 0으로 처리한다.

    Parameters
    ----------
    CFS : pd.DataFrame
        Cash Flow Statement DataFrame (행 인덱스: 항목, 열: 기간)
    taxRate : float
        세율 (예: 0.21)

    Returns
    -------
    pd.DataFrame
        'TAX' 행이 추가 또는 갱신된 DataFrame
    """
    df = CFS.copy()

    # 필요한 행 존재 여부 체크
    if "EBT (Taxable Income)" not in df.index:
        raise KeyError("'EBT (Taxable Income)' 행이 없습니다.")

    # TAX 계산: EBT>0인 경우만 세금 부과
    ebt_values = df.loc["EBT (Taxable Income)"]
    tax_values = ebt_values.apply(lambda x: -taxRate * x if x > 0 else 0)
    tax_row = pd.DataFrame([tax_values], index=["TAX"])

    # 기존 TAX가 있으면 제거 후 교체
    if "TAX" in df.index:
        df = df.drop(index="TAX")

    idx_list = df.index.tolist()

    # 삽입 위치 결정
    if "Depreciation and Amortization (add)" in idx_list:
        insert_pos = idx_list.index("Depreciation and Amortization (add)")
    else:
        insert_pos = len(idx_list)  # 없으면 맨 뒤에 추가

    # 삽입
    top = df.iloc[:insert_pos]
    bottom = df.iloc[insert_pos:]
    result = pd.concat([top, tax_row, bottom], axis=0)

    return result



def NI(CFS):
    """
    'EBT (Taxable Income)' + 'TAX'를 계산해 'NET INCOME' 행을 만들고,
    'Depreciation and Amortization (add)' 위에 삽입한다.

    Parameters
    ----------
    CFS : pd.DataFrame
        Cash Flow Statement DataFrame (행 인덱스: 항목, 열: 기간)

    Returns
    -------
    pd.DataFrame
        'NET INCOME' 행이 추가 또는 갱신된 DataFrame
    """
    df = CFS.copy()

    # 필요한 행 존재 여부 체크
    if "EBT (Taxable Income)" not in df.index:
        raise KeyError("'EBT (Taxable Income)' 행이 없습니다.")
    if "TAX" not in df.index:
        raise KeyError("'TAX' 행이 없습니다.")

    # NET INCOME 계산
    ni_values = df.loc["EBT (Taxable Income)"] + df.loc["TAX"]
    ni_row = pd.DataFrame([ni_values], index=["NET INCOME"])

    # 기존 NET INCOME이 있으면 제거 후 교체
    if "NET INCOME" in df.index:
        df = df.drop(index="NET INCOME")

    idx_list = df.index.tolist()

    # 삽입 위치 결정
    if "Depreciation and Amortization (add)" in idx_list:
        insert_pos = idx_list.index("Depreciation and Amortization (add)")
    else:
        insert_pos = len(idx_list)  # 없으면 맨 뒤에 추가

    # 삽입
    top = df.iloc[:insert_pos]
    bottom = df.iloc[insert_pos:]
    result = pd.concat([top, ni_row, bottom], axis=0)

    return result


def CASH_FLOW(CFS):
    """
    'NET INCOME', 'Depreciation and Amortization (add)', 
    'Capital OM Cost', 'CAPEX', 'CAPEX (DEBT portion)', 'DEBT repayment'
    을 합산하여 'CASH FLOW' 행을 만들고, DataFrame 최하단에 추가한다.

    Parameters
    ----------
    CFS : pd.DataFrame
        Cash Flow Statement DataFrame (행 인덱스: 항목, 열: 기간)

    Returns
    -------
    pd.DataFrame
        'CASH FLOW' 행이 추가 또는 갱신된 DataFrame
    """
    df = CFS.copy()

    required_rows = [
        "NET INCOME",
        "Depreciation and Amortization (add)",
        "Capital OM Cost",
        "CAPEX",
        "CAPEX (DEBT portion)",
        "DEBT repayment",
    ]

    # 모든 필수 행이 있는지 확인
    missing = [row for row in required_rows if row not in df.index]
    if missing:
        raise KeyError(f"필수 행이 누락되었습니다: {missing}")

    # CASH FLOW 계산
    cashflow_values = sum(df.loc[row] for row in required_rows)
    cashflow_row = pd.DataFrame([cashflow_values], index=["CASH FLOW"])

    # 기존 CASH FLOW가 있으면 제거 후 교체
    if "CASH FLOW" in df.index:
        df = df.drop(index="CASH FLOW")

    # 맨 아래에 삽입
    result = pd.concat([df, cashflow_row], axis=0)

    return result

