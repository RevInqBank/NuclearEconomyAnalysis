from pathlib import Path
import pandas as pd
import numpy as np
import yaml
import matplotlib.pyplot as plt
from dataclasses import dataclass
import os
import argparse

import input.code.Reactor_Selection as RS
import input.code.readInput as read
import input.code.EQcost as EQ
import input.code.CONSTRUCTIONcost as CON
import input.code.Fuel_Cost_Input as Fuel
import input.code.Cash_Flow_Statement as CF
import input.code.Escalation as ESCALATION
import input.code.Analysis as ANALYSIS
import input.code.Scheduling as SCHEDULING


@dataclass
class ReactorConfig:
    # 0. read input from yaml or excel
    use_yaml: bool

    # 1. Reactor Selection
    reactorType: str
    powerDensity: float
    activeCoreD: float
    activeCoreDpct: float
    activeCoreH: float
    activeCoreHpct: float
    TGefficiency: float
    moduleNumber: int

    # 2. Fuel Cost
    Feed: float
    Product: float
    Tail: float
    totalFuelQty: float
    U3O8Price: int
    EnrichmentPrice: int
    FabricationPrice: int
    ConversionPrice: int
    BatchNumber: float
    BatchCycleLength: int 
    CoreDesignFactor: int

    # Interim Storage
    interimCOST_initial: int
    interimCOST_OM: float
    COSTperHM: int
    HMperASSEMBLY: float
    ASSEMBLYperCORE: int
    yearsForInterimStorage: int

    # 3. O&M Cost
    annualOMcost: float

    # 4. Operation
    plantLifetime: int
    capacityFactor: float
    electricityPrice: int
    salesToRevenueRatio: float

    # 5. Financial
    escalationNSSS: int
    escalationTG: float
    escalationBOP: float
    escalationLabor: float
    escalationInterimStorage: float
    escalationDisposal: float
    debtToEquityRatio: float
    interestRate: float
    loanTenor: int
    depreciationPeriod: int
    taxRate: float
    discountRate: float

    # 6. Cost
    minMeanMAX: str

    # 7. Scaling
    DesignSimplification_safetyPIPING: int
    DesignSimplification_safetyVALVES: int
    DesignSimplification_safetyPUMPS: int
    DesignSimplification_safetyCABLES: int
    DesignSimplification_safetyMECH: int

    # 8. Country
    Country: str

    # 9. Concrete Rate
    Rate_BASEMAT: float
    Rate_INCV: float
    Rate_CNT: float
    Licensing_Duration: float


