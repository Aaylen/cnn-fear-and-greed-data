from backtest import FearGreedBacktester

def main():
    """Main function to run the backtest"""
    backtester = FearGreedBacktester()
    
    # You can modify these parameters:
    backtester.PURCHASE_DAY = 1
    backtester.START_DATE = '2020-07-28'
    backtester.END_DATE = '2025-07-28'
    backtester.WEEKLY_BUDGET = 500
    backtester.INITIAL_CASH = 0

    # Example investment multipliers based on fear/greed levels
    backtester.INVESTMENT_MULTIPLIERS = {
        'Extreme Fear': 2.0,     # Invest 200% of budget when extremely fearful
        'Fear': 1.5,              # Invest 150% of budget when fearful
        'Neutral': 1.0,           # Normal investment
        'Greed': 0.75,            # Invest only 75% when greedy (save cash)
        'Extreme Greed': 0.2     # Invest only 20% when extremely greedy
    }
    
    # Run backtest
    results = backtester.run_backtest()
    
    if results:
        (dca_portfolio_df, dca_transactions_df, fg_portfolio_df, fg_transactions_df, 
         fg_cash_stats_df, sp500_df, total_weeks, fear_greed_week_counts, 
         dca_total_budget_received, fg_total_budget_received) = results
        
        # Print results
        backtester.print_summary_stats(dca_portfolio_df, dca_transactions_df, fg_portfolio_df, 
                                     fg_transactions_df, fg_cash_stats_df, total_weeks, 
                                     fear_greed_week_counts, dca_total_budget_received, fg_total_budget_received)
        
        # Plot results
        backtester.plot_results(dca_portfolio_df, fg_portfolio_df, fg_cash_stats_df, dca_transactions_df, fg_transactions_df)
        
        return results
    
    return None

if __name__ == "__main__":
    # Run the backtest
    results = main()