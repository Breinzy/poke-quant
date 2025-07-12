#!/usr/bin/env python3
"""
PriceCharting Data Collector
Focused script to collect price chart data for our curated investment targets
"""

import sys
import os
import time
import json
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from card_selector import CardSelector
from pricecharting_scraper import PriceChartingScraper

class PriceChartingDataCollector:
    """Collect PriceCharting data for all curated targets"""
    
    def __init__(self):
        self.card_selector = CardSelector()
        self.pricecharting_scraper = PriceChartingScraper()
        
        # Progress tracking
        self.total_targets = 0
        self.successful_collections = 0
        self.failed_collections = 0
        self.collected_data = []
        
    def collect_all_curated_data(self) -> Dict[str, Any]:
        """Collect PriceCharting data for all curated targets"""
        
        print(f"📊 PRICECHARTING DATA COLLECTION")
        print(f"{'='*60}")
        
        # Get our curated targets
        print("💎 Getting curated investment targets...")
        cards = self.card_selector.get_curated_investment_targets()
        sealed_products = self.card_selector.get_sealed_products_list()
        
        all_targets = cards + sealed_products
        self.total_targets = len(all_targets)
        
        print(f"💎 Found {len(cards)} cards + {len(sealed_products)} sealed products = {self.total_targets} total targets")
        print()
        
        # Process each target
        for i, target in enumerate(all_targets, 1):
            target_name = target.get('card_name', target.get('product_name', 'Unknown'))
            target_type = 'card' if 'card_name' in target else 'sealed_product'
            
            print(f"🎯 [{i}/{self.total_targets}] Processing: {target_name} ({target_type})")
            
            try:
                # Search for the target on PriceCharting
                if target_type == 'card':
                    pricecharting_url = self.pricecharting_scraper.search_card_on_pricecharting(
                        target.get('card_name', ''),
                        target.get('set_name', ''),
                        target
                    )
                else:
                    pricecharting_url = self.pricecharting_scraper.search_sealed_product_on_pricecharting(
                        target.get('product_name', '')
                    )
                
                if pricecharting_url:
                    print(f"  ✅ Found PriceCharting page: {pricecharting_url}")
                    
                    # Scrape the price history data
                    price_data = self.pricecharting_scraper.scrape_price_history(pricecharting_url)
                    
                    if price_data:
                        # Add metadata
                        price_data['target_info'] = target
                        price_data['target_type'] = target_type
                        price_data['collection_timestamp'] = datetime.now().isoformat()
                        
                        self.collected_data.append(price_data)
                        self.successful_collections += 1
                        
                        print(f"  ✅ Successfully collected data:")
                        print(f"    Current prices: {len(price_data.get('current_prices', {}))}")
                        print(f"    Chart data points: {len(price_data.get('historical_chart_data', []))}")
                        print(f"    Price tables: {len(price_data.get('price_tables', []))}")
                        
                        # Show sample of clean historical data
                        historical_data = price_data.get('historical_chart_data', [])
                        if historical_data:
                            sample_data = historical_data[:3]  # Show first 3 entries
                            print(f"    Sample historical data:")
                            for entry in sample_data:
                                if isinstance(entry, dict) and 'date' in entry and 'price' in entry:
                                    print(f"      {entry['date']}: ${entry['price']}")
                        
                        # Show clean price table data
                        price_tables = price_data.get('price_tables', [])
                        total_clean_entries = sum(len(table.get('clean_price_data', [])) for table in price_tables)
                        if total_clean_entries > 0:
                            print(f"    Clean table entries: {total_clean_entries}")
                            
                            # Show sample from tables
                            for table in price_tables[:1]:  # Show first table
                                clean_data = table.get('clean_price_data', [])
                                if clean_data:
                                    print(f"    Sample table data:")
                                    for entry in clean_data[:3]:  # Show first 3
                                        print(f"      {entry['date']}: ${entry['price']}")
                                    break
                    else:
                        print(f"  ❌ Failed to scrape price data")
                        self.failed_collections += 1
                else:
                    print(f"  ❌ No PriceCharting page found")
                    self.failed_collections += 1
                    
            except Exception as e:
                print(f"  ❌ Error processing {target_name}: {e}")
                self.failed_collections += 1
            
            # Rate limiting between targets
            if i < self.total_targets:
                print(f"  ⏳ Waiting 3s before next target...")
                time.sleep(3)
                print()
        
        # Save all collected data
        results = self._save_collected_data()
        self._print_summary(results)
        
        return results
    
    def _save_collected_data(self) -> Dict[str, Any]:
        """Save all collected data to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create data directory
        os.makedirs("data/pricecharting", exist_ok=True)
        
        # Save comprehensive data
        comprehensive_filename = f"data/pricecharting/comprehensive_collection_{timestamp}.json"
        
        comprehensive_data = {
            'collection_metadata': {
                'timestamp': timestamp,
                'total_targets': self.total_targets,
                'successful_collections': self.successful_collections,
                'failed_collections': self.failed_collections,
                'success_rate': (self.successful_collections / self.total_targets) * 100 if self.total_targets > 0 else 0
            },
            'collected_data': self.collected_data
        }
        
        try:
            with open(comprehensive_filename, 'w') as f:
                json.dump(comprehensive_data, f, indent=2, default=str)
            print(f"📄 Comprehensive data saved: {comprehensive_filename}")
        except Exception as e:
            print(f"⚠️ Could not save comprehensive data: {e}")
        
        # Save summary data (prices only)
        summary_filename = f"data/pricecharting/price_summary_{timestamp}.json"
        
        summary_data = []
        for item in self.collected_data:
            target_info = item.get('target_info', {})
            
            # Count clean historical data
            historical_data = item.get('historical_chart_data', [])
            clean_historical_count = sum(1 for entry in historical_data 
                                       if isinstance(entry, dict) and 'date' in entry and 'price' in entry)
            
            # Count clean table data
            price_tables = item.get('price_tables', [])
            clean_table_count = sum(len(table.get('clean_price_data', [])) for table in price_tables)
            
            # Filter current prices (remove subscription fees)
            current_prices = item.get('current_prices', {})
            filtered_prices = {k: v for k, v in current_prices.items() 
                             if v != 6.0 and v >= 1.0 and v <= 100000}
            
            summary_item = {
                'name': target_info.get('card_name', target_info.get('product_name', 'Unknown')),
                'type': item.get('target_type', 'unknown'),
                'url': item.get('url', ''),
                'current_prices': filtered_prices,
                'current_prices_count': len(filtered_prices),
                'historical_data_count': clean_historical_count,
                'table_data_count': clean_table_count,
                'total_clean_data_points': clean_historical_count + clean_table_count,
                'chart_data_count': len(item.get('historical_chart_data', [])),
                'price_tables_count': len(item.get('price_tables', [])),
                'scraped_at': item.get('scraped_at', '')
            }
            summary_data.append(summary_item)
        
        try:
            with open(summary_filename, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            print(f"📄 Summary data saved: {summary_filename}")
        except Exception as e:
            print(f"⚠️ Could not save summary data: {e}")
        
        return comprehensive_data
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print collection summary"""
        
        print(f"\n{'='*60}")
        print("📊 PRICECHARTING COLLECTION COMPLETE")
        print(f"{'='*60}")
        
        metadata = results.get('collection_metadata', {})
        
        print(f"📈 SUMMARY:")
        print(f"  Total targets: {metadata.get('total_targets', 0)}")
        print(f"  Successful collections: {metadata.get('successful_collections', 0)}")
        print(f"  Failed collections: {metadata.get('failed_collections', 0)}")
        print(f"  Success rate: {metadata.get('success_rate', 0):.1f}%")
        
        if self.collected_data:
            print(f"\n📊 COLLECTED DATA:")
            
            # Calculate clean data statistics
            total_filtered_prices = 0
            total_clean_historical = 0
            total_clean_table_data = 0
            
            for item in self.collected_data:
                # Count filtered current prices
                current_prices = item.get('current_prices', {})
                filtered_prices = {k: v for k, v in current_prices.items() 
                                 if v != 6.0 and v >= 1.0 and v <= 100000}
                total_filtered_prices += len(filtered_prices)
                
                # Count clean historical data
                historical_data = item.get('historical_chart_data', [])
                clean_historical = sum(1 for entry in historical_data 
                                     if isinstance(entry, dict) and 'date' in entry and 'price' in entry)
                total_clean_historical += clean_historical
                
                # Count clean table data  
                price_tables = item.get('price_tables', [])
                clean_table_data = sum(len(table.get('clean_price_data', [])) for table in price_tables)
                total_clean_table_data += clean_table_data
            
            total_prices = sum(len(item.get('current_prices', {})) for item in self.collected_data)
            total_chart_points = sum(len(item.get('historical_chart_data', [])) for item in self.collected_data)
            total_tables = sum(len(item.get('price_tables', [])) for item in self.collected_data)
            
            print(f"  Raw data collected:")
            print(f"    Total current prices: {total_prices}")
            print(f"    Total chart data points: {total_chart_points}")
            print(f"    Total price tables: {total_tables}")
            
            print(f"  Clean data (filtered):")
            print(f"    Filtered current prices: {total_filtered_prices} (removed {total_prices - total_filtered_prices} subscription fees)")
            print(f"    Clean historical entries: {total_clean_historical}")
            print(f"    Clean table entries: {total_clean_table_data}")
            print(f"    Total clean data points: {total_clean_historical + total_clean_table_data}")
            
            # Show top items by clean data richness
            data_richness = []
            for item in self.collected_data:
                name = item.get('target_info', {}).get('card_name', item.get('target_info', {}).get('product_name', 'Unknown'))
                
                # Count clean data
                historical_data = item.get('historical_chart_data', [])
                clean_historical = sum(1 for entry in historical_data 
                                     if isinstance(entry, dict) and 'date' in entry and 'price' in entry)
                
                price_tables = item.get('price_tables', [])
                clean_table_data = sum(len(table.get('clean_price_data', [])) for table in price_tables)
                
                total_clean = clean_historical + clean_table_data
                data_richness.append((name, total_clean))
            
            data_richness.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\n🏆 TOP CLEAN DATA COLLECTIONS:")
            for i, (name, data_count) in enumerate(data_richness[:5], 1):
                print(f"  {i}. {name}: {data_count} clean data points")
        
        print(f"\n💾 DATA FILES:")
        print(f"  • Comprehensive: data/pricecharting/comprehensive_collection_*.json")
        print(f"  • Summary: data/pricecharting/price_summary_*.json")
        
        print(f"{'='*60}")

def main():
    """Run PriceCharting data collection"""
    
    print("🚀 Starting PriceCharting Data Collection...")
    
    collector = PriceChartingDataCollector()
    
    try:
        results = collector.collect_all_curated_data()
        
        if results['collection_metadata']['successful_collections'] > 0:
            print(f"\n🎉 SUCCESS: Collected data for {results['collection_metadata']['successful_collections']} targets")
        else:
            print(f"\n⚠️ No data was collected")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")

if __name__ == "__main__":
    main() 