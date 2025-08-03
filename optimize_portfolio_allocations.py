import pandas as pd
import numpy as np
import os
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# --- ======================================================================= ---
# --- STEP 1: DEFINE ALL YOUR SCENARIOS HERE                                  ---
# --- ======================================================================= ---

# Each dictionary in this list represents one full run of the optimizer.
# Give each a unique 'name' for the report folders.

SCENARIOS_TO_RUN = [
    {
        'name': 'Conservative_5_Percent',
        'target_return': 0.05,
        'constraints': {
            'SPY': 0.13,
            'BOEING_Stable_2_84': 0.13,
            'BOEING_BALANCED_70_30': 0.03,
            'BA': 0.02
        }
    },
    {
        'name': 'Moderate_7_Percent',
        'target_return': 0.07,
        'constraints': {
            'SPY': 0.13,
            'BOEING_Stable_2_84': 0.13,
            'BOEING_BALANCED_70_30': 0.03,
            'BA': 0.02
        }
    },
    # You can add more scenarios here. For example:
    # {
    #     'name': 'Aggressive_8_Percent_No_Constraints',
    #     'target_return': 0.08,
    #     'constraints': {}
    # }
]

# --- General Configuration ---
input_dir = 'stock_data_yfinance'
add_risk_free_asset = True
risk_free_rate = 0.04
initial_investment = 100000

# --- ======================================================================= ---
# --- (The rest of the script runs automatically based on the scenarios above) ---
# --- ======================================================================= ---

# --- Data Loading and Prep (Done once at the start) ---
if not os.path.exists(input_dir):
    print(f"Error: Directory '{input_dir}' not found. Please run the data prep script.")
    exit()

all_prices = {}
tickers_from_files = []
print(f"Reading data from '{input_dir}' directory...")
for filename in os.listdir(input_dir):
    if filename.endswith('.csv'):
        ticker = filename.split('.')[0]
        tickers_from_files.append(ticker)
        file_path = os.path.join(input_dir, filename)
        df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
        all_prices[ticker] = df['Close']

price_df = pd.DataFrame(all_prices)
price_df = price_df.dropna()
log_returns_risky = np.log(price_df / price_df.shift(1)).dropna()

# --- Main Processing Loop ---
summary_results_for_csv = []
main_reports_dir = 'reports'
os.makedirs(main_reports_dir, exist_ok=True)

