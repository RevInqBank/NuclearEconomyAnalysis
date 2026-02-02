# NuEcon Code Manual

## Abstract
This document serves as the user manual and technical reference for the **NuEcon Code** (Version 1.0), a Python-based economic analysis tool designed for nuclear power reactor concepts. The code employs a top-down cost modeling approach to estimate the Levelized Cost of Electricity (LCOE), Total Capital Investment Cost (TCIC), and detailed cash flow metrics. It allows for sensitivity analysis and parameter sweeps across various reactor types (e.g., APR1400, AP1000, NuScale, SMART, SNU) by scaling reference cost data.

## Executive Summary
The NuEcon Code provides a flexible framework for evaluating the economic viability of nuclear power plants. It integrates modules for equipment cost scaling, construction schedule simulation, fuel cycle cost analysis, and financial modeling. The tool calculates LCOE by aggregating capital, O&M, and fuel cycle costs (including interim storage) over the plant's lifetime. Key outputs include a comprehensive Cash Flow Statement (CFS) and summary metrics (LCOE, IRR). The code is structured to facilitate rapid comparative analysis and sensitivity studies through YAML-based configuration and batch execution capabilities.

## Acronyms and Abbreviations
-   **LCOE**: Levelized Cost of Electricity
-   **TCIC**: Total Capital Investment Cost
-   **NOAK**: Nth-of-a-Kind
-   **FOAK**: First-of-a-Kind
-   **O&M**: Operations and Maintenance
-   **CAPEX**: Capital Expenditure
-   **IDC**: Interest During Construction
-   **CFS**: Cash Flow Statement
-   **SWU**: Separative Work Unit (Enrichment)
-   **U3O8**: Triuranium Octoxide (Yellowcake)
-   **LWR**: Light Water Reactor
-   **SMR**: Small Modular Reactor
-   **CPM**: Critical Path Method

---

# 1. Introduction

## 1.1. Objective of the NuEcon Code
The primary objective of the NuEcon Code is to provide an automated, transparent, and scalable platform for the economic assessment of nuclear reactor designs. It aims to:
-   Estimate overnight capital costs using top-down scaling laws derived from mature reference reactors.
-   Calculate determining economic indicators such as LCOE, IRR, and Break-even Price (BEP).
-   Analyze the impact of design parameters (e.g., power density, core size) and financial parameters (e.g., discount rate, construction duration) on economic performance.

## 1.2. Assumptions and Limitations
-   **Top-down Scaling**: The cost model relies on scaling laws derived from reference reactors (e.g., APR1400, AP1000). Accuracy depends on the applicability of these scaling exponents ($n$) to the target design.
-   **Reference Data**: The quality of output is contingent on accurate reference cost data provided in `SOURCE_DATA.xlsx`.
-   **Market Conditions**: Escalation rates and fuel prices are treated as constant or deterministically escalated defined inputs. Stochastic market volatility is not modeled.
-   **Schedule Estimation**: Construction duration is estimated based on concrete volume and installation rates, assuming a critical path logic (CPM).

---

# 2. Modeling Framework

## 2.1. Overall Approach (Top-down Cost Modeling)
NuEcon utilizes a top-down approach where costs for a target reactor are derived from a known reference reactor's costs. This methodology assumes that component costs follow power-law relationships with respect to key capacity or size parameters. This allows for estimating costs of conceptual designs without requiring a detailed Bill of Materials (BOM).

## 2.2. Model Architecture and Workflow
The code execution follows a sequential workflow:
1.  **Initialization**: Define target reactor parameters (Power, Dimensions, Fuel Cycle).
2.  **Cost Scaling**: Calculate Equipment (EQ) and Construction (CON) costs using scaling factors.
3.  **Schedule Simulation**: Determine construction duration using Critical Path Method (CPM) based on concrete volumes.
4.  **Financial Modeling**: Generate a year-by-year Cash Flow Statement (CFS) integrating revenues, costs, taxes, and debt service.
5.  **Economic Metric Calculation**: Compute LCOE, IRR, and BEP from the CFS.

