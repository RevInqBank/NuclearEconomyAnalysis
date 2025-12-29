import math

def Core(powerDensity, activeCoreD, activeCoreH, activeCoreDpct, activeCoreHpct, TGefficiency, moduleNumber):
    """"
    7개의 변수를 입력받아 3개의 값을 반환하는 함수
    """
    # 여기에 계산 로직 작성
    ThermalCapacityPerModule = powerDensity*activeCoreH*activeCoreD**2*math.pi/4  
    ElectricCapacityPerModule = ThermalCapacityPerModule*TGefficiency  
    TotalCapacity = ElectricCapacityPerModule*moduleNumber
    CoreH = activeCoreH/activeCoreHpct
    CoreD = activeCoreD/activeCoreDpct
    RPVvolume = activeCoreH*math.pi/4*activeCoreD**2/(activeCoreDpct*activeCoreHpct)
    
    return ThermalCapacityPerModule, ElectricCapacityPerModule, TotalCapacity, CoreH, CoreD, RPVvolume
