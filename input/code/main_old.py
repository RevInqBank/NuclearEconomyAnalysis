import pandas as pd
import numpy as np
import Reactor_Selection as RS
import readInput as read
import EQcost as EQ
import CONSTRUCTIONcost as CON
import Fuel_Cost_Input as Fuel
import Cash_Flow_Statement as CF
import Escalation as ESCALATION
import Analysis as ANALYSIS
import matplotlib.pyplot as plt
import os
import numpy_financial as npf  

def snapshot_declared_vars(output_path="output/input_snapshot.xlsx"):
    """
    현재 모듈(globals())에 존재하는 '사전 선언 변수들'의
    value / python type / pandas dtype-ish / 결측 여부 등을 스냅샷으로 저장.
    """

    declared_var_names = [
        # 1. Reactor Selection
        "powerDensity", "activeCoreD", "activeCoreDpct", "activeCoreH", "activeCoreHpct",
        "TGefficiency", "moduleNumber",

        # 2. Fuel Cost - Front End
        "Feed", "Product", "Tail", "totalFuelQty", "U3O8Price", "EnrichmentPrice",
        "FabricationPrice", "ConversionPrice", "BatchNumber", "BatchCycleLength", "CoreDesignFactor",

        # 2. Fuel Cost - Interim Storage
        "interimCOST_initial", "interimCOST_OM", "COSTperHM", "HMperASSEMBLY",
        "ASSEMBLYperCORE", "yearsForInterimStorage",

        # 3. O&M
        "annualOMcost",

        # 4. Operation
        "plantLifetime", "capacityFactor", "electricityPrice", "salesToRevenueRatio",

        # 5. Financial
        "escalationNSSS", "escalationTG", "escalationBOP", "escalationLabor",
        "escalationInterimStorage", "escalationDisposal",
        "debtToEquityRatio", "interestRate", "loanTenor", "depreciationPeriod",
        "taxRate", "discountRate",

        # 6. Cost
        "minMeanMAX",

        # 7. Scaling
        "DesignSimplification_safetyPIPING", "DesignSimplification_safetyVALVES",
        "DesignSimplification_safetyPUMPS", "DesignSimplification_safetyCABLES",
        "DesignSimplification_safetyMECH",

        # 8. Country
        "Country",
    ]

    rows = []
    g = globals()

    for name in declared_var_names:
        if name in g:
            v = g[name]
            py_type = type(v).__name__
            is_na = (v is None) or (isinstance(v, float) and np.isnan(v)) or (pd.isna(v))

            # 보기 좋게 문자열로
            if isinstance(v, (float, np.floating)):
                value_str = repr(float(v))
            else:
                value_str = repr(v)

            rows.append({
                "var": name,
                "value": value_str,
                "python_type": py_type,
                "is_missing": bool(is_na),
            })
        else:
            rows.append({
                "var": name,
                "value": "<NOT_IN_GLOBALS>",
                "python_type": "<N/A>",
                "is_missing": True,
            })

    df = pd.DataFrame(rows)

    # output 폴더 생성
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # 저장
    df.to_excel(output_path, index=False)
    print(f"[saved] {output_path}")

    return df



'''''
이건 그냥 건설 기간 우선 정하고 하는것 
'''''
constructionPeriod = 10.45  # years
preconstructionPeriod = 2  # years


'''
# Step 0: 변수 선언 및 초기화 ##########################################################################################################################
'''

# 1. Reactor Selection 변수들 선언 및 초기화 ########
powerDensity = None
powerDensity = None
activeCoreD  = None
activeCoreDpct = None
activeCoreH  = None
activeCoreHpct = None
TGefficiency = None
moduleNumber = None



# 2. Fuel Cost 변수들 선언 및 초기화 ###############
# Front End
Feed = None
Product = None
Tail = None
totalFuelQty = None
U3O8Price = None
EnrichmentPrice = None
FabricationPrice = None
ConversionPrice = None
BatchNumber = None         #새로 추가한 변수들
BatchCycleLength = None    #새로 추가한 변수들
CoreDesignFactor = None    #새로 추가한 변수들

# Interim Storage
interimCOST_initial = None #초기 투자 비용
interimCOST_OM = None      #연간 O&M 비용
COSTperHM = None  #Cask 비용 + 운송 비용 (HM ton 당)
HMperASSEMBLY = None
ASSEMBLYperCORE = None
yearsForInterimStorage = None


# Disposal




# 3. O&M Cost 변수들 선언 및 초기화 #################
annualOMcost = None



# 4. Operation 변수들 선언 및 초기화 ##############
# Calculation
plantLifetime = None      # 이름만 변경: 원래 이름은 Operating Year 였음 (엑셀 기준)
capacityFactor = None

