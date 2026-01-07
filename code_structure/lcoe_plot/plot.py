import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_lcoe_stack_from_csv(
    csv_path: str,
    *,
    case_col: str = "Case",
    fuel_col: str = "Fuel",
    om_col: str = "O&M",
    capex_col: str = "CAPEX",
    component_col: str = "Component",   # long 형식일 때만 사용
    value_col: str = "Value",           # long 형식일 때만 사용
    order: list[str] | None = None,     # 예: ["A","B","C"]
    title: str = "LCOE Breakdown",
    y_label: str = "LCOE ($/MWh)",
    annotate_total: bool = True,
    figsize=(7, 4),
    save_path: str | None = None,
    dpi: int = 300,
):
    """
    A/B/C 같은 Case별 LCOE를 Fuel, O&M, CAPEX로 스택 막대 그래프로 그림.
    - Wide 형식: Case,Fuel,O&M,CAPEX
    - Long  형식: Case,Component,Value  (Component는 Fuel/O&M/CAPEX 중 하나)
    """
    # Read CSV with tab/whitespace delimiter
    df = pd.read_csv(csv_path, sep='\t')
    df.columns = df.columns.str.strip()

    # --- Wide 형식인지 확인 ---
    wide_cols = {case_col, fuel_col, om_col, capex_col}
    is_wide = wide_cols.issubset(set(df.columns))

    # --- Long 형식인지 확인 ---
    long_cols = {case_col, component_col, value_col}
    is_long = long_cols.issubset(set(df.columns))

    if not (is_wide or is_long):
        raise ValueError(
            "CSV 형식을 인식 못했습니다.\n"
            f"Wide 형식 필요 컬럼: {sorted(list(wide_cols))}\n"
            f"Long 형식 필요 컬럼: {sorted(list(long_cols))}\n"
            f"현재 컬럼: {list(df.columns)}"
        )

    if is_long and not is_wide:
        # Long -> Wide 변환
        df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0.0)
        pivot = df.pivot_table(
            index=case_col, columns=component_col, values=value_col, aggfunc="sum"
        ).reset_index()

        # 누락된 컴포넌트가 있으면 0으로 채움
        for c in [fuel_col, om_col, capex_col]:
            if c not in pivot.columns:
                pivot[c] = 0.0
        dfw = pivot[[case_col, fuel_col, om_col, capex_col]].copy()
    else:
        # Wide 그대로 사용
        dfw = df[[case_col, fuel_col, om_col, capex_col]].copy()
        for c in [fuel_col, om_col, capex_col]:
            dfw[c] = pd.to_numeric(dfw[c], errors="coerce").fillna(0.0)

    # 순서 지정
    if order is not None:
        dfw[case_col] = pd.Categorical(dfw[case_col], categories=order, ordered=True)
        dfw = dfw.sort_values(case_col)
    else:
        dfw = dfw.sort_values(case_col)

    cases = dfw[case_col].astype(str).tolist()
    x = np.arange(len(cases))

    fuel = dfw[fuel_col].to_numpy()
    om = dfw[om_col].to_numpy()
    capex = dfw[capex_col].to_numpy()

    fig, ax = plt.subplots(figsize=figsize)

    b1 = ax.bar(x, capex, label="CAPEX")
    b2 = ax.bar(x, om, bottom=capex, label="O&M")
    b3 = ax.bar(x, fuel, bottom=capex + om, label="Fuel")

    totals = capex + om + fuel

    if annotate_total:
        for i, t in enumerate(totals):
            ax.text(x[i], t, f"{t:.2f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(cases, rotation=45, ha='right')
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.5)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches="tight")

    return fig, ax


def main():
    """Main function to plot LCOE data from lcoe.csv"""
    from pathlib import Path
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    csv_path = script_dir / "lcoe.csv"
    save_path = script_dir / "lcoe_stack.png"
    
    print(f"Reading data from: {csv_path}")
    
    # Plot the LCOE stack chart
    fig, ax = plot_lcoe_stack_from_csv(
        str(csv_path),
        title="LCOE Breakdown by Reactor Design",
        y_label="LCOE ($/MWh)",
        annotate_total=True,
        figsize=(14, 7),
        save_path=str(save_path),
        dpi=300
    )
    
    print(f"Plot saved to: {save_path}")
    plt.show()


if __name__ == "__main__":
    main()


# --- 사용 예시 (Wide 형식) ---
# CSV: Case	Fuel	O&M	CAPEX  (tab-delimited)
# A	10.2	5.1	30.0
# B	12.0	4.8	28.5
# C	9.7	5.5	32.1
#
# plot_lcoe_stack_from_csv("lcoe.csv", order=["A","B","C"], save_path="lcoe_stack.png")


# --- 사용 예시 (Long 형식) ---
# CSV: Case	Component	Value  (tab-delimited)
# A	Fuel	10.2
# A	O&M	5.1
# A	CAPEX	30.0
# ...
#
# plot_lcoe_stack_from_csv("lcoe_long.csv", save_path="lcoe_stack.png")
