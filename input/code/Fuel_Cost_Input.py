import math
import numpy as np


def FrontEnd(x_Feed, x_Product, x_Tail, totalFuelQty, U3O8Price, EnrichmentPrice, FabricationPrice, ConversionPrice,moduleNumber,BatchNumber, BatchCycleLength, CoreDesignFactor):

    # 여기에 계산 로직 작성
    # totalFuelQty: Initial Core Inventory [tU/(module*one fuel charging)]

    # (4) Fabrication Cost: tUFAB*FabricationPrice
    tUFAB = totalFuelQty*moduleNumber*(12/(BatchNumber*BatchCycleLength))*CoreDesignFactor
    FabricationCost = tUFAB*FabricationPrice
    # (3) Enrichment Cost: tSWU*EnrichmentPrice
    V_Feed = (2*x_Feed-1)*math.log(x_Feed/(1-x_Feed))
    V_Product = (2*x_Product-1)*math.log(x_Product/(1-x_Product))
    V_Tail = (2*x_Tail-1)*math.log(x_Tail/(1-x_Tail))
    FtoP = (x_Product-x_Tail)/(x_Feed-x_Tail)
    #TtoP = (x_Product-x_Feed)/(x_Feed-x_Tail)
    SWUtoP = (V_Product-V_Tail) - FtoP*(V_Feed-V_Tail) # [SWU/tU]

    tSWU = SWUtoP * tUFAB
    EnrichmentCost = tSWU*EnrichmentPrice
    # (2) Conversion Cost: tUCNV*ConversionPrice
    tUCNV = FtoP * tUFAB
    ConversionCost = tUCNV*ConversionPrice
    # (1) Natural Uranium Cost: tU3O8*U3O8Price
    U238 = 238.051
    U235 = 235.044
    O16 = 15.999
    U3O8toF = (x_Feed*U235 + (1-x_Feed)*U238)/((x_Feed*U235 + (1-x_Feed)*U238)+O16*8/3)

    tU3O8 = tUCNV / U3O8toF
    NaturalUraniumCost = tU3O8*U3O8Price

    print("-----------")
    print(f"tU3O8: {tU3O8}")
    print(f"tUCNV: {tUCNV}")
    print(f"tSWU: {tSWU}")
    print(f"tUFAB: {tUFAB}")
    print("-----------")

    AnnualFuelCost = NaturalUraniumCost + ConversionCost + EnrichmentCost + FabricationCost
    ratio = {"U3O8": NaturalUraniumCost/AnnualFuelCost, "Conversion": ConversionCost/AnnualFuelCost, "Enrichment": EnrichmentCost/AnnualFuelCost, "Fabrication": FabricationCost/AnnualFuelCost}
    # (1) Natural Uranium Cost: tU3O8*U3O8Price
    # (2) Conversion Cost: tUCNV*ConversionPrice
    # (3) Enrichment Cost: tSWU*EnrichmentPrice
    # (4) Fabrication Cost: tUFAB*FabricationPrice

    return AnnualFuelCost/1000, ratio  # in million USD


def InterimStorage(COSTperHM, HMperASSEMBLY,BatchNumber, BatchCycleLength, ASSEMBLYperCORE, moduleNumber):

    annualASSEMBLY = ASSEMBLYperCORE/BatchNumber*(12/BatchCycleLength) #Assembly per Core 같은 경우 APR1400 = 241 기준
    annualHM = HMperASSEMBLY * annualASSEMBLY #ton
    annualCost_CASK = COSTperHM * annualHM *1000 * moduleNumber /1000000 #2개 호기 Million USD
    return annualCost_CASK

#def Disposal():
#    pass

#print(FrontEnd(0.00711, 0.045, 0.0025, 57.2, 135, 97, 350, 12))


