import math
import numpy as np


def FrontEnd(Feed, Product, Tail, totalFuelQty, U3O8Price, EnrichmentPrice, FabricationPrice, ConversionPrice,moduleNumber,BatchNumber, BatchCycleLength, CoreDesignFactor):

    # 여기에 계산 로직 작성
    FeedVF = (2*Feed-1)*math.log(Feed/(1-Feed))
    ProductVF = (2*Product-1)*math.log(Product/(1-Product))
    TailVF = (2*Tail-1)*math.log(Tail/(1-Tail))
    FtoP = (Product-Tail)/(Feed-Tail)
    #TtoP = (Product-Feed)/(Feed-Tail)
    SWUtoP = (ProductVF-TailVF) - FtoP*(FeedVF-TailVF)
    U238 = 238.051
    U235 = 235.044
    O16 = 15.999
    U3O8toF = (Feed*U235 + (1-Feed)*U238)/((Feed*U235 + (1-Feed)*U238)+O16*8/3)

    tUFAB = totalFuelQty*moduleNumber/BatchNumber*(12/BatchCycleLength)*CoreDesignFactor
    tSWU = SWUtoP * tUFAB
    tUCNV = FtoP * tUFAB
    tU3O8 = tUCNV / U3O8toF

    AnnualFuelCost = tU3O8*U3O8Price + tSWU*EnrichmentPrice + tUCNV*ConversionPrice + tUFAB*FabricationPrice
    # (1) Natural Uranium Cost: tU3O8*U3O8Price
    # (2) Conversion Cost: tSWU*ConversionPrice
    # (3) Enrichment Cost: tUCNV*EnrichmentPrice
    # (4) Fabrication Cost: tUFAB*FabricationPrice

    return AnnualFuelCost/1000  # in million USD


def InterimStorage(COSTperHM, HMperASSEMBLY,BatchNumber, BatchCycleLength, ASSEMBLYperCORE, moduleNumber):

    annualASSEMBLY = ASSEMBLYperCORE/BatchNumber*(12/BatchCycleLength) #Assembly per Core 같은 경우 APR1400 = 241 기준
    annualHM = HMperASSEMBLY * annualASSEMBLY #ton
    annualCost_CASK = COSTperHM * annualHM *1000 * moduleNumber /1000000 #2개 호기 Million USD
    return annualCost_CASK

#def Disposal():
#    pass

#print(FrontEnd(0.00711, 0.045, 0.0025, 57.2, 135, 97, 350, 12))