class economic_analysis():

    def __init__(self):
        super().__init__()

        '''
        # Step 0: 변수 선언 및 초기화 ##########################################################################################################################
        '''
        # 0. 기본 변수들
        # Use Path(__file__).parent to get the directory where the script is located
        # This is more robust than os.getcwd() which depends on where you run the command from
        self.project_root = Path(__file__).resolve().parent

        '''
        # STEP 1: 엑셀 파일에서 INPUT 변수 및 값들 읽어오기 ####################################################################################################
        이건 input 파일에서 변수들을 읽어와서 전역변수로 생성하는 함수인데 그냥 init에 다 합쳐버려도 될듯. xlsx를 csv로 바꾸어서 다 해버립시다.. 
        data도 folder 잘 정리해서 하면 될 듯?
        '''
        input_yaml = self.project_root / "input" / "data" / "input.yaml"
        self.step_1_read_yaml(input_yaml)
        '''
        # STEP 2: Source 데이터 읽어오기 및 계산 (하나의 파일에서 여러 시트 읽기) #########################################################################################################₩
        '''
        source_file = self.project_root / "input" / "data" / "SOURCE_DATA.xlsx"
        self.step_2_read_source_excel(source_file)

    def step_1_read_yaml(self, yaml_file):
        """
        YAML 파일에서 변수를 읽어와
        ReactorConfig dataclass로 변환하여 self.config에 저장
        """
        with open(yaml_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Dataclass를 사용하여 검증 및 자동완성 지원
        self.config = ReactorConfig(**data)

        if not self.config.use_yaml:
            print(f"Reading input from Excel (use_yaml={self.config.use_yaml})")
            # Excel file path
            input_excel = self.project_root / "input" / "data" / "INPUT.xlsx"
            
            if input_excel.exists():
                df = pd.read_excel(input_excel, header=None)
                loaded_count = 0
                
                for i in range(len(df)):
                    var_name = df.iloc[i, 1]    # Column 2: Variable Name
                    var_value = df.iloc[i, 2]   # Column 3: Variable Value
                    
                    # Update config if the attribute exists
                    if hasattr(self.config, var_name):
                        # Enforce type based on ReactorConfig definition
                        if var_name in self.config.__annotations__:
                            target_type = self.config.__annotations__[var_name]
                            try:
                                # Handle optional or specific types if needed, but for now simple casting
                                # Special handling for boolean if 'TRUE'/'FALSE' strings are used in Excel
                                if target_type == bool and isinstance(var_value, str):
                                    var_value = var_value.lower() == 'true'
                                
                                # Cast the value
                                converted_value = target_type(var_value)
                                setattr(self.config, var_name, converted_value)
                            except (ValueError, TypeError) as e:
                                print(f"Warning: Failed to cast {var_name}='{var_value}' to {target_type}. Keeping original. Error: {e}")
                                setattr(self.config, var_name, var_value)
                        else:
                            setattr(self.config, var_name, var_value)
                            
                        loaded_count += 1
                
                print(f"Updated {loaded_count} configuration variables from {input_excel.name}")
            else:
                print(f"Warning: {input_excel} not found. Using YAML defaults.")
        else:
            print(f"Reading input from YAML (use_yaml={self.config.use_yaml})")
        # read input from excel
            # def step_1_read_input(self, excel_file):
            # """
            # Excel 파일에서 변수를 읽어와 호출한 모듈의 전역변수로 생성
            # """
            # df = pd.read_excel(excel_file, header=None)
            
            # # 호출한 모듈의 globals() 찾기
            # caller_globals = inspect.currentframe().f_back.f_globals
            
            # for i in range(len(df)):
            #     var_name = df.iloc[i, 1]    # 2열: 변수 이름
            #     var_value = df.iloc[i, 2]   # 3열: 변수 값
                
            #     # 호출한 모듈의 전역변수로 생성
            #     caller_globals[var_name] = var_value
            #     #print(f"{var_name} = {var_value}")
            
            # #print(f"총 {len(df)}개 변수가 생성되었습니다.")
            # # return 없음 - None 반환

    def step_2_read_source_excel(self, source_file):
        self.SNU = False
        if self.config.reactorType == 'SNU':
            self.df_EQcost_original = pd.read_excel(source_file, sheet_name='EQcost_SNU') # EQ Cost 원본 데이터
            self.config.reactorType = 'AP1000'
            self.SNU = True
        # for key, value in self.config.__dict__.items():
        elif self.config.reactorType == 'Nuscale':
            self.df_EQcost_original = pd.read_excel(source_file, sheet_name='EQcost_Nuscale') # EQ Cost 원본 데이터
        else:
            self.df_EQcost_original = pd.read_excel(source_file, sheet_name='EQcost') # EQ Cost 원본 데이터
        self.df_currency = pd.read_excel(source_file, sheet_name='Currency') # 환율 데이터
        self.df_dollarValue = pd.read_excel(source_file, sheet_name='dollarValue') # CPI 데이터
        self.df_CP_List = pd.read_excel(source_file, sheet_name='CP_List') # CP List 데이터
        self.df_scaling_power = pd.read_excel(source_file, sheet_name='SCALING_POWER_EXPONENT') # Scaling Power Exponent 데이터
        self.df_country_specific = pd.read_excel(source_file, sheet_name='COUNTRY_SPECIFIC') # Country Specific 데이터

        ''''# INPUT 수정 기회  ##############################################################################################################
        # '''

        # self.Product = 0.062
        # self.BatchNumber = 2.3
        # self.BatchCycleLength = 24
        # self.capacityFactor = 0.923

        ''''
        #############################################################################################################
        '''

        # Schedule 데이터 (임시!!!)
        self.df_schedule = pd.read_excel(source_file, sheet_name='SCHEDULE') # Schedule 데이터 (임시!!!)

        # print(f"df_EQcost_original: {self.df_EQcost_original}")
        # print(f"df_currency: {self.df_currency}")
        # print(f"df_dollarValue: {self.df_dollarValue}")
        # print(f"df_CP_List: {self.df_CP_List}")
        # print(f"df_scaling_power: {self.df_scaling_power}")
        # print(f"df_country_specific: {self.df_country_specific}")
        # print(f"self.df_schedule: {self.df_schedule}")
        
        # want to save as .csv
        # self.df_EQcost_original.to_csv('EQcost_original.csv', index=False)
        # self.df_currency.to_csv('currency.csv', index=False)
        # self.df_dollarValue.to_csv('dollarValue.csv', index=False)
        # self.df_CP_List.to_csv('CP_List.csv', index=False)
        # self.df_scaling_power.to_csv('SCALING_POWER_EXPONENT.csv', index=False)
        # self.df_country_specific.to_csv('COUNTRY_SPECIFIC.csv', index=False)
        # self.df_schedule.to_csv('SCHEDULE.csv', index=False)
        
        # exit()

    def step_3_calculate_eq_cost(self, ElectricCapacityPerModule):
        '''
        # STEP 3: EQ Cost 계산 ##############################################################################################################
        '''
        self.df_EQcost_original = EQ.convert_currency(self.df_EQcost_original, self.df_currency) # 환율 변환 후 우측에 4개 열 추가
        self.df_EQcost_original = EQ.adjust_dollar_value(self.df_EQcost_original, self.df_dollarValue) # 딜러가치 변환 우측에 4개 열 추가 
        self.df_EQcost_original = EQ.mergeEQcost(self.df_EQcost_original) # min / Mean / MAX 구하기
        #print(self.df_EQcost_original) 

        self.df_EQcost_original = EQ.scaling(self.config.Country, self.df_EQcost_original, self.df_scaling_power, self.df_country_specific, ElectricCapacityPerModule, self.config.moduleNumber, 
                        self.config.DesignSimplification_safetyPIPING, self.config.DesignSimplification_safetyVALVES, 
                        self.config.DesignSimplification_safetyPUMPS, self.config.DesignSimplification_safetyCABLES, 
                        self.config.DesignSimplification_safetyMECH) # min / Mean / MAX 구하기
        return self.df_EQcost_original
        #print(self.self.df_EQcost_original) 
        #self.self.df_EQcost_original.to_excel('/Users/seungminkwak/Economics/EQcost_output.xlsx', index=False) # 엑셀 파일로 출력

    def step_5_calculate_capex(self, CPpivot, CPconst):
        '''
        # STEP 5: CP/EQ/CON/START/END 로 표 재구성하기 ##############################################################################################################
        '''
        CAPEX = ESCALATION.CAPEX_w0_schedule(CPpivot, CPconst) # CAPEX 표 생성
        #print(CAPEX)

        df_CAPEX = ESCALATION.addSCHEDULE(CAPEX,self.df_schedule) # CAPEX 표에 START, END 열 추가
        #print(df_CAPEX)

        df_CAPEX = ESCALATION.CAPEX(df_CAPEX, self.preconstructionPeriod, self.constructionPeriod, self.config.plantLifetime,self.config.escalationNSSS, self.config.escalationTG, self.config.escalationBOP, self.config.escalationLabor)
        #print(df_CAPEX)

        return df_CAPEX    

    def step_6_calculate_cash_flow(self, df_CAPEX, ElectricCapacityPerModule, annualCost_CASK):
        '''
        # STEP 6: Cash Flow Output ####################################################################################################################################
        '''
        CFS = CF.YEARS(self.preconstructionPeriod, self.constructionPeriod, self.config.plantLifetime)   #연도 생성 
        CFS = CF.REVENUE(CFS, ElectricCapacityPerModule, self.config.moduleNumber, self.config.electricityPrice, self.config.salesToRevenueRatio, self.config.capacityFactor, self.constructionPeriod, self.constructionPeriod + self.config.plantLifetime)  #Revenue 행 생성 
        CFS = CF.OM_ANNUAL(self.SNU, CFS, self.constructionPeriod, self.constructionPeriod + self.config.plantLifetime, ElectricCapacityPerModule, self.config.moduleNumber)  #OM_ANNUAL 행 생성
        CFS, self.ratio = CF.FUEL_FRONTEND(CFS, self.constructionPeriod, self.constructionPeriod + self.config.plantLifetime, self.config.Feed, self.config.Product, self.config.Tail, self.config.totalFuelQty, self.config.U3O8Price, self.config.EnrichmentPrice, self.config.FabricationPrice, self.config.ConversionPrice,self.config.moduleNumber,self.config.BatchNumber, self.config.BatchCycleLength, self.config.CoreDesignFactor)  #FUEL_FRONTEND 행 생성
        CFS = CF.FUEL_INTERIM_STORAGE(CFS, self.config.interimCOST_initial, annualCost_CASK, self.config.interimCOST_OM, self.constructionPeriod, self.constructionPeriod + self.config.plantLifetime, self.config.yearsForInterimStorage, self.config.BatchCycleLength)
        CFS = CF.GROSS_PROFIT(CFS)  #GROSS_PROFIT 행 생성
        CFS = CF.OM_CAPITAL(CFS, self.constructionPeriod, self.constructionPeriod + self.config.plantLifetime, ElectricCapacityPerModule, self.config.moduleNumber)  #OM_ANNUAL 행 생성
        CFS = CF.CAPEX(CFS, df_CAPEX)  #CAPEX 행 생성
        CFS = CF.CAPEX_DEBT(self.config.debtToEquityRatio, CFS) #Debt에 해당하는 CAPEX 행 생성 
        CFS = CF.INTERESTnDEBTrepayment(CFS, self.config.interestRate, self.config.loanTenor, self.constructionPeriod) #건설중이자 + 운영중이자 + 원금상환
        CFS = CF.DEPRECIATIONandAMORTIZATION(CFS, self.constructionPeriod, self.config.plantLifetime) # 감가상각비 처리 
        CFS = CF.EBIT(CFS)
        CFS = CF.EBT(CFS)
        CFS = CF.TAX(CFS,self.config.taxRate)
        CFS = CF.NI(CFS)
        CFS = CF.CASH_FLOW(CFS)

        # output 폴더 경로
        output_dir = self.project_root / "output"
        output_dir.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 생성 (pathlib way)

        # 저장 경로
        output_file = output_dir / "CFS.xlsx"

        # 저장
        CFS.to_excel(output_file, index=False)  # index=False는 보통 깔끔하게 저장할 때 사용 

        return CFS
    
    def step_7_analysis(self, CFS, ThermalCapacityPerModule):
        '''
        # STEP 7: Analysis ####################################################################################################################################
        '''
        # Cash Flow Statement 출력 
        ANALYSIS.CASHFLOW(CFS)
        LCOE_CON, LCOE_OM, LCOE_FUEL, LCOE_FUEL_IS, LCOE_TOTAL = ANALYSIS.LCOE(CFS, self.config.discountRate, self.config.electricityPrice, self.config.salesToRevenueRatio)
        ANALYSIS.IRR(CFS)
        ANALYSIS.BEP(CFS)
        ANALYSIS.CONSTRUCTION_COST(CFS)

        # for 형탁 (평소에는 삭제)
        print("--------------------------------")
        # print(f"LCOE_CON: {LCOE_CON:.2f}, LCOE_OM: {LCOE_OM:.2f}, LCOE_FUEL: {LCOE_FUEL:.2f}, LCOE_FUEL_IS: {LCOE_FUEL_IS:.2f}, LCOE_TOTAL: {LCOE_TOTAL:.2f}")
        print(f"LCOE_TOTAL: {LCOE_TOTAL}") # LCOE total
        print(f"LCOE_CON: {LCOE_CON}") # LCOE construction
        print(f"LCOE_OM: {LCOE_OM}") # LCOE operation and maintenance
        print(f"LCOE_FUEL: {LCOE_FUEL + LCOE_FUEL_IS}") # LCOE fuel
        print("--------------------------------")
        print(f"LCOE_U3O8: {LCOE_FUEL*self.ratio['U3O8']}") # LCOE natural uranium
        print(f"LCOE_Conversion: {LCOE_FUEL*self.ratio['Conversion']}") # LCOE conversion
        print(f"LCOE_Enrichment: {LCOE_FUEL*self.ratio['Enrichment']}") # LCOE enrichment
        print(f"LCOE_Fabrication: {LCOE_FUEL*self.ratio['Fabrication']}") # LCOE fabrication
        print(f"LCOE_FUEL_IS: {LCOE_FUEL_IS}") # LCOE fuel interim storage
        print("--------------------------------")
        EFPD = self.config.capacityFactor * self.config.BatchCycleLength * 30
        BU_cycle = EFPD* ThermalCapacityPerModule / self.config.totalFuelQty
        Discharged_BU = BU_cycle * self.config.BatchNumber
        print(f"Average EFPD: {EFPD} [days]")
        print(f"Average Discharged_BU: {Discharged_BU/1000} [MWd/kgU]") # Discharged BU
        print(f"  Thermal Capacity: {ThermalCapacityPerModule} [MWth]")
        print(f"  total fuel Qty: {self.config.totalFuelQty} [tU]")
        print(f"  Batch Number: {self.config.BatchNumber}")
        print(f"  Batch Cycle Length: {self.config.BatchCycleLength} [months]")
        return

    def run(self): 
        # step 1,2 Initialize the input data
        # self.init()  
        
        # Initialize SNU flag
        self.SNU = False
        
        # Special handling for SNU reloading triggered by args
        if self.config.reactorType == 'SNU':
            self.SNU = True
            source_file = self.project_root / "input" / "data" / "SOURCE_DATA.xlsx"
            self.df_EQcost_original = pd.read_excel(source_file, sheet_name='EQcost_SNU')
            
        # wanna print config, row by row
        for key, value in self.config.__dict__.items():
            print(f"{key}: {value}")

        """------------------------------------------------------------------------------------------"""
        """------------------------------------------------------------------------------------------"""
        # Base MWe mapping
        base_mwe_map = {
            "APR1400": 1400,
            "AP1000": 1027,
            "SMART": 109.5,
            "NuScale": 876,
            "SNU": 100,
            # "NuScale": 77 # Check if user meant 222 total (which is often 77*modules?) User said 222.
            # >> Nuscale: 73*12=876
        }
        
        base_mwe = base_mwe_map.get(self.config.reactorType, 1400) # Default to 1400 if unknown

        if hasattr(self, 'target_mwe') and self.target_mwe is not None:
             self.config.powerDensity = self.config.powerDensity * (self.target_mwe / base_mwe)
        else:
             # Default fallback if no argument is passed (original logic was 100/1400, preserving user's manual change for now if they run without args? 
             # Actually user's code had 100/1400 hardcoded. I will make sure we respect that if no arg is passed, OR maybe just default to 100/1400 if that was their intent.
             # But likely they want to preserve original behavior if run normally. 
             # The user's code at line 337 was: self.config.powerDensity = self.config.powerDensity * (100/1400)
             # I will keep that as the "else" but usually it's better to NOT scale if not asked?
             # User said "그럼 내가 태깅한 코드는 APR1400에 대해서 100으로 스케일링한 것을 알겠지?" implies they were manually testing 100.
             # I will use the manual hardcode just as a fallback or remove it if I am sure.
             # Safest is to use the arg if present.
             self.config.powerDensity = self.config.powerDensity
        
        print(f"BaseMWe: {base_mwe}")
        print(f"ModifiedPowerDensity: {self.config.powerDensity}")
        print("--------------------------------")
        """------------------------------------------------------------------------------------------"""
        """------------------------------------------------------------------------------------------"""
        

        current_directory = os.getcwd()
        source_file =  os.path.join(current_directory, "input", "data", "SOURCE_DATA.xlsx")
        
        # SNU uses AP1000 scheduling sheet
        sched_sheet = self.config.reactorType
        if sched_sheet == 'SNU':
            sched_sheet = 'AP1000'
            
        df_scheduling = pd.read_excel(source_file, sheet_name = sched_sheet) # EQ Cost 원본 데이터
        df_result, critical_path_duration = SCHEDULING.Rate(df_scheduling, self.config.Rate_BASEMAT, self.config.Rate_INCV, self.config.Rate_CNT)
        self.constructionPeriod = max(critical_path_duration,10.45)  # years
        self.preconstructionPeriod = 2  # years
        #print(f"Construction Period: {self.constructionPeriod} years")
        
        # step 2-2. Reactor Selection Output: 사실상 ElectricalCapacityPerModule 뽑는 용도
        (ThermalCapacityPerModule, ElectricCapacityPerModule, 
        TotalCapacity, CoreH, CoreD, RPVvolume) = RS.Core(self.config.powerDensity, self.config.activeCoreD, self.config.activeCoreH, self.config.activeCoreDpct, 
            self.config.activeCoreHpct, self.config.TGefficiency, self.config.moduleNumber)

        # step 3-1. Fuel Interim Storage 계산
        annualCost_CASK = Fuel.InterimStorage(self.config.COSTperHM, self.config.HMperASSEMBLY,self.config.BatchNumber, 
            self.config.BatchCycleLength, self.config.ASSEMBLYperCORE, self.config.moduleNumber)
        # print(f"annualCost_CASK: {annualCost_CASK}")

        # step 3-2. eq cost 계산
        self.df_EQcost_original = self.step_3_calculate_eq_cost(ElectricCapacityPerModule) # self.self.df_EQcost_original 생성
        CPpivot = EQ.sum_by_CP(self.df_EQcost_original, self.df_CP_List, self.config.minMeanMAX) # CP별 합산한 값 반환
        print(CPpivot)
        print("--------------------------------")
        print(f"ElectricCapacityPerModule: {ElectricCapacityPerModule}")
        print(f"ThermalCapacityPerModule: {ThermalCapacityPerModule}")
        print("--------------------------------")
        # Save intermediate results to output directory
        # output_dir = self.project_root / "output"
        # output_dir.mkdir(parents=True, exist_ok=True)
        
        # self.df_EQcost_original.to_csv(output_dir / "df_EQcost_original.csv", index=False)
        # CPpivot.to_csv(output_dir / "CPpivot.csv", index=False)
        # exit()

        # 4. construction cost 계산
        CPconst = CON.scaling(self.df_CP_List, self.df_scaling_power, self.df_country_specific,self.config.Country, self.config.moduleNumber, ElectricCapacityPerModule)
        # CPconst.to_csv(output_dir / "CPconst.csv", index=False)
        # exit()

        # 5. CAPEX 계산
        df_CAPEX = self.step_5_calculate_capex(CPpivot, CPconst) # CAPEX 생성
        #print(df_CAPEX)
        #df_CAPEX.to_csv(output_dir / "df_CAPEX.csv", index=False)
        # exit()

        # 6. Cash Flow Statement 계산
        CFS = self.step_6_calculate_cash_flow(df_CAPEX, ElectricCapacityPerModule, annualCost_CASK) # CFS 생성
        # CFS.to_csv(output_dir / "CFS.csv", index=False)
        # exit()

        # 7. Analysis and save CFS
        self.step_7_analysis(CFS, ThermalCapacityPerModule)

        return


if __name__ == "__main__":
    # parser = transformers.HfArgumentParser((ModelArguments, DataArguments, TrainingArguments))
    # model_args, data_args, training_args = parser.parse_args_into_dataclasses()
    # train(model_args, data_args, training_args)
    parser = argparse.ArgumentParser(description='Economic Analysis for Nuclear Reactors')
    parser.add_argument('--reactor', type=str, help='Reactor type (APR1400, AP1000, NuScale, SMART)')
    parser.add_argument('--target_mwe', type=float, help='Target MWe')
    args = parser.parse_args()
    
    analysis = economic_analysis()
    if args.reactor:
        analysis.config.reactorType = args.reactor
        # Reload specific yaml for the reactor if needed or rely on base logic if it just overrides input.yaml
        # However, input.yaml is loaded in init. We might need to reload or just set the attribute.
        # But wait, step_1_read_yaml loads input.yaml. 
        # Ideally we should load the specific yaml for that reactor if the user wants to switch context completely.
        # But the user said "yaml 파일은 AP1000,APR1400,SMART,NuScale 있는거 보일 거야."
        # So we should probably load the corresponding yaml file.
        
        project_root = Path(__file__).resolve().parent
        reactor_yaml = project_root / "input" / "data" / f"{args.reactor}.yaml"
        if reactor_yaml.exists():
            analysis.step_1_read_yaml(reactor_yaml)
        else:
             print(f"Warning: Specific yaml for {args.reactor} not found. Using default input.yaml but overriding reactorType name.")

    if args.target_mwe:
        analysis.target_mwe = args.target_mwe
    else:
        analysis.target_mwe = None # Default behavior

    analysis.run()


# /mnt/ssd0/Donguk_data/miniconda3/envs/econ/bin/python main_for_loop.py --reactor APR1400 --target_mwe 1400
