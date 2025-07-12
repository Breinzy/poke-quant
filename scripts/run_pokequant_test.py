#!/usr/bin/env python3
"""
Clean PokeQuant Test Pipeline
Works from root directory without path manipulation
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Set up the Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
ebay_scraper_dir = os.path.join(current_dir, 'ebay-scraper')
quant_dir = os.path.join(current_dir, 'quant')

sys.path.insert(0, ebay_scraper_dir)
sys.path.insert(0, quant_dir)

# Now we can import cleanly
try:
    from card_selector import CardSelector
    from targeted_scraper import TargetedeBayScraper
    from enhanced_pokequant_main import EnhancedPokeQuantOrchestrator
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required dependencies are installed.")
    sys.exit(1)

load_dotenv()

class CleanPokeQuantPipeline:
    """Clean pipeline for PokeQuant testing"""
    
    def __init__(self):
        self.start_time = datetime.now()
        try:
            self.card_selector = CardSelector()
            self.targeted_scraper = TargetedeBayScraper()
            self.pokequant = EnhancedPokeQuantOrchestrator()
            self.log("✅ Pipeline initialized successfully")
        except Exception as e:
            self.log(f"❌ Failed to initialize pipeline: {e}", "ERROR")
            raise
    
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def ensure_product_exists(self, product_name: str, product_type: str = "card") -> Optional[Dict[str, Any]]:
        """Ensure product exists in database, create if needed"""
        
        try:
            if product_type == "card":
                # Search for existing card
                result = self.card_selector.supabase.table('pokemon_cards').select('*').ilike('card_name', f'%{product_name.split()[0]}%').execute()
                
                if result.data:
                    product = result.data[0]
                    self.log(f"✅ Found existing card: {product['card_name']}")
                    return product
                else:
                    # Create new card
                    card_data = {
                        'card_name': product_name,
                        'set_name': '151' if '151' in product_name else 'Unknown',
                        'card_number': '1',
                        'rarity': 'Rare'
                    }
                    
                    insert_result = self.card_selector.supabase.table('pokemon_cards').insert(card_data).execute()
                    if insert_result.data:
                        product = insert_result.data[0]
                        self.log(f"✅ Created new card: {product_name}")
                        return product
                    
            elif product_type == "sealed":
                # Search for existing sealed product
                result = self.card_selector.supabase.table('sealed_products').select('*').ilike('product_name', f'%{product_name.split()[0]}%').execute()
                
                if result.data:
                    product = result.data[0]
                    self.log(f"✅ Found existing sealed product: {product['product_name']}")
                    return product
                else:
                    # Create new sealed product
                    product_data = {
                        'product_name': product_name,
                        'set_name': '151' if '151' in product_name else 'Unknown',
                        'product_type': 'Elite Trainer Box' if 'Elite Trainer Box' in product_name else 'Booster Box',
                        'msrp': 49.99 if 'Elite Trainer Box' in product_name else 143.64
                    }
                    
                    insert_result = self.card_selector.supabase.table('sealed_products').insert(product_data).execute()
                    if insert_result.data:
                        product = insert_result.data[0]
                        self.log(f"✅ Created new sealed product: {product_name}")
                        return product
                        
        except Exception as e:
            self.log(f"❌ Error handling product {product_name}: {e}", "ERROR")
            return None
        
        return None
    
    def scrape_product_data(self, product_name: str, product_type: str = "card") -> Dict[str, Any]:
        """Scrape data for a specific product"""
        
        self.log(f"🔍 Scraping data for {product_type}: {product_name}")
        
        # Ensure product exists in database
        product = self.ensure_product_exists(product_name, product_type)
        if not product:
            return {"error": f"Could not find or create product: {product_name}"}
        
        # Prepare search term
        search_term = f"{product_name} pokemon"
        
        try:
            if product_type == "card":
                result = self.targeted_scraper._process_single_card(product, search_term)
            elif product_type == "sealed":
                result = self.targeted_scraper._process_single_sealed_product(product, search_term)
            else:
                return {"error": f"Unknown product type: {product_type}"}
            
            if result.get('success'):
                self.log(f"✅ Successfully scraped {result.get('uploaded_count', 0)} listings")
                return {
                    "success": True,
                    "uploaded_count": result.get('uploaded_count', 0),
                    "total_listings": result.get('total_listings', 0),
                    "product_id": product.get('id')
                }
            else:
                return {"error": f"Scraping failed: {result.get('error', 'Unknown error')}"}
                
        except Exception as e:
            self.log(f"❌ Scraping error: {e}", "ERROR")
            return {"error": str(e)}
    
    def analyze_product(self, product_name: str) -> Dict[str, Any]:
        """Run enhanced PokeQuant analysis"""
        
        self.log(f"📊 Analyzing product: {product_name}")
        
        try:
            # Run enhanced analysis
            analysis_result = self.pokequant.analyze_product(product_name)
            
            if analysis_result.get('error'):
                self.log(f"❌ Analysis failed: {analysis_result['error']}", "ERROR")
                return analysis_result
            
            # Log key results
            metrics = analysis_result.get('quantitative_analysis', {})
            recommendation = analysis_result.get('recommendation', 'N/A')
            confidence = analysis_result.get('confidence_score', 0)
            
            self.log(f"✅ Analysis complete: {recommendation} (Confidence: {confidence:.1f})")
            
            if 'cagr' in metrics:
                cagr = metrics['cagr'] * 100
                self.log(f"   💰 CAGR: {cagr:.1f}%")
            
            if 'sharpe_ratio' in metrics:
                sharpe = metrics['sharpe_ratio']
                self.log(f"   📊 Sharpe Ratio: {sharpe:.2f}")
            
            return analysis_result
            
        except Exception as e:
            self.log(f"❌ Analysis error: {e}", "ERROR")
            return {"error": str(e)}
    
    def run_complete_pipeline(self, card_name: Optional[str] = None, sealed_product: Optional[str] = None) -> Dict[str, Any]:
        """Run complete pipeline for specified products"""
        
        self.log("🚀 STARTING COMPLETE POKEQUANT PIPELINE")
        self.log("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "products_processed": [],
            "scraping_results": {},
            "analysis_results": {},
            "summary": {}
        }
        
        # Process card if provided
        if card_name:
            self.log(f"\n📄 Processing card: {card_name}")
            
            # Step 1: Scrape data
            scraping_result = self.scrape_product_data(card_name, "card")
            results["scraping_results"][card_name] = scraping_result
            
            # Step 2: Analyze data
            if scraping_result.get("success"):
                analysis_result = self.analyze_product(card_name)
                results["analysis_results"][card_name] = analysis_result
            else:
                results["analysis_results"][card_name] = {"error": "Scraping failed"}
            
            results["products_processed"].append({"name": card_name, "type": "card"})
        
        # Process sealed product if provided
        if sealed_product:
            self.log(f"\n📦 Processing sealed product: {sealed_product}")
            
            # Step 1: Scrape data
            scraping_result = self.scrape_product_data(sealed_product, "sealed")
            results["scraping_results"][sealed_product] = scraping_result
            
            # Step 2: Analyze data
            if scraping_result.get("success"):
                analysis_result = self.analyze_product(sealed_product)
                results["analysis_results"][sealed_product] = analysis_result
            else:
                results["analysis_results"][sealed_product] = {"error": "Scraping failed"}
            
            results["products_processed"].append({"name": sealed_product, "type": "sealed"})
        
        # Generate summary
        self.generate_summary(results)
        
        # Save results
        self.save_results(results)
        
        return results
    
    def generate_summary(self, results: Dict[str, Any]):
        """Generate and log summary"""
        
        total_time = datetime.now() - self.start_time
        
        self.log("\n🎯 PIPELINE SUMMARY")
        self.log("=" * 60)
        self.log(f"Total execution time: {total_time}")
        
        successful_analyses = 0
        failed_analyses = 0
        
        for product_name, analysis_result in results["analysis_results"].items():
            if analysis_result.get('error'):
                self.log(f"❌ {product_name}: {analysis_result['error']}")
                failed_analyses += 1
            else:
                recommendation = analysis_result.get('recommendation', 'N/A')
                confidence = analysis_result.get('confidence_score', 0)
                self.log(f"✅ {product_name}: {recommendation} (Confidence: {confidence:.1f})")
                successful_analyses += 1
        
        results["summary"] = {
            "execution_time": str(total_time),
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "total_products": len(results["products_processed"])
        }
        
        self.log(f"\n📈 Results: {successful_analyses} successful, {failed_analyses} failed")
        
        if successful_analyses > 0:
            self.log("🎉 Pipeline completed successfully!")
        else:
            self.log("⚠️ Pipeline completed with issues")
    
    def save_results(self, results: Dict[str, Any]):
        """Save results to file"""
        
        output_file = f"pokequant_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.log(f"📁 Results saved to: {output_file}")
            
        except Exception as e:
            self.log(f"❌ Failed to save results: {e}", "ERROR")


def main():
    """Main function"""
    
    print("🧪 Clean PokeQuant Pipeline Test")
    print("Testing with: Mew ex 151 + 151 Elite Trainer Box")
    print()
    
    try:
        pipeline = CleanPokeQuantPipeline()
        
        # Run the complete pipeline
        results = pipeline.run_complete_pipeline(
            card_name="Mew ex 151",
            sealed_product="151 Elite Trainer Box"
        )
        
        if results.get('summary', {}).get('successful_analyses', 0) > 0:
            print("\n✅ Pipeline test completed successfully!")
            return 0
        else:
            print("\n❌ Pipeline test failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Pipeline crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 