# Electricity Sales
electricityPrice = None
salesToRevenueRatio = None #엑셀 기준 정산조정계수



# 5. Financial 변수들 선언 및 초기화 ##############
# Escalation
escalationNSSS = None
escalationTG = None
escalationBOP = None
escalationLabor = None
#escalationOM = None 
escalationInterimStorage = None     #새로 추가한 변수들
escalationDisposal = None           #새로 추가한 변수들

#Financing Structure 
debtToEquityRatio = None
interestRate = None
loanTenor = None
depreciationPeriod = None
taxRate = None

# Analysis 
discountRate = None


# 6. Cost 변수들 선언 및 초기화 #####################
minMeanMAX = None # 새로 추가된 변수들



# 7. Scaling 변수들 (Safety 만) ###################
#Safety만
DesignSimplification_safetyPIPING = None
DesignSimplification_safetyVALVES = None
DesignSimplification_safetyPUMPS = None
DesignSimplification_safetyCABLES = None
DesignSimplification_safetyMECH = None #새로 도입한 변수


# 8. Country-Specific Drivers ###################
Country = None 













'''
# STEP 1: 엑셀 파일에서 INPUT 변수 및 값들 읽어오기 ####################################################################################################
'''
import os

# 현재 작업 디렉토리 구하기
current_directory = os.getcwd()

# 현재 폴더의 INPUT.xlsx 경로
input_file = os.path.join(current_directory, "INPUT.xlsx")

# 사용
read.Input(input_file)

# # want to save data and data type from 
# snapshot_declared_vars("output/input_snapshot.xlsx")
# exit()

'''
# STEP 2: Source 데이터 읽어오기 및 계산 (하나의 파일에서 여러 시트 읽기) #########################################################################################################₩
'''
source_file =  os.path.join(current_directory, "SOURCE_DATA.xlsx")

df_EQcost_original = pd.read_excel(source_file, sheet_name='EQcost') # EQ Cost 원본 데이터
df_currency = pd.read_excel(source_file, sheet_name='Currency') # 환율 데이터
df_dollarValue = pd.read_excel(source_file, sheet_name='dollarValue') # CPI 데이터
df_CP_List = pd.read_excel(source_file, sheet_name='CP_List') # CP List 데이터
df_scaling_power = pd.read_excel(source_file, sheet_name='SCALING_POWER_EXPONENT') # Scaling Power Exponent 데이터
df_country_specific = pd.read_excel(source_file, sheet_name='COUNTRY_SPECIFIC') # Country Specific 데이터




''''# INPUT 수정 기회  ##############################################################################################################
# '''

# Product = 0.062
# BatchNumber = 2.3
# BatchCycleLength = 24
# capacityFactor = 0.923

''''
#############################################################################################################
'''







# Schedule 데이터 (임시!!!)
df_schedule = pd.read_excel(source_file, sheet_name='SCHEDULE') # Schedule 데이터 (임시!!!)

# Reactor Selection Output ###########
(ThermalCapacityPerModule, 
 ElectricCapacityPerModule, 
 TotalCapacity, 
 CoreH, 
 CoreD, 
 RPVvolume) = RS.Core(powerDensity, activeCoreD, activeCoreH, activeCoreDpct, activeCoreHpct, TGefficiency, moduleNumber)


# Fuel Interim Storage  ###########
annualCost_CASK = Fuel.InterimStorage(COSTperHM, HMperASSEMBLY,BatchNumber, BatchCycleLength, ASSEMBLYperCORE, moduleNumber)

print(annualCost_CASK)









'''
# STEP 3: EQ Cost 계산 ##############################################################################################################
'''
df_EQcost_original = EQ.convert_currency(df_EQcost_original, df_currency) # 환율 변환 후 우측에 4개 열 추가
df_EQcost_original = EQ.adjust_dollar_value(df_EQcost_original, df_dollarValue) # 딜러가치 변환 우측에 4개 열 추가 
df_EQcost_original = EQ.mergeEQcost(df_EQcost_original) # min / Mean / MAX 구하기

df_EQcost_original = EQ.scaling(Country, df_EQcost_original, df_scaling_power, df_country_specific, ElectricCapacityPerModule, moduleNumber, 
                 DesignSimplification_safetyPIPING, DesignSimplification_safetyVALVES, 
                 DesignSimplification_safetyPUMPS, DesignSimplification_safetyCABLES, 
                 DesignSimplification_safetyMECH) # min / Mean / MAX 구하기
#print(df_EQcost_original)
#df_EQcost_original.to_excel('/Users/seungminkwak/Economics/EQcost_output.xlsx', index=False) # 엑셀 파일로 출력