for scenario in SCENARIOS_TO_RUN:
    scenario_name = scenario['name']
    target_return = scenario['target_return']
    min_allocation_constraints = scenario['constraints']

    print(f"\n{'='*60}\nRunning Scenario: {scenario_name}\n{'='*60}")

    # --- Prepare Data for this specific scenario ---
    tickers = tickers_from_files.copy()
    expected_returns = log_returns_risky.mean() * 12
    cov_matrix = log_returns_risky.cov() * 12
    num_risky_assets = len(tickers)

    if add_risk_free_asset:
        expected_returns = np.append(expected_returns.values, risk_free_rate)
        if 'Risk-Free' not in tickers:
            tickers.append('Risk-Free')
        new_cov_matrix = np.zeros((num_risky_assets + 1, num_risky_assets + 1))
        new_cov_matrix[:num_risky_assets, :num_risky_assets] = cov_matrix.values
        cov_matrix = pd.DataFrame(new_cov_matrix, index=tickers, columns=tickers)

    # --- Optimization Functions ---
    def portfolio_std_dev(weights, cov_matrix): return np.sqrt(weights.T @ cov_matrix @ weights)
    def portfolio_return(weights, expected_returns): return np.sum(weights * expected_returns)
    def objective_function(weights, cov_matrix): return portfolio_std_dev(weights, cov_matrix)

    # --- Set Up Constraints ---
    num_assets = len(tickers)
    cons = [
        {'type': 'eq', 'fun': lambda weights: portfolio_return(weights, expected_returns) - target_return},
        {'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1}
    ]
    if min_allocation_constraints:
        print("\nApplying minimum allocation constraints:")
        for ticker, min_percentage in min_allocation_constraints.items():
            try:
                idx = tickers.index(ticker)
                print(f"  - Minimum {min_percentage:.0%} for {ticker}")
                def make_constraint(i, p): return lambda w: w[i] - p
                cons.append({'type': 'ineq', 'fun': make_constraint(idx, min_percentage)})
            except ValueError:
                print(f"  - Warning: Constrained ticker '{ticker}' not found. Constraint ignored.")

    bounds = tuple((0, 1) for _ in range(num_assets))
    initial_weights = np.array([1/num_assets] * num_assets)
    
    # --- Run Optimization ---
    optimization_result = minimize(fun=objective_function, x0=initial_weights, args=(cov_matrix,), method='SLSQP', bounds=bounds, constraints=tuple(cons))

    # --- Generate Reports if Successful ---
    if optimization_result.success:
        print(f"\nOptimization for '{scenario_name}' SUCCEEDED.")
        optimal_weights = optimization_result.x
        
        # --- Create Scenario Subdirectory ---
        scenario_dir = os.path.join(main_reports_dir, scenario_name)
        os.makedirs(scenario_dir, exist_ok=True)
        
        # --- Calculations for Reports ---
        optimal_portfolio_return = portfolio_return(optimal_weights, expected_returns)
        optimal_portfolio_volatility = portfolio_std_dev(optimal_weights, cov_matrix)
        
        risky_weights = optimal_weights[:num_risky_assets]
        risk_free_weight = optimal_weights[num_risky_assets] if add_risk_free_asset else 0
        risk_free_monthly_return = (1 + risk_free_rate)**(1/12) - 1 if add_risk_free_asset else 0
        risky_returns_values = np.exp(log_returns_risky.dot(risky_weights)).values - 1
        total_returns_values = risky_returns_values + (risk_free_weight * risk_free_monthly_return)
        portfolio_total_simple_returns = pd.Series(total_returns_values, index=log_returns_risky.index)
        
        portfolio_cumulative_growth = (1 + portfolio_total_simple_returns).cumprod() * initial_investment
        
        portfolio_total_simple_returns.index = pd.to_datetime(portfolio_total_simple_returns.index, utc=True)
        annual_returns = portfolio_total_simple_returns.resample('YE').apply(lambda x: (1 + x).prod() - 1)
        annual_returns_df = pd.DataFrame(annual_returns)
        annual_returns_df.index = annual_returns_df.index.year
        annual_returns_df.columns = ['Annual Return']
        
        running_max = portfolio_cumulative_growth.cummax()
        drawdowns = (portfolio_cumulative_growth - running_max) / running_max
        max_drawdown = drawdowns.min()

        one_std_lower, one_std_upper = optimal_portfolio_return - optimal_portfolio_volatility, optimal_portfolio_return + optimal_portfolio_volatility
        two_std_lower, two_std_upper = optimal_portfolio_return - 2 * optimal_portfolio_volatility, optimal_portfolio_return + 2 * optimal_portfolio_volatility

        # --- Generate and Save Plot ---
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(portfolio_cumulative_growth.index, portfolio_cumulative_growth.values)
        ax.set_title(f'Growth of ${initial_investment:,.0f} - Scenario: {scenario_name}', fontsize=16)
        ax.set_ylabel('Portfolio Value'); ax.set_xlabel('Date')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        plot_path = os.path.join(scenario_dir, 'portfolio_growth_chart.png')
        plt.savefig(plot_path); plt.close(fig)
        
        # --- Generate and Save Text Report ---
        report_text = f"""
==================================================
SUMMARY REPORT FOR SCENARIO: {scenario_name}
==================================================

Optimal Portfolio for a Target Return of {target_return:.2%}
--------------------------------------------------
"""
        for i, t in enumerate(tickers): report_text += f"  Allocation for {t}: {max(0, optimal_weights[i]):.2%}\n"
        report_text += f"""--------------------------------------------------
Expected Annual Return: {optimal_portfolio_return:.2%}
Lowest Possible Annual Volatility: {optimal_portfolio_volatility:.2%}
--------------------------------------------------

Statistical Projections (Forward-Looking)
--------------------------------------------------
68% Confidence Interval (1 Std. Dev.):
  The annual return is expected to be between {one_std_lower:.2%} and {one_std_upper:.2%}.

95% Confidence Interval (2 Std. Dev.):
  The annual return is expected to be between {two_std_lower:.2%} and {two_std_upper:.2%}.

--- Historical Performance Analysis (Backward-Looking) ---

Portfolio Annual Returns:
{annual_returns_df.to_string(formatters={'Annual Return': '{:,.2%}'.format})}

Maximum Drawdown (since {price_df.index.min().year}): {max_drawdown:.2%}
--------------------------------------------------
"""
        report_path = os.path.join(scenario_dir, 'summary_report.txt')
        with open(report_path, 'w') as f: f.write(report_text)
        print(f"-> Saved individual report and plot to '{scenario_dir}'")
        
        # --- Collect data for the final summary CSV ---
        summary_data_row = {'Scenario': scenario_name, 'Target Return': target_return, 'Volatility (Std Dev)': optimal_portfolio_volatility}
        for i, t in enumerate(tickers): summary_data_row[f'Allocation: {t}'] = optimal_weights[i]
        summary_data_row['Max Drawdown'] = max_drawdown
        summary_data_row['2008 Return'] = annual_returns_df.loc[2008, 'Annual Return'] if 2008 in annual_returns_df.index else 'N/A'
        summary_data_row['95% Lower Bound'] = two_std_lower
        summary_data_row['95% Upper Bound'] = two_std_upper
        summary_results_for_csv.append(summary_data_row)
        
    else:
        print(f"Optimization for '{scenario_name}' FAILED. Message: {optimization_result.message}")

# --- Generate Final Comparison CSV ---
if summary_results_for_csv:
    summary_df = pd.DataFrame(summary_results_for_csv)
    summary_df.set_index('Scenario', inplace=True)
    
    # Format columns for better readability
    for col in summary_df.columns:
        if 'Allocation' in col or 'Return' in col or 'Bound' in col or 'Drawdown' in col or 'Volatility' in col:
            summary_df[col] = summary_df[col].apply(lambda x: f"{x:.2%}" if isinstance(x, (int, float)) else x)
            
    summary_csv_path = os.path.join(main_reports_dir, 'scenarios_comparison_summary.csv')
    summary_df.to_csv(summary_csv_path)
    print(f"\n{'='*60}\nMaster comparison report saved to: {summary_csv_path}\n{'='*60}")