## 2.3. Capital Cost Model
Capital costs are categorized into Equipment Costs and Construction (Labor/Material) Costs.

### Governing Equations
The scaling equation for a specific cost account $i$ is defined as:

$$Cost_{scaled,i} = Cost_{ref,i} \times \left( \frac{C_{target}}{C_{ref}} \right)^n \times K_{module} \times K_{design} \times K_{country}$$

Where:
-   $Cost_{ref,i}$: Cost of account $i$ for the reference reactor (e.g., APR1400).
-   $C_{target}, C_{ref}$: Capacity parameter (Thermal Power or Electric Power).
-   $n$: Scaling exponent specific to the equipment type (e.g., 0.6 for tanks, 1.0 for I&C).
-   $K_{module}$: Module number factor. For a reference of 2 modules: $K_{module} = N_{module} / 2$.
-   $K_{design}$: Design simplification factor (e.g., elimination of piping loops).
-   $K_{country}$: Localization factor accounting for labor rates and productivity in the target country.

### Procedure
1.  **Currency Conversion**: Convert all reference costs to a common base year and currency (e.g., 2025 USD) using Exchange Rates and CPI indices.
2.  **Scaling Application**: Apply the scaling equation to each line item in the reference cost database (`EQcost`).
3.  **Aggregation**: Sum scaled costs to obtain Total Overnight Capital Cost (OCC).

## 2.4. Operations & Maintenance (O&M) Cost Model
O&M costs are modeled as annual recurring expenses.
$$Cost_{O\&M, total} = Cost_{Fixed} + Cost_{Variable}$$
The code allows for direct input of `annualOMcost` or scaling based on staffing and output levels.

## 2.5. Fuel Cycle Cost Model
The fuel cycle cost model calculates the front-end direct costs based on mass balance equations.

### Governing Equations (Mass Balance)
1.  **Value Function**: $V(x) = (2x-1)\ln\left(\frac{x}{1-x}\right)$
2.  **Feed-to-Product Ratio**: $F/P = \frac{x_P - x_T}{x_F - x_T}$
3.  **SWU-to-Product Ratio**: $S/P = V(x_P) - V(x_T) - (F/P)(V(x_F) - V(x_T))$

Where $x_F, x_P, x_T$ are the assays for Feed, Product, and Tails, respectively.

### Cost Calculation
$$Cost_{Fuel} = M_{U3O8} P_{U3O8} + M_{Conv} P_{Conv} + M_{SWU} P_{SWU} + M_{Fab} P_{Fab}$$
Where $M$ denotes mass and $P$ denotes price.

## 2.6. Interim Storage / Spent Fuel Management Cost Model
Back-end costs for on-site dry cask storage are calculated based on the discharge rate.
$$Cost_{IS} = \frac{N_{Assembly/Core} \times M_{HM/Assembly}}{N_{Batch}} \times Cost_{UnitHM} \times N_{Module}$$

## 2.7. LCOE / IRR Formulation
### Levelized Cost of Electricity (LCOE)
LCOE is the price of electricity required for the project to break even over its lifetime, discounted to the present value.

$$LCOE = \frac{\sum_{t=0}^{Lifetime} \frac{\text{Capital}_t + \text{O\&M}_t + \text{Fuel}_t + \text{Decomm}_t}{(1+r)^t}}{\sum_{t=0}^{Lifetime} \frac{\text{Electricity}_t}{(1+r)^t}}$$

Where $r$ is the discount rate.

### Internal Rate of Return (IRR)
IRR is the discount rate $r^*$ that results in a Net Present Value (NPV) of zero:
$$NPV = \sum_{t=0}^{Lifetime} \frac{CF_t}{(1+r^*)^t} = 0$$

---

# 3. Code Description

## 3.1. Code Structure

