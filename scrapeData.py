import requests
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class FearGreedBacktester:
    def __init__(self):
        # Configuration variables - modify these as needed
        self.WEEKLY_BUDGET = 500  # Total weekly investment budget for both strategies
        
        # Fear/Greed investment multipliers (percentage of weekly budget)
        self.INVESTMENT_MULTIPLIERS = {
            'Extreme Fear': 2.0,     # Invest 200% of weekly budget (use saved cash)
            'Fear': 1.5,             # Invest 150% of weekly budget
            'Neutral': 1.0,          # Invest 100% of weekly budget (normal)
            'Greed': 0.5,            # Invest 50% of weekly budget (save cash)
            'Extreme Greed': 0.2     # Invest 20% of weekly budget (save most cash)
        }
        
        # Trading configuration
        self.PURCHASE_DAY = 1  # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday
        self.START_DATE = '2020-01-01'  # Backtest start date
        self.END_DATE = 'present'       # Backtest end date ('present' for current date or specific date like '2024-12-31')
        self.INITIAL_CASH = 0       # Starting cash balance for both strategies
        
        # Fee configuration
        self.TRANSACTION_FEE = 0  # Fee per transaction (e.g., $0.50)
        self.EXPENSE_RATIO = 0.0003  # Annual expense ratio (0.03% for SPY)

        self._fear_greed_df = None
        self._sp500_df = None
        
    def get_fear_greed_data(self):
        if self._fear_greed_df is not None:
            return self._fear_greed_df

        """Fetch fear and greed index data"""
        url = "https://www.finhacker.cz/wp-content/custom-api/fear-greed-data.php"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://www.finhacker.cz/fear-and-greed-index-historical-data-and-chart/",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json().get("agg", [])
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'])
            df = df.sort_values('date').reset_index(drop=True)
            self._fear_greed_df = df
            return df
        except Exception as e:
            print(f"Error fetching fear/greed data: {e}")
            return None
    
    def get_sp500_data(self, start_date, end_date):
        if self._sp500_df is not None:
            return self._sp500_df

        """Fetch S&P 500 data using yfinance with fallback options"""
        # Handle 'present' end date
        if end_date == 'present':
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Try multiple tickers as fallbacks
        tickers_to_try = ['SPY', 'VOO']
        
        for ticker in tickers_to_try:
            try:
                # Add retry logic and different parameters
                sp500 = yf.download(
                    ticker, 
                    start=start_date, 
                    end=end_date, 
                    progress=False,
                    timeout=30,
                    threads=False
                )
                
                if sp500.empty:
                    print(f"{ticker} returned empty data")
                    continue
                
                sp500 = sp500.reset_index()
                
                # Check if we have the required columns
                if 'Date' not in sp500.columns:
                    print(f"{ticker} missing Date column")
                    continue
                    
                if 'Adj Close' not in sp500.columns:
                    if 'Close' in sp500.columns:
                        sp500['Adj Close'] = sp500['Close']
                    else:
                        print(f"{ticker} missing price columns")
                        continue
                
                sp500['Date'] = pd.to_datetime(sp500['Date'])
                result_df = sp500[['Date', 'Adj Close']].rename(columns={'Date': 'date', 'Adj Close': 'price'})
                
                # Remove any NaN values
                result_df = result_df.dropna()
                
                if len(result_df) > 0:
                    self._sp500_df = result_df
                    return result_df
                else:
                    print(f"{ticker} had no valid data after cleaning")
                    continue
                    
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                continue
        
        print("All ticker downloads failed. You may need to:")
        print("1. Check your internet connection")
        print("2. Try again later (yfinance sometimes has temporary issues)")
        print("3. Install/update yfinance: pip install --upgrade yfinance")
        return None
    
    def classify_fear_greed(self, value):
        """Classify fear/greed value into categories"""
        if value <= 24:
            return 'Extreme Fear'
        elif value <= 44:
            return 'Fear'
        elif value <= 55:
            return 'Neutral'
        elif value <= 75:
            return 'Greed'
        else:
            return 'Extreme Greed'
    
    def get_purchase_dates(self, start_date, end_date, day_of_week):
        """Generate all purchase dates based on day of week"""
        dates = []
        current_date = pd.to_datetime(start_date)
        
        # Handle 'present' end date
        if end_date == 'present':
            end_date = pd.to_datetime(datetime.now().strftime('%Y-%m-%d'))
        else:
            end_date = pd.to_datetime(end_date)
        
        # Find first occurrence of the specified day
        while current_date.weekday() != day_of_week:
            current_date += timedelta(days=1)
        
        # Generate weekly dates
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=7)
        
        return dates
    
    def get_most_recent_fear_greed(self, target_date, fear_greed_df):
        """Get the most recent fear/greed value before or on target date"""
        available_dates = fear_greed_df[fear_greed_df['date'] <= target_date]
        if len(available_dates) == 0:
            return None
        
        # Get the value as a scalar, not a Series
        value = available_dates.iloc[-1]['value']
        return float(value)  # Ensure it's a scalar float
    
    def get_sp500_price(self, target_date, sp500_df):
        """Get S&P 500 price on or closest to target date"""
        # Find the closest date (forward fill for weekends/holidays)
        available_dates = sp500_df[sp500_df['date'] <= target_date]
        if len(available_dates) == 0:
            return None
        
        # Get the price as a scalar value, not a Series
        price = available_dates.iloc[-1]['price']
        return float(price)  # Ensure it's a scalar float
    
    def run_backtest(self):
        """Run the complete backtest comparing both strategies"""
        # Get data
        fear_greed_df = self.get_fear_greed_data()
        sp500_df = self.get_sp500_data(self.START_DATE, self.END_DATE)
        
        if fear_greed_df is None:
            print("Failed to fetch fear/greed data")
            return None
            
        if sp500_df is None:
            print("Failed to fetch S&P 500 data")
            return None
        
        if len(sp500_df) == 0:
            print("S&P 500 data is empty")
            return None
        
        # Generate purchase dates
        purchase_dates = self.get_purchase_dates(self.START_DATE, self.END_DATE, self.PURCHASE_DAY)
        
        # Initialize tracking variables for BOTH strategies
        # Strategy 1: Consistent DCA
        dca_cash = float(self.INITIAL_CASH)
        dca_shares = 0.0
        dca_history = []
        dca_transactions = []
        dca_total_budget_received = 0.0
        
        # Strategy 2: Fear/Greed with cash buffer
        fg_cash_buffer = float(self.INITIAL_CASH)  # This is the "bank" for timing the market
        fg_shares = 0.0
        fg_history = []
        fg_transactions = []
        fg_cash_stats = []  # Track cash buffer over time
        fg_total_budget_received = 0.0
        
        # Week counting and categorization
        total_weeks = 0
        fear_greed_week_counts = {
            'Extreme Fear': 0,
            'Fear': 0,
            'Neutral': 0,
            'Greed': 0,
            'Extreme Greed': 0
        }
        
        dca_successful_purchases = 0
        fg_successful_purchases = 0
        
        for date in purchase_dates:
            # Get fear/greed value
            fear_greed_value = self.get_most_recent_fear_greed(date, fear_greed_df)
            if fear_greed_value is None:
                continue
            
            # Get S&P 500 price
            sp500_price = self.get_sp500_price(date, sp500_df)
            if sp500_price is None:
                continue
            
            # Ensure all values are scalars
            fear_greed_value = float(fear_greed_value)
            sp500_price = float(sp500_price)
            
            # Count this week and categorize
            total_weeks += 1
            fear_greed_category = self.classify_fear_greed(fear_greed_value)
            fear_greed_week_counts[fear_greed_category] += 1
            
            # Both strategies receive the same weekly budget
            weekly_budget = float(self.WEEKLY_BUDGET)
            dca_total_budget_received += weekly_budget
            fg_total_budget_received += weekly_budget
            
            # === STRATEGY 1: CONSISTENT DCA ===
            # Add weekly budget to DCA cash and always invest it
            dca_cash += weekly_budget
            
            if dca_cash >= weekly_budget + self.TRANSACTION_FEE:
                effective_investment = weekly_budget - self.TRANSACTION_FEE
                shares_to_buy = effective_investment / sp500_price
                
                dca_cash = dca_cash - weekly_budget
                dca_shares = dca_shares + shares_to_buy
                dca_successful_purchases += 1
                
                dca_transactions.append({
                    'date': date,
                    'investment_amount': weekly_budget,
                    'shares_bought': shares_to_buy,
                    'total_shares': dca_shares,
                    'cash_balance': dca_cash,
                    'price': sp500_price
                })
            
            # Calculate DCA portfolio value
            dca_portfolio_value = dca_cash + (dca_shares * sp500_price)
            
            # Apply expense ratio to DCA
            if float(dca_shares) > 0:
                daily_expense = (dca_shares * sp500_price * self.EXPENSE_RATIO) / 365
                dca_portfolio_value = dca_portfolio_value - daily_expense
                dca_shares = dca_shares - (daily_expense / sp500_price)
            
            dca_history.append({
                'date': date,
                'portfolio_value': float(dca_portfolio_value),
                'shares_owned': float(dca_shares),
                'cash_balance': float(dca_cash),
                'sp500_price': sp500_price
            })
            
            # === STRATEGY 2: FEAR/GREED WITH CASH BUFFER ===
            investment_multiplier = self.INVESTMENT_MULTIPLIERS[fear_greed_category]

            # Add weekly budget to the cash buffer
            fg_cash_buffer += weekly_budget

            # 1. Calculate the ideal investment for this week
            desired_investment = weekly_budget * investment_multiplier

            # 2. Determine the actual investment amount, capped by the available cash buffer.
            investment_to_make = min(desired_investment, fg_cash_buffer)

            # 3. Only proceed if the determined investment can cover the transaction fee.
            if investment_to_make > self.TRANSACTION_FEE:
                # The amount for shares is the investment minus the fee
                amount_for_shares = investment_to_make - self.TRANSACTION_FEE
                shares_to_buy = amount_for_shares / sp500_price
                
                # Update portfolio state
                fg_cash_buffer -= investment_to_make  # Deduct the total amount spent
                fg_shares += shares_to_buy
                fg_successful_purchases += 1
                
                # Log the transaction with both desired and actual investment amounts
                fg_transactions.append({
                    'date': date,
                    'fear_greed_value': fear_greed_value,
                    'fear_greed_category': fear_greed_category,
                    'investment_multiplier': investment_multiplier,
                    'desired_investment': desired_investment,
                    'investment_amount': investment_to_make,  # Log the actual amount spent
                    'shares_bought': shares_to_buy,
                    'total_shares': fg_shares,
                    'cash_buffer': fg_cash_buffer,
                    'price': sp500_price
                })
            
            # Calculate Fear/Greed portfolio value
            fg_portfolio_value = fg_cash_buffer + (fg_shares * sp500_price)
            
            # Apply expense ratio to Fear/Greed strategy
            if float(fg_shares) > 0:
                daily_expense = (fg_shares * sp500_price * self.EXPENSE_RATIO) / 365
                fg_portfolio_value = fg_portfolio_value - daily_expense
                fg_shares = fg_shares - (daily_expense / sp500_price)
            
            # Track cash buffer statistics
            fg_cash_stats.append({
                'date': date,
                'cash_buffer': float(fg_cash_buffer),
                'fear_greed_value': fear_greed_value,
                'fear_greed_category': fear_greed_category
            })
            
            fg_history.append({
                'date': date,
                'portfolio_value': float(fg_portfolio_value),
                'shares_owned': float(fg_shares),
                'cash_buffer': float(fg_cash_buffer),
                'sp500_price': sp500_price,
                'fear_greed_value': fear_greed_value
            })
        
        if len(dca_history) == 0 or len(fg_history) == 0:
            print("No portfolio history generated - check date ranges and data availability")
            return None
        
        # Convert to DataFrames
        dca_portfolio_df = pd.DataFrame(dca_history)
        dca_transactions_df = pd.DataFrame(dca_transactions)
        fg_portfolio_df = pd.DataFrame(fg_history)
        fg_transactions_df = pd.DataFrame(fg_transactions)
        fg_cash_stats_df = pd.DataFrame(fg_cash_stats)
        
        return (dca_portfolio_df, dca_transactions_df, fg_portfolio_df, fg_transactions_df, 
                fg_cash_stats_df, sp500_df, total_weeks, fear_greed_week_counts, 
                dca_total_budget_received, fg_total_budget_received)
    
    def plot_results(self, dca_portfolio_df, fg_portfolio_df, fg_cash_stats_df, dca_transactions_df, fg_transactions_df):
        """Plot comparison of both strategies"""
        if len(dca_portfolio_df) == 0 or len(fg_portfolio_df) == 0:
            print("No data to plot")
            return
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
        
        # Plot 1: Portfolio Performance Comparison
        ax1.plot(dca_portfolio_df['date'], dca_portfolio_df['portfolio_value'], 
                label='Consistent DCA', linewidth=2, color='blue')
        ax1.plot(fg_portfolio_df['date'], fg_portfolio_df['portfolio_value'], 
                label='Fear/Greed Strategy', linewidth=2, color='red')
        
        ax1.set_title('Portfolio Performance Comparison', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.ticklabel_format(style='plain', axis='y')
        
        # Plot 2: Cash Buffer Over Time
        ax2.plot(fg_cash_stats_df['date'], fg_cash_stats_df['cash_buffer'], 
                color='green', linewidth=2)
        ax2.set_title('Fear/Greed Strategy Cash Buffer', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Cash Buffer ($)')
        ax2.grid(True, alpha=0.3)
        ax2.ticklabel_format(style='plain', axis='y')
        
        # # Plot 3: Fear/Greed Index over time
        # ax3.plot(fg_portfolio_df['date'], fg_portfolio_df['fear_greed_value'], 
        #         color='orange', linewidth=1.5)
        # ax3.axhline(y=25, color='red', linestyle='--', alpha=0.5, label='Extreme Fear')
        # ax3.axhline(y=75, color='darkgreen', linestyle='--', alpha=0.5, label='Extreme Greed')
        # ax3.set_title('Fear & Greed Index Over Time', fontsize=14, fontweight='bold')
        # ax3.set_ylabel('Fear & Greed Index')
        # ax3.set_xlabel('Date')
        # ax3.legend()
        # ax3.grid(True, alpha=0.3)
        # ax3.set_ylim(0, 100)

        # Plot 3: Weekly Investment Amounts (replaces Fear & Greed Index plot)
        dca_weekly = pd.DataFrame(dca_transactions_df[['date', 'investment_amount']]).copy()
        dca_weekly['strategy'] = 'DCA'

        fg_weekly = pd.DataFrame(fg_transactions_df[['date', 'investment_amount']]).copy()
        fg_weekly['strategy'] = 'Fear/Greed'

        all_investments = pd.concat([dca_weekly, fg_weekly]).sort_values('date')
        pivot_df = all_investments.pivot(index='date', columns='strategy', values='investment_amount').fillna(0)

        ax3.plot(pivot_df.index, pivot_df['DCA'], label='Consistent DCA', color='blue', linewidth=1.8)
        ax3.plot(pivot_df.index, pivot_df['Fear/Greed'], label='Fear/Greed Strategy', color='red', linewidth=1.8)
        ax3.set_title('Weekly Investment Amount by Strategy', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Investment ($)')
        ax3.set_xlabel('Date')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.ticklabel_format(style='plain', axis='y')
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: S&P 500 price
        ax4.plot(dca_portfolio_df['date'], dca_portfolio_df['sp500_price'], 
                color='black', linewidth=1.5)
        ax4.set_title('S&P 500 Price Over Time', fontsize=14, fontweight='bold')
        ax4.set_ylabel('S&P 500 Price ($)')
        ax4.set_xlabel('Date')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def print_summary_stats(self, dca_portfolio_df, dca_transactions_df, fg_portfolio_df, fg_transactions_df, 
                           fg_cash_stats_df, total_weeks, fear_greed_week_counts, dca_total_budget_received, fg_total_budget_received):
        """Print comprehensive summary statistics"""
        if len(dca_portfolio_df) == 0 or len(fg_portfolio_df) == 0:
            print("No data to analyze")
            return
        
        print("\n" + "="*80)
        print("BACKTEST SUMMARY STATISTICS")
        print("="*80)
        
        # DCA Strategy Stats
        dca_total_invested = dca_transactions_df['investment_amount'].sum() if len(dca_transactions_df) > 0 else 0
        dca_final_value = dca_portfolio_df['portfolio_value'].iloc[-1]
        dca_final_cash = dca_portfolio_df['cash_balance'].iloc[-1]
        dca_total_return = dca_final_value - self.INITIAL_CASH - dca_total_budget_received
        dca_total_return_pct = (dca_total_return / (self.INITIAL_CASH + dca_total_budget_received)) * 100
        
        # Fear/Greed Strategy Stats
        fg_total_invested = fg_transactions_df['investment_amount'].sum() if len(fg_transactions_df) > 0 else 0
        fg_final_value = fg_portfolio_df['portfolio_value'].iloc[-1]
        fg_final_cash = fg_portfolio_df['cash_buffer'].iloc[-1]
        fg_total_return = fg_final_value - self.INITIAL_CASH - fg_total_budget_received
        fg_total_return_pct = (fg_total_return / (self.INITIAL_CASH + fg_total_budget_received)) * 100
        
        # Cash buffer stats
        max_cash = fg_cash_stats_df['cash_buffer'].max()
        min_cash = fg_cash_stats_df['cash_buffer'].min()
        avg_cash = fg_cash_stats_df['cash_buffer'].mean()
        
        print(f"Total Weeks:            {total_weeks}")
        print(f"Weekly Budget:          ${self.WEEKLY_BUDGET:,.2f}")
        print(f"Initial Cash:           ${self.INITIAL_CASH:,.2f} per strategy")
        
        print(f"\nWeek Breakdown by Fear/Greed Level:")
        for category, count in fear_greed_week_counts.items():
            print(f"  {category:15}: {count:3d} weeks")
        
        print(f"\n{'='*40}")
        print("CONSISTENT DCA STRATEGY")
        print('='*40)
        print(f"Total Budget Received:  ${dca_total_budget_received:,.2f}")
        print(f"Total Actually Invested: ${dca_total_invested:,.2f}")
        print(f"Final Portfolio Value:  ${dca_final_value:,.2f}")
        print(f"Final Cash Balance:     ${dca_final_cash:,.2f}")
        print(f"Total Return:           ${dca_total_return:,.2f}")
        print(f"Total Return %:         {dca_total_return_pct:.2f}%")
        print(f"Total Transactions:     {len(dca_transactions_df)}")
        
        print(f"\n{'='*40}")
        print("FEAR/GREED STRATEGY")
        print('='*40)
        print(f"Total Budget Received:  ${fg_total_budget_received:,.2f}")
        print(f"Total Actually Invested: ${fg_total_invested:,.2f}")
        print(f"Final Portfolio Value:  ${fg_final_value:,.2f}")
        print(f"Final Cash Buffer:      ${fg_final_cash:,.2f}")
        print(f"Total Return:           ${fg_total_return:,.2f}")
        print(f"Total Return %:         {fg_total_return_pct:.2f}%")
        print(f"Total Transactions:     {len(fg_transactions_df)}")
        
        print(f"\nCash Buffer Statistics:")
        print(f"  Maximum Cash on Hand:  ${max_cash:,.2f}")
        print(f"  Minimum Cash on Hand:  ${min_cash:,.2f}")
        print(f"  Average Cash on Hand:  ${avg_cash:,.2f}")
        print(f"  Final Cash on Hand:    ${fg_final_cash:,.2f}")
        
        # Investment by category
        if len(fg_transactions_df) > 0:
            print(f"\nActual Investment by Fear/Greed Category:")
            category_stats = fg_transactions_df.groupby('fear_greed_category')['desired_investment'].agg(['count', 'sum'])
            for category, stats in category_stats.iterrows():
                multiplier = self.INVESTMENT_MULTIPLIERS[category]
                print(f"  {category:15}: {int(stats['count']):3d} trades, ${stats['sum']:,.2f} ({multiplier:.1f}x multiplier)")
        
        # Performance comparison
        excess_return = fg_total_return_pct - dca_total_return_pct
        print(f"\n{'='*40}")
        print("STRATEGY COMPARISON")
        print('='*40)
        print(f"Budget Verification:")
        print(f"  DCA Budget Received:    ${dca_total_budget_received:,.2f}")
        print(f"  F&G Budget Received:    ${fg_total_budget_received:,.2f}")
        print(f"  Budget Difference:      ${abs(dca_total_budget_received - fg_total_budget_received):,.2f}")
        print(f"\nFear/Greed vs DCA:")
        print(f"  Excess Return:         {excess_return:+.2f}%")
        if excess_return > 0:
            print(f"  Fear/Greed strategy outperformed by {excess_return:.2f}%")
        else:
            print(f"  DCA strategy outperformed by {abs(excess_return):.2f}%")