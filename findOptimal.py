import numpy as np
from skopt import gp_minimize
from skopt.space import Real
from skopt.acquisition import gaussian_ei
from scrapeData import FearGreedBacktester

def bayesian_optimization():
    """
    Use Bayesian optimization to find optimal Fear & Greed multipliers
    """
    
    # Initialize backtester
    backtester = FearGreedBacktester()
    backtester.PURCHASE_DAY = 1
    backtester.START_DATE = '2015-07-28'
    backtester.END_DATE = '2025-07-28'
    backtester.WEEKLY_BUDGET = 500
    backtester.INITIAL_CASH = 0
    
    # Keep track of all evaluations for analysis
    evaluation_history = []
    
    def objective_function(params):
        """
        Objective function to minimize (we minimize negative portfolio value)
        
        Args:
            params: [extreme_fear, fear, neutral, greed, extreme_greed] multipliers
        
        Returns:
            float: Negative portfolio value (since we want to maximize portfolio value)
        """
        ef, f, n, g, eg = params
        
        print(f"[{len(evaluation_history)+1}] Evaluating: EF={ef:.2f}, F={f:.2f}, N={n:.2f}, G={g:.2f}, EG={eg:.2f}", end=" -- ")
        
        # Apply constraint: at least one multiplier should be ≤ 1.0
        if min(ef, f, n, g, eg) > 1.0:
            print("Skipped (constraint violation)")
            return 1e6  # Large penalty for constraint violation
        
        # Set up backtester with current parameters
        backtester.INVESTMENT_MULTIPLIERS = {
            'Extreme Fear': ef,
            'Fear': f,
            'Neutral': n,  # Now also a parameter
            'Greed': g,
            'Extreme Greed': eg
        }
        
        try:
            result = backtester.run_backtest()
            if result is None:
                print("Backtest failed")
                return 1e6
            
            # Extract results
            (_, _, fg_portfolio_df, _, _, _, _, _, dca_total_budget, fg_total_budget) = result
            final_value = fg_portfolio_df['portfolio_value'].iloc[-1]
            
            # Calculate excess return vs DCA
            dca_final_value = result[0]['portfolio_value'].iloc[-1]
            fg_return_pct = ((final_value - fg_total_budget) / fg_total_budget) * 100 if fg_total_budget > 0 else 0
            dca_return_pct = ((dca_final_value - dca_total_budget) / dca_total_budget) * 100 if dca_total_budget > 0 else 0
            excess_return = fg_return_pct - dca_return_pct
            
            print(f"Portfolio Value: ${final_value:.2f}, Excess Return: {excess_return:.2f}%")
            
            # Store evaluation for analysis
            evaluation_history.append({
                'params': {'EF': ef, 'F': f, 'N': n, 'G': g, 'EG': eg},
                'portfolio_value': final_value,
                'excess_return': excess_return
            })
            
            # Return negative value since we're minimizing
            return -final_value
            
        except Exception as e:
            print(f"Error: {e}")
            return 1e6
    
    # Define search space - now includes neutral as a parameter
    # Each parameter can range from 0.0 to 2.0
    search_space = [
        Real(0.0, 2.0, name='extreme_fear'),  # Extreme Fear multiplier
        Real(0.0, 2.0, name='fear'),          # Fear multiplier
        Real(0.0, 2.0, name='neutral'),       # Neutral multiplier (now optimized)
        Real(0.0, 2.0, name='greed'),         # Greed multiplier
        Real(0.0, 2.0, name='extreme_greed')  # Extreme Greed multiplier
    ]
    
    print("Starting Bayesian Optimization...")
    print("Optimizing all 5 sentiment multipliers (including Neutral)!")
    print("This will intelligently sample ~200 parameter combinations.")
    print("-" * 80)
    
    # Run Bayesian optimization
    result = gp_minimize(
        func=objective_function,           # Function to minimize
        dimensions=search_space,           # Parameter bounds
        n_calls=400,                      # Number of evaluations
        n_initial_points=25,              # Random exploration points to start
        acq_func='EI',                    # Expected Improvement acquisition
        random_state=42,                  # For reproducibility
        verbose=False                      # Show progress
    )
    
    # Extract best results
    best_params = result.x
    best_value = -result.fun  # Convert back from negative
    
    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE!")
    print("="*80)
    print(f"Best Portfolio Value: ${best_value:.2f}")
    print(f"Best Parameters:")
    print(f"  Extreme Fear: {best_params[0]:.2f}")
    print(f"  Fear:         {best_params[1]:.2f}")
    print(f"  Neutral:      {best_params[2]:.2f}")
    print(f"  Greed:        {best_params[3]:.2f}")
    print(f"  Extreme Greed: {best_params[4]:.2f}")
    
    # Find best result in history for excess return info
    best_eval = max(evaluation_history, key=lambda x: x['portfolio_value'])
    print(f"Excess Return vs DCA: {best_eval['excess_return']:.2f}%")
    
    # Show top 10 results
    print("\nTop 10 Results:")
    print("-" * 60)
    sorted_history = sorted(evaluation_history, key=lambda x: x['portfolio_value'], reverse=True)
    for i, eval_result in enumerate(sorted_history[:10], 1):
        p = eval_result['params']
        print(f"{i:2d}.) EF={p['EF']:.2f}, F={p['F']:.2f}, N={p['N']:.2f}, G={p['G']:.2f}, EG={p['EG']:.2f} "
              f": ${eval_result['portfolio_value']:.2f} (Excess: {eval_result['excess_return']:.2f}%)")
    
    # Save results
    with open("bayesian_optimization_results.txt", "w") as f:
        f.write("Bayesian Optimization Results (with Neutral parameter)\n")
        f.write("="*60 + "\n")
        f.write(f"Best Portfolio Value: ${best_value:.2f}\n")
        f.write(f"Best Parameters: EF={best_params[0]:.2f}, F={best_params[1]:.2f}, N={best_params[2]:.2f}, G={best_params[3]:.2f}, EG={best_params[4]:.2f}\n")
        f.write(f"Total Evaluations: {len(evaluation_history)}\n\n")
        f.write("Top 10 Results:\n")
        for i, eval_result in enumerate(sorted_history[:10], 1):
            p = eval_result['params']
            f.write(f"{i:2d}.) EF={p['EF']:.2f}, F={p['F']:.2f}, N={p['N']:.2f}, G={p['G']:.2f}, EG={p['EG']:.2f} "
                   f": ${eval_result['portfolio_value']:.2f} (Excess: {eval_result['excess_return']:.2f}%)\n")
    
    return result, evaluation_history

if __name__ == "__main__":
    # Run the optimization
    optimization_result, history = bayesian_optimization()
    
    print(f"\nEfficiency Gain:")
    print(f"Full Grid Search: Would be 3,200,000+ evaluations (2.0^5 with 0.01 steps)")  
    print(f"Bayesian Opt: {len(history)} evaluations")
    print(f"Speedup: ~{3200000 // len(history)}x faster!")