CPpivot = EQ.sum_by_CP(df_EQcost_original, df_CP_List, minMeanMAX) # CP별 합산한 값 반환
#print(CPpivot)









'''
# STEP 4: Construction Cost 계산 ##############################################################################################################
'''
CPconst = CON.scaling(df_CP_List, df_scaling_power, df_country_specific,Country, moduleNumber, ElectricCapacityPerModule)
#print(CPconst)








'''
# STEP 5: CP/EQ/CON/START/END 로 표 재구성하기 ##############################################################################################################
'''
CAPEX = ESCALATION.CAPEX_w0_schedule(CPpivot, CPconst) # CAPEX 표 생성
#print(CAPEX)

df_CAPEX = ESCALATION.addSCHEDULE(CAPEX,df_schedule) # CAPEX 표에 START, END 열 추가
#print(df_CAPEX)

CAPEX = ESCALATION.CAPEX(df_CAPEX, preconstructionPeriod, constructionPeriod, plantLifetime,escalationNSSS, escalationTG, escalationBOP, escalationLabor)
#print(CAPEX)

'''
# STEP 6: Cash Flow Output ####################################################################################################################################
'''
CFS = CF.YEARS(preconstructionPeriod, constructionPeriod, plantLifetime)   #연도 생성 
CFS = CF.REVENUE(CFS, ElectricCapacityPerModule, moduleNumber, electricityPrice, salesToRevenueRatio, capacityFactor, constructionPeriod, constructionPeriod + plantLifetime)  #Revenue 행 생성 
CFS = CF.OM_ANNUAL(CFS, constructionPeriod, constructionPeriod + plantLifetime, ElectricCapacityPerModule, moduleNumber)  #OM_ANNUAL 행 생성
CFS = CF.FUEL_FRONTEND(CFS, constructionPeriod, constructionPeriod + plantLifetime, Feed, Product, Tail, totalFuelQty, U3O8Price, EnrichmentPrice, FabricationPrice, ConversionPrice,moduleNumber,BatchNumber, BatchCycleLength, CoreDesignFactor)  #FUEL_FRONTEND 행 생성
CFS = CF.FUEL_INTERIM_STORAGE(CFS, interimCOST_initial, annualCost_CASK, interimCOST_OM, constructionPeriod, constructionPeriod + plantLifetime, yearsForInterimStorage, BatchCycleLength)
CFS = CF.GROSS_PROFIT(CFS)  #GROSS_PROFIT 행 생성
CFS = CF.OM_CAPITAL(CFS, constructionPeriod, constructionPeriod + plantLifetime, ElectricCapacityPerModule, moduleNumber)  #OM_ANNUAL 행 생성
CFS = CF.CAPEX(CFS, CAPEX)  #CAPEX 행 생성
CFS = CF.CAPEX_DEBT(debtToEquityRatio, CFS) #Debt에 해당하는 CAPEX 행 생성 
CFS = CF.INTERESTnDEBTrepayment(CFS, interestRate, loanTenor, constructionPeriod) #건설중이자 + 운영중이자 + 원금상환
CFS = CF.DEPRECIATIONandAMORTIZATION(CFS, constructionPeriod, plantLifetime) # 감가상각비 처리 
CFS = CF.EBIT(CFS)
CFS = CF.EBT(CFS)
CFS = CF.TAX(CFS,taxRate)
CFS = CF.NI(CFS)
CFS = CF.CASH_FLOW(CFS)

#print(CFS)
current_directory = os.getcwd()

# output 폴더 경로
output_dir = os.path.join(current_directory, "output")
os.makedirs(output_dir, exist_ok=True)  # 폴더 없으면 생성

# 저장 경로
output_file = os.path.join(output_dir, "CFS.xlsx")

# 저장
CFS.to_excel(output_file, index=False)  # index=False는 보통 깔끔하게 저장할 때 사용








'''
# STEP 7: Analysis ####################################################################################################################################
'''
# Cash Flow Statement 출력 
ANALYSIS.CASHFLOW(CFS)
LCOE_CON, LCOE_OM, LCOE_FUEL, LCOE_FUEL_IS, LCOE_TOTAL = ANALYSIS.LCOE(CFS, discountRate, electricityPrice, salesToRevenueRatio)
ANALYSIS.IRR(CFS)
ANALYSIS.BEP(CFS)
ANALYSIS.CONSTRUCTION_COST(CFS)



# for 형탁 (평소에는 삭제)
print(f"LCOE_CON: {LCOE_CON}, LCOE_OM: {LCOE_OM}, LCOE_FUEL: {LCOE_FUEL}, LCOE_FUEL_IS: {LCOE_FUEL_IS}, LCOE_TOTAL: {LCOE_TOTAL}")