The following flowchart illustrates the data flow and module interaction within the NuEcon code:

```text
[Start]
   |
   +--> [Input Processing]
   |       |-- Read input.yaml
   |       |-- Read SOURCE_DATA.xlsx
   |
   +--> [Reactor Characterization]
   |
   +--> {Cost Scaling}
   |       |-- EQcost.py: Scale Equipment
   |       |-- CONSTRUCTIONcost.py: Scale Labor/Mat
   |       |-- Scheduling.py: Calculate Duration
   |
   +--> (Financial Integration)
   |       |-- Make CAPEX Schedule
   |       |-- Fuel_Cost_Input.py: Calculate Fuel Cycle
   |
   +--> [Cash_Flow_Statement.py]
   |       |-- Generate Annual Cash Flows
   |       |-- Calculate Tax, Debt, Depreciation
   |
   +--> (Analysis)
   |       |-- Analysis.py: Calculate LCOE, IRR, BEP
   |
   +--> [Output Results]
           |-- Console Output
           |-- CFS.xlsx
```

### Module Descriptions
-   **`main.py`**: The central controller. Initializes the `ReactorConfig` and `economic_analysis` class, sequentially calls step functions.
-   **`input/code/EQcost.py`**: Handles currency conversion (`convert_currency`), inflation adjustment (`adjust_dollar_value`), and applies power-law scaling (`scaling`) to equipment costs.
-   **`input/code/CONSTRUCTIONcost.py`**: Scales construction material and labor costs based on reactor power and country-specific labor factors.
-   **`input/code/Fuel_Cost_Input.py`**: Implements the `FrontEnd` and `InterimStorage` functions to calculate annual fuel cycle costs based on enrichment assays and uranium prices.
-   **`input/code/Scheduling.py`**: Determines the construction duration. It calculates task durations from concrete volumes and installation rates, then builds a dependency graph (NetworkX) to find the Critical Path.
-   **`input/code/Cash_Flow_Statement.py`**: Generates the financial statements. It maps costs to years, calculates debt service (`INTERESTnDEBTrepayment`), tax (`TAX`), and net income (`NI`).
-   **`input/code/Analysis.py`**: computes final metrics (`LCOE`, `IRR`, `BEP`) from the Cash Flow Statement dataframe and formats the Excel output.

## 3.2. Code Installation and Execution
(See Section 3.2 in previous version - Retained)

## 3.3. Inputs and Outputs

### 3.3.1. Inputs (`input.yaml` & `SOURCE_DATA.xlsx`)

#### Reactor Configuration (`input.yaml`)
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `reactorType` | String | Reference reactor model (e.g., 'APR1400', 'SNU'). |
| `powerDensity` | Float | Core power density [W/cc]. |
| `activeCoreD/H` | Float | Core dimensions [m]. |
| `moduleNumber` | Int | Number of units per site. |
| `DesignSimplification` | Float | Multipliers (0.0-1.0) for safety systems (Piping, Valves, etc.). |

#### Economic Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `discountRate` | Float | Real discount rate for LCOE. |
| `interestRate` | Float | Interest rate on debt. |
| `debtToEquityRatio` | Float | Project financing structure. |
| `taxRate` | Float | Corporate tax rate. |
| `U3O8Price` | Int | Uranium spot price [$/kg]. |
| `EnrichmentPrice` | Int | SWU cost [$/SWU]. |

### 3.3.2. Outputs

#### 1. Cash Flow Statement (`output/CFS.xlsx`)
A detailed Excel sheet containing year-by-year financial data:
-   **REVENUE**: Electricity sales income.
-   **CAPEX**: Yearly capital expenditure.
-   **O&M**: Operations and maintenance outlay.
-   **FUEL**: Front-end and back-end fuel costs.
-   **DEBT/EQUITY**: Funding inflows.
-   **INTEREST/PRINCIPAL**: Debt service outflows.
-   **NET INCOME**: Post-tax profit.
-   **CASH FLOW**: Free cash flow for NPV/IRR.

#### 2. Analysis Results
-   **LCOE Breakdown**:
    -   `LCOE_CON`: Construction component.
    -   `LCOE_OM`: O&M component.
    -   `LCOE_FUEL`: Fuel component.
    -   `LCOE_TOTAL`: Total LCOE [$/MWh].
-   **IRR**: Internal Rate of Return [%].
-   **BEP**: Break-even year.
-   **Construction Cost**: Total overnight cost + IDC [$M].

---

# 4. References
1.  OECD/NEA, "Projected Costs of Generating Electricity," 2020 Edition.
2.  IAEA, "Economic Evaluation of Alternative Nuclear Energy Systems," TECDOC-1837.
3.  Evaluation of Nuclear Power Plant Costs, *G4ECONS* guidelines.

---

# Appendix A – Input Instructions for the NuEcon-1.0 Code

The input file `input.yaml` is the primary configuration file. All parameters below can be modified to customize the analysis.

# Appendix A – Input Instructions for the NuEcon-1.0 Code

The input file `input.yaml` is the primary configuration file. Users can modify parameters to simulate different reactor designs and economic scenarios.

### 1. Reactor Selection
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `reactorType` | "SNU" | - | Reference reactor model to use for base costs. Options: `APR1400`, `AP1000`, `NuScale`, `SMART`, `SNU`. Affects which sheet is read from `SOURCE_DATA.xlsx`. |
| `powerDensity` | 100.5 | W/cc | Core volumetric power density. Used to calculate active core volume if dimensions are not fixed. |
| `activeCoreD` | 3.647 | m | Active core diameter. Used for vessel sizing scaling. |
| `activeCoreDpct` | 0.788 | - | Ratio of active core diameter to Reactor Pressure Vessel (RPV) inner diameter. |
| `activeCoreH` | 3.81 | m | Active core height. Used for vessel sizing scaling. |
| `activeCoreHpct` | 0.261 | - | Ratio of active core height to RPV height. |
| `TGefficiency` | 0.35 | - | Thermal efficiency of the turbine-generator cycle. Converts Thermal Power ($MW_{th}$) to Electric Power ($MW_e$). |
| `moduleNumber` | 2 | ea | Number of reactor modules deployed at a single site. Affects shared cost savings (Nth-of-a-kind effects). |

### 2. Fuel Cost
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `Feed` | 0.00711 | - | Natural Uranium feed assay (weight fraction, e.g., 0.711%). |
| `Product` | 0.045 | - | Target enrichment level of fuel product (e.g., 4.5%). Higher enrichment increases SWU requirements. |
| `Tail` | 0.0022 | - | Tails assay from enrichment process (e.g., 0.22%). |
| `totalFuelQty` | 103.82 | tU | Total mass of uranium in the reactor core (Heavy Metal). |
| `U3O8Price` | 135 | $/kg | Spot market price for Uranium Ore Concentrate ($U_3O_8$). |
| `EnrichmentPrice` | 97 | $/SWU | Cost per Separative Work Unit for enrichment. |
| `FabricationPrice` | 350 | $/tU | Cost to fabricate fuel assemblies from enriched $UF_6$. |
| `ConversionPrice` | 12 | $/tU | Cost to convert $U_3O_8$ to $UF_6$ for enrichment. |
| `BatchNumber` | 2.5 | - | Number of fuel batches in the core. Inverse of the replacement fraction (e.g., 3 = 1/3 core replaced/cycle). |
| `BatchCycleLength` | 18 | months | Duration of nuclear fuel cycle between refuelling outages. |
| `CoreDesignFactor` | 1 | - | Multiplier for fuel quantity to account for specific design margins (default: 1). |

### 3. Interim Storage
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `interimCOST_initial` | 9 | $M | Initial fixed capital investment for the Independent Spent Fuel Storage Installation (ISFSI). |
| `interimCOST_OM` | 0.75 | $M/yr | Annual O&M cost for maintaining the ISFSI. |
| `COSTperHM` | 70 | $/kgHM | Variable cost for dry cask storage per kg of Heavy Metal stored. |
| `HMperASSEMBLY` | 0.45 | t | Mass of Heavy Metal per single fuel assembly. |
| `ASSEMBLYperCORE` | 241 | ea | Total number of fuel assemblies in the reactor core. |
| `yearsForInterimStorage` | 5 | years | Duration spent fuel remains in on-site dry storage after plant decommission. |

### 4. O&M Cost
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `annualOMcost` | 50.0 | $M/yr | Total annual Operations & Maintenance cost (Staffing, specialized maintenance, fees). Input as a fixed value or scaled. |

### 5. Operation
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `plantLifetime` | 60 | years | Operational design lifetime of the power plant. Used for depreciation and LCOE amortization period. |
| `capacityFactor` | 0.9 | - | Average annual utilization factor (Generation / Rated Capacity). Accounts for refueling outages and maintenance. |
| `electricityPrice` | 130 | $/MWh | Market price of electricity sold (used for Revenue calculation in CFS). |
| `salesToRevenueRatio` | 0.5 | - | Fraction of gross sales that contributes to effective revenue (e.g., accounting for transmission fees or losses). |

### 6. Financial
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `escalationNSSS` | 0.0 | /yr | Annual cost escalation rate for Nuclear Steam Supply System components. |
| `escalationTG` | 0.05 | /yr | Annual cost escalation rate for Turbine-Generator islands. |
| `escalationBOP` | 0.065 | /yr | Annual cost escalation rate for Balance of Plant (Construction materials). |
| `escalationLabor` | 0.052 | /yr | Annual escalation rate for construction labor wages. |
| `escalationInterimStorage`| 0.05 | /yr | Escalation rate applied to back-end fuel cycle costs. |
| `escalationDisposal` | 0.05 | /yr | Escalation rate for calculation of the permanent disposal fund. |
| `debtToEquityRatio` | 0.0 | - | Ratio of Debt to Equity financing. (e.g., 2.33 implies 70% Debt, 30% Equity). |
| `interestRate` | 0.05 | /yr | Annual interest rate on debt financing. |
| `loanTenor` | 18 | years | Duration of the loan repayment period, starting from operation. |
| `depreciationPeriod` | 60 | years | Time period over which capital assets are depreciated for tax purposes. |
| `taxRate` | 0.22 | - | Corporate income tax rate applied to EBT (Earnings Before Tax). |
| `discountRate` | 0.05 | - | Real discount rate used to discount future cash flows for LCOE and NPV calculation. |

### 7. Cost & Scaling
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `minMeanMAX` | "Mean" | - | Selects which cost scenario to use from the reference database (Cost uncertainty range). |
| `DesignSimplification` | 1.0 | - | Set of multipliers (`_safetyPIPING`, `_safetyVALVES`, etc.) applied to reduce quantities of safety-grade components relative to the reference design (0.0 = complete elimination, 1.0 = same as reference). |
| `Country` | "South Korea"| - | Selects the target country to apply localization factors (Labor productivity, Commodity pricing) from `COUNTRY_SPECIFIC` sheet. |

### 8. Construction Rates
| Parameter | Default | Units | Detailed Description |
| :--- | :--- | :--- | :--- |
| `Rate_BASEMAT` | 8476 | CY/mo | Installation rate of concrete for the Basemat. Used to determine critical path duration: $Time = Volume / Rate$. |
| `Rate_INCV` | 713 | CY/mo | Installation rate of concrete for Inner Containment Vessel structures. |
| `Rate_CNT` | 1217 | CY/mo | Installation rate of concrete for the Containment Wall. |
| `Licensing_Duration` | 2 | years | Duration of the licensing phase prior to commercial operation (adds to total project time). |
