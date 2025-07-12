"""
Phase 6: Market Summary & Analytics
Calculates market insights and pricing analytics from scraped eBay data
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import statistics

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import supabase

class MarketAnalyzer:
    """Analyzes eBay market data and generates insights"""
    
    def __init__(self):
        self.supabase = supabase
        
    def calculate_card_market_summary(self, card_id: int) -> Dict[str, Any]:
        """Calculate comprehensive market summary for a specific card"""
        
        print(f"📊 Calculating market summary for card_id {card_id}...")
        
        try:
            # Get all listings for this card
            result = self.supabase.table("ebay_sold_listings").select("*").eq("card_id", card_id).execute()
            
            if not result.data:
                print(f"⚠️ No listings found for card {card_id}")
                return {}
            
            listings = result.data
            print(f"📈 Analyzing {len(listings)} listings...")
            
            # Separate by search strategy
            raw_listings = [l for l in listings if l.get('search_strategy') == 'raw_nm']
            psa9_listings = [l for l in listings if l.get('search_strategy') == 'psa_9']
            psa10_listings = [l for l in listings if l.get('search_strategy') == 'psa_10']
            
            print(f"   Raw: {len(raw_listings)}, PSA 9: {len(psa9_listings)}, PSA 10: {len(psa10_listings)}")
            
            # Calculate stats for each category
            raw_stats = self._calculate_price_stats(raw_listings, "raw")
            psa9_stats = self._calculate_price_stats(psa9_listings, "PSA 9")
            psa10_stats = self._calculate_price_stats(psa10_listings, "PSA 10")
            
            # Calculate overall stats
            all_prices = [float(l['price']) for l in listings if l.get('price') and float(l['price']) > 0]
            overall_stats = {
                'total_sold_listings': len(listings),  # Updated field name
                'avg_sold_price': statistics.mean(all_prices) if all_prices else 0,  # Updated field name
                'lowest_sold_price': min(all_prices) if all_prices else 0,  # Updated field name
                'highest_sold_price': max(all_prices) if all_prices else 0  # Updated field name
            }
            
            # Calculate grading premiums
            grading_premiums = self._calculate_grading_premiums(raw_stats, psa9_stats, psa10_stats)
            
            # Market liquidity assessment
            market_liquidity = self._assess_market_liquidity(listings)
            
            # Combine all stats
            summary = {
                'card_id': card_id,
                **overall_stats,
                **raw_stats,
                **psa9_stats,
                **psa10_stats,
                **grading_premiums,
                'market_liquidity': market_liquidity,
                'last_updated': datetime.now().isoformat()
            }
            
            print(f"✅ Market summary calculated for card {card_id}")
            return summary
            
        except Exception as e:
            print(f"❌ Error calculating market summary for card {card_id}: {e}")
            return {}
    
    def _calculate_price_stats(self, listings: List[Dict], category: str) -> Dict[str, Any]:
        """Calculate price statistics for a category of listings"""
        
        if not listings:
            return {
                f'{category.lower().replace(" ", "")}_sold_count': 0,  # Updated field name
                f'{category.lower().replace(" ", "")}_avg_price': 0,
                f'{category.lower().replace(" ", "")}_median_price': 0,
                f'{category.lower().replace(" ", "")}_lowest_price': 0,
                f'{category.lower().replace(" ", "")}_highest_price': 0
            }
        
        # Extract valid prices
        prices = []
        for listing in listings:
            price = listing.get('price')
            if price and float(price) > 0:
                prices.append(float(price))
        
        if not prices:
            return {
                f'{category.lower().replace(" ", "")}_sold_count': len(listings),  # Updated field name
                f'{category.lower().replace(" ", "")}_avg_price': 0,
                f'{category.lower().replace(" ", "")}_median_price': 0,
                f'{category.lower().replace(" ", "")}_lowest_price': 0,
                f'{category.lower().replace(" ", "")}_highest_price': 0
            }
        
        # Calculate statistics
        prefix = category.lower().replace(" ", "")
        return {
            f'{prefix}_sold_count': len(listings),  # Updated field name
            f'{prefix}_avg_price': round(statistics.mean(prices), 2),
            f'{prefix}_median_price': round(statistics.median(prices), 2),
            f'{prefix}_lowest_price': round(min(prices), 2),
            f'{prefix}_highest_price': round(max(prices), 2)
        }
    
    def _calculate_grading_premiums(self, raw_stats: Dict, psa9_stats: Dict, psa10_stats: Dict) -> Dict[str, Any]:
        """Calculate grading premiums over raw card prices"""
        
        raw_avg = raw_stats.get('raw_avg_price', 0)
        psa9_avg = psa9_stats.get('psa9_avg_price', 0)
        psa10_avg = psa10_stats.get('psa10_avg_price', 0)
        
        premiums = {}
        
        if raw_avg > 0:
            if psa9_avg > 0:
                premiums['grading_premium_psa9'] = round(((psa9_avg / raw_avg) - 1) * 100, 2)
            else:
                premiums['grading_premium_psa9'] = 0
                
            if psa10_avg > 0:
                premiums['grading_premium_psa10'] = round(((psa10_avg / raw_avg) - 1) * 100, 2)
            else:
                premiums['grading_premium_psa10'] = 0
        else:
            premiums['grading_premium_psa9'] = 0
            premiums['grading_premium_psa10'] = 0
        
        return premiums
    
    def _assess_market_liquidity(self, listings: List[Dict]) -> str:
        """Assess market liquidity based on number of recent sales"""
        
        # Count recent sales (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_sales = 0
        
        for listing in listings:
            sold_date = listing.get('sold_date')
            if sold_date:
                try:
                    if isinstance(sold_date, str):
                        sale_date = datetime.fromisoformat(sold_date.replace('Z', '+00:00'))
                    else:
                        sale_date = sold_date
                    
                    if sale_date >= thirty_days_ago:
                        recent_sales += 1
                except:
                    continue
        
        # Assess liquidity
        if recent_sales >= 20:
            return 'high'
        elif recent_sales >= 5:
            return 'medium'
        else:
            return 'low'
    
    def update_market_summary(self, card_id: int) -> bool:
        """Update market summary for a specific card in database"""
        
        print(f"🔄 Updating market summary for card {card_id}...")
        
        # Calculate new summary
        summary = self.calculate_card_market_summary(card_id)
        
        if not summary:
            print(f"❌ Could not calculate summary for card {card_id}")
            return False
        
        try:
            # Upsert summary (insert or update)
            result = self.supabase.table("ebay_market_summary").upsert(summary).execute()
            
            if result.data:
                print(f"✅ Market summary updated for card {card_id}")
                return True
            else:
                print(f"❌ Failed to update market summary for card {card_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating market summary for card {card_id}: {e}")
            return False
    
    def bulk_update_market_summaries(self, card_ids: List[int] = None) -> Dict[str, Any]:
        """Update market summaries for multiple cards"""
        
        if card_ids is None:
            # Get all cards that have listings
            print("🔍 Finding all cards with eBay listings...")
            try:
                result = self.supabase.table("ebay_sold_listings").select("card_id").execute()
                if result.data:
                    card_ids = list(set(row['card_id'] for row in result.data))
                    print(f"📊 Found {len(card_ids)} cards with listings")
                else:
                    print("⚠️ No cards found with listings")
                    return {'success': 0, 'failed': 0, 'total': 0}
            except Exception as e:
                print(f"❌ Error getting card list: {e}")
                return {'success': 0, 'failed': 0, 'total': 0}
        
        print(f"🚀 Bulk updating market summaries for {len(card_ids)} cards...")
        
        results = {
            'success': 0,
            'failed': 0,
            'total': len(card_ids),
            'failed_cards': []
        }
        
        for i, card_id in enumerate(card_ids, 1):
            print(f"\n📈 Processing card {i}/{len(card_ids)} (ID: {card_id})")
            
            if self.update_market_summary(card_id):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['failed_cards'].append(card_id)
        
        print(f"\n✅ Bulk update complete!")
        print(f"   Success: {results['success']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Total: {results['total']}")
        
        return results
    
    def generate_market_insights(self, limit: int = 20) -> Dict[str, Any]:
        """Generate market insights and top opportunities"""
        
        print("🔍 Generating market insights...")
        
        try:
            # Get market summary data
            result = self.supabase.table("ebay_market_summary").select("*").execute()
            
            if not result.data:
                print("⚠️ No market summary data found")
                return {}
            
            summaries = result.data
            print(f"📊 Analyzing {len(summaries)} card summaries...")
            
            # Filter valid data
            valid_summaries = [s for s in summaries if s.get('total_listings', 0) >= 3]
            
            insights = {
                'total_cards_analyzed': len(valid_summaries),
                'top_value_raw_cards': self._find_top_value_cards(valid_summaries, 'raw_avg_price', limit),
                'highest_psa10_premiums': self._find_highest_premiums(valid_summaries, 'grading_premium_psa10', limit),
                'highest_psa9_premiums': self._find_highest_premiums(valid_summaries, 'grading_premium_psa9', limit),
                'most_liquid_markets': self._find_most_liquid_markets(valid_summaries, limit),
                'market_overview': self._calculate_market_overview(valid_summaries),
                'generated_at': datetime.now().isoformat()
            }
            
            print("✅ Market insights generated")
            return insights
            
        except Exception as e:
            print(f"❌ Error generating market insights: {e}")
            return {}
    
    def _find_top_value_cards(self, summaries: List[Dict], price_field: str, limit: int) -> List[Dict]:
        """Find cards with best value (lowest prices)"""
        
        valid_cards = [s for s in summaries if s.get(price_field, 0) > 0]
        sorted_cards = sorted(valid_cards, key=lambda x: x.get(price_field, 0))
        
        return [{
            'card_id': card['card_id'],
            'avg_price': card.get(price_field, 0),
            'listings_count': card.get('total_listings', 0),
            'market_liquidity': card.get('market_liquidity', 'unknown')
        } for card in sorted_cards[:limit]]
    
    def _find_highest_premiums(self, summaries: List[Dict], premium_field: str, limit: int) -> List[Dict]:
        """Find cards with highest grading premiums"""
        
        valid_cards = [s for s in summaries if s.get(premium_field, 0) > 0]
        sorted_cards = sorted(valid_cards, key=lambda x: x.get(premium_field, 0), reverse=True)
        
        return [{
            'card_id': card['card_id'],
            'premium_percentage': card.get(premium_field, 0),
            'raw_price': card.get('raw_avg_price', 0),
            'graded_price': card.get('psa10_avg_price' if 'psa10' in premium_field else 'psa9_avg_price', 0),
            'listings_count': card.get('total_listings', 0)
        } for card in sorted_cards[:limit]]
    
    def _find_most_liquid_markets(self, summaries: List[Dict], limit: int) -> List[Dict]:
        """Find cards with most liquid markets (high sales volume)"""
        
        sorted_cards = sorted(summaries, key=lambda x: x.get('total_listings', 0), reverse=True)
        
        return [{
            'card_id': card['card_id'],
            'total_listings': card.get('total_listings', 0),
            'avg_price': card.get('avg_price', 0),
            'market_liquidity': card.get('market_liquidity', 'unknown')
        } for card in sorted_cards[:limit]]
    
    def _calculate_market_overview(self, summaries: List[Dict]) -> Dict[str, Any]:
        """Calculate overall market statistics"""
        
        total_listings = sum(s.get('total_listings', 0) for s in summaries)
        
        # Average premiums
        psa9_premiums = [s.get('grading_premium_psa9', 0) for s in summaries if s.get('grading_premium_psa9', 0) > 0]
        psa10_premiums = [s.get('grading_premium_psa10', 0) for s in summaries if s.get('grading_premium_psa10', 0) > 0]
        
        # Liquidity distribution
        liquidity_counts = {}
        for s in summaries:
            liquidity = s.get('market_liquidity', 'unknown')
            liquidity_counts[liquidity] = liquidity_counts.get(liquidity, 0) + 1
        
        return {
            'total_cards': len(summaries),
            'total_listings': total_listings,
            'avg_listings_per_card': round(total_listings / len(summaries), 1) if summaries else 0,
            'avg_psa9_premium': round(statistics.mean(psa9_premiums), 2) if psa9_premiums else 0,
            'avg_psa10_premium': round(statistics.mean(psa10_premiums), 2) if psa10_premiums else 0,
            'liquidity_distribution': liquidity_counts
        }

def main():
    """Command line interface for market analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="eBay Market Analyzer - Phase 6")
    parser.add_argument("--card-id", type=int, help="Analyze specific card")
    parser.add_argument("--update-all", action="store_true", help="Update all market summaries")
    parser.add_argument("--insights", action="store_true", help="Generate market insights")
    parser.add_argument("--limit", type=int, default=20, help="Limit for insights")
    
    args = parser.parse_args()
    
    analyzer = MarketAnalyzer()
    
    if args.card_id:
        # Update and analyze specific card
        analyzer.update_market_summary(args.card_id)
    elif args.update_all:
        # Update all market summaries
        results = analyzer.bulk_update_market_summaries()
        print(f"\n📊 BULK UPDATE RESULTS:")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
    elif args.insights:
        # Generate market insights
        insights = analyzer.generate_market_insights(args.limit)
        if insights:
            print(f"\n💡 MARKET INSIGHTS")
            print("=" * 50)
            overview = insights['market_overview']
            print(f"Total Cards: {overview['total_cards']}")
            print(f"Total Listings: {overview['total_listings']}")
            print(f"Avg PSA 10 Premium: {overview['avg_psa10_premium']:.1f}%")
    else:
        print("🚀 eBay Market Analyzer - Phase 6")
        print("Use --help to see available commands")

if __name__ == "__main__":
    main() 