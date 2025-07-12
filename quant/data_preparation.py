#!/usr/bin/env python3
"""
Data Preparation for Quant Analysis
Joins eBay sold listings with PriceCharting historical data for comprehensive analysis
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class DataPreparation:
    """Prepares and joins data sources for quant analysis"""
    
    def __init__(self):
        self.supabase = supabase
        
    def load_ebay_data(self, card_ids: List[str] = None) -> pd.DataFrame:
        """Load eBay sold listings data"""
        
        print("📊 Loading eBay sold listings data...")
        
        try:
            # Build query
            query = self.supabase.table("ebay_sold_listings").select("""
                *,
                pokemon_cards!inner(card_name, set_name, rarity)
            """)
            
            # Filter by card IDs if provided
            if card_ids:
                query = query.in_("card_id", card_ids)
            
            result = query.execute()
            
            if result.data:
                df = pd.DataFrame(result.data)
                
                # Flatten pokemon_cards data
                card_data = pd.json_normalize(df['pokemon_cards'])
                card_data.columns = ['card_' + col for col in card_data.columns]
                
                # Drop original nested column and concatenate
                df = df.drop('pokemon_cards', axis=1)
                df = pd.concat([df, card_data], axis=1)
                
                # Convert data types
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                df['sold_date'] = pd.to_datetime(df['sold_date'])
                df['created_at'] = pd.to_datetime(df['created_at'])
                
                print(f"✅ Loaded {len(df)} eBay listings")
                return df
            else:
                print("⚠️ No eBay data found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error loading eBay data: {e}")
            return pd.DataFrame()
    
    def load_pricecharting_data(self, data_file: str = None) -> Dict[str, Any]:
        """Load PriceCharting historical data from file"""
        
        print("📈 Loading PriceCharting historical data...")
        
        try:
            # Find the most recent file if none specified
            if not data_file:
                data_dir = "ebay-scraper/data"
                if os.path.exists(data_dir):
                    pc_files = [f for f in os.listdir(data_dir) if f.startswith('pricecharting_historical_')]
                    if pc_files:
                        data_file = os.path.join(data_dir, sorted(pc_files)[-1])
                        print(f"📁 Using latest file: {data_file}")
                    else:
                        print("⚠️ No PriceCharting data files found")
                        return {}
                else:
                    print("⚠️ Data directory not found")
                    return {}
            
            # Load the file
            with open(data_file, 'r') as f:
                data = json.load(f)
            
            print(f"✅ Loaded PriceCharting data: {len(data.get('cards', []))} cards, {len(data.get('sealed_products', []))} sealed products")
            return data
            
        except Exception as e:
            print(f"❌ Error loading PriceCharting data: {e}")
            return {}
    
    def create_unified_dataset(self, ebay_df: pd.DataFrame, 
                             pricecharting_data: Dict[str, Any]) -> pd.DataFrame:
        """Create unified dataset joining eBay and PriceCharting data"""
        
        print("🔗 Creating unified dataset...")
        
        if ebay_df.empty:
            print("⚠️ No eBay data to process")
            return pd.DataFrame()
        
        # Start with eBay data
        unified_df = ebay_df.copy()
        
        # Add PriceCharting data if available
        if pricecharting_data:
            pc_lookup = {}
            
            # Build lookup for cards
            for card_data in pricecharting_data.get('cards', []):
                card_id = card_data.get('card_id')
                if card_id:
                    pc_lookup[card_id] = card_data.get('pricecharting_data', {})
            
            # Add PriceCharting columns
            unified_df['pc_current_price'] = None
            unified_df['pc_loose_price'] = None
            unified_df['pc_graded_price'] = None
            unified_df['pc_new_price'] = None
            unified_df['pc_url'] = None
            
            # Fill PriceCharting data
            for idx, row in unified_df.iterrows():
                card_id = row.get('card_id')
                if card_id in pc_lookup:
                    pc_data = pc_lookup[card_id]
                    current_prices = pc_data.get('current_prices', {})
                    
                    unified_df.at[idx, 'pc_current_price'] = current_prices.get('current')
                    unified_df.at[idx, 'pc_loose_price'] = current_prices.get('loose')
                    unified_df.at[idx, 'pc_graded_price'] = current_prices.get('graded')
                    unified_df.at[idx, 'pc_new_price'] = current_prices.get('new')
                    unified_df.at[idx, 'pc_url'] = pc_data.get('url')
        
        print(f"✅ Created unified dataset with {len(unified_df)} records")
        return unified_df
    
    def calculate_basic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic features for analysis"""
        
        print("📊 Calculating basic features...")
        
        if df.empty:
            return df
        
        # Add time-based features
        df['year'] = df['sold_date'].dt.year
        df['month'] = df['sold_date'].dt.month
        df['quarter'] = df['sold_date'].dt.quarter
        df['day_of_week'] = df['sold_date'].dt.dayofweek
        df['days_since_sold'] = (datetime.now() - df['sold_date']).dt.days
        
        # Price features
        df['log_price'] = np.log1p(df['price'])  # Log(1 + price) to handle zeros
        
        # Condition features
        df['is_graded'] = df['is_graded'].fillna(False)
        df['grade_numeric'] = pd.to_numeric(df['grade'], errors='coerce')
        
        # Set rarity encoding (you may want to customize this)
        rarity_order = {
            'Common': 1, 'Uncommon': 2, 'Rare': 3, 'Rare Holo': 4,
            'Ultra Rare': 5, 'Secret Rare': 6, 'Hyper Rare': 7
        }
        df['rarity_rank'] = df['card_rarity'].map(rarity_order).fillna(0)
        
        # PriceCharting comparison features (if available)
        if 'pc_current_price' in df.columns:
            # Price vs PriceCharting current
            df['price_vs_pc_current'] = df['price'] / df['pc_current_price'].fillna(df['price'])
            df['price_premium_pc'] = ((df['price'] / df['pc_current_price']) - 1) * 100
            
            # Graded vs ungraded comparison
            df['price_vs_pc_loose'] = df['price'] / df['pc_loose_price'].fillna(df['price'])
            df['price_vs_pc_graded'] = df['price'] / df['pc_graded_price'].fillna(df['price'])
        
        print(f"✅ Added features to dataset")
        return df
    
    def calculate_card_aggregates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate per-card aggregate statistics"""
        
        print("📈 Calculating card-level aggregates...")
        
        if df.empty:
            return pd.DataFrame()
        
        # Group by card
        card_stats = df.groupby(['card_id', 'card_card_name', 'card_set_name']).agg({
            'price': ['count', 'mean', 'median', 'std', 'min', 'max'],
            'sold_date': ['min', 'max'],
            'is_graded': 'sum',
            'grade_numeric': 'mean',
            'pc_current_price': 'first',
            'pc_loose_price': 'first', 
            'pc_graded_price': 'first'
        }).round(2)
        
        # Flatten column names
        card_stats.columns = ['_'.join(col).strip() for col in card_stats.columns]
        card_stats = card_stats.reset_index()
        
        # Calculate additional metrics
        card_stats['price_volatility'] = card_stats['price_std'] / card_stats['price_mean']
        card_stats['graded_percentage'] = (card_stats['is_graded_sum'] / card_stats['price_count']) * 100
        card_stats['date_range_days'] = (card_stats['sold_date_max'] - card_stats['sold_date_min']).dt.days
        
        # Market liquidity categories
        card_stats['liquidity'] = pd.cut(card_stats['price_count'], 
                                       bins=[0, 5, 15, 50, float('inf')], 
                                       labels=['Low', 'Medium', 'High', 'Very High'])
        
        print(f"✅ Calculated aggregates for {len(card_stats)} cards")
        return card_stats
    
    def save_prepared_data(self, unified_df: pd.DataFrame, card_stats: pd.DataFrame):
        """Save prepared datasets"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save unified dataset
        unified_file = f"quant/data/unified_dataset_{timestamp}.csv"
        os.makedirs("quant/data", exist_ok=True)
        
        try:
            unified_df.to_csv(unified_file, index=False)
            print(f"💾 Unified dataset saved: {unified_file}")
        except Exception as e:
            print(f"⚠️ Could not save unified dataset: {e}")
        
        # Save card aggregates
        stats_file = f"quant/data/card_stats_{timestamp}.csv"
        try:
            card_stats.to_csv(stats_file, index=False)
            print(f"💾 Card statistics saved: {stats_file}")
        except Exception as e:
            print(f"⚠️ Could not save card statistics: {e}")
    
    def run_full_preparation(self, card_ids: List[str] = None, 
                           pricecharting_file: str = None) -> Dict[str, pd.DataFrame]:
        """Run complete data preparation pipeline"""
        
        print("🚀 STARTING DATA PREPARATION PIPELINE")
        print("=" * 50)
        
        # Load data
        ebay_df = self.load_ebay_data(card_ids)
        pricecharting_data = self.load_pricecharting_data(pricecharting_file)
        
        # Create unified dataset
        unified_df = self.create_unified_dataset(ebay_df, pricecharting_data)
        
        # Calculate features
        unified_df = self.calculate_basic_features(unified_df)
        
        # Calculate aggregates
        card_stats = self.calculate_card_aggregates(unified_df)
        
        # Save results
        self.save_prepared_data(unified_df, card_stats)
        
        print(f"\n✅ DATA PREPARATION COMPLETE")
        print(f"Unified dataset: {len(unified_df)} records")
        print(f"Card statistics: {len(card_stats)} cards")
        
        return {
            'unified_data': unified_df,
            'card_statistics': card_stats
        }

def main():
    """Run data preparation"""
    
    prep = DataPreparation()
    
    # Get curated card IDs
    from ebay_scraper.card_selector import CardSelector
    card_selector = CardSelector()
    curated_cards = card_selector.get_curated_investment_targets()
    card_ids = [card['id'] for card in curated_cards if card.get('id')]
    
    print(f"📊 Preparing data for {len(card_ids)} curated cards")
    
    # Run preparation
    results = prep.run_full_preparation(card_ids)
    
    # Basic analysis preview
    if not results['unified_data'].empty:
        print(f"\n📈 QUICK PREVIEW:")
        print(f"Price range: ${results['unified_data']['price'].min():.2f} - ${results['unified_data']['price'].max():.2f}")
        print(f"Average price: ${results['unified_data']['price'].mean():.2f}")
        print(f"Graded percentage: {(results['unified_data']['is_graded'].sum() / len(results['unified_data'])) * 100:.1f}%")
        
        top_cards = results['card_statistics'].nlargest(5, 'price_mean')[['card_card_name', 'price_mean', 'price_count']]
        print(f"\nTop 5 cards by average price:")
        print(top_cards.to_string(index=False))

if __name__ == "__main__":
    main() 