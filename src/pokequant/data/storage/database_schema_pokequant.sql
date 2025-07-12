-- PokeQuant Database Schema
-- Additional tables for quantitative analysis of Pokemon cards and sealed products

-- 1. Products table for PokeQuant tracking
CREATE TABLE IF NOT EXISTS pokequant_products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    product_type VARCHAR NOT NULL, -- 'card' or 'sealed'
    product_id VARCHAR NOT NULL,   -- card_id or sealed_product_id (as string for flexibility)
    product_name VARCHAR NOT NULL,
    set_name VARCHAR,
    last_data_update TIMESTAMP WITH TIME ZONE,
    last_analysis_run TIMESTAMP WITH TIME ZONE,
    data_quality_score DECIMAL(3,2), -- 0.00 to 1.00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique product identification
    UNIQUE(product_type, product_id)
);

-- 2. Price series table for storing aggregated price data
CREATE TABLE IF NOT EXISTS pokequant_price_series (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pokequant_product_id UUID REFERENCES pokequant_products(id) ON DELETE CASCADE,
    price_date DATE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    source VARCHAR NOT NULL, -- 'ebay', 'pricecharting'
    condition_category VARCHAR, -- 'raw', 'graded', 'sealed'
    data_confidence DECIMAL(3,2) DEFAULT 1.00, -- 0.00 to 1.00
    listing_count INTEGER DEFAULT 1, -- Number of listings averaged for this price point
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure no duplicate price points for same product/date/source/condition
    UNIQUE(pokequant_product_id, price_date, source, condition_category)
);

-- 3. Analysis results table for storing quantitative analysis
CREATE TABLE IF NOT EXISTS pokequant_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pokequant_product_id UUID REFERENCES pokequant_products(id) ON DELETE CASCADE,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metrics JSONB NOT NULL, -- Store all calculated metrics
    recommendation VARCHAR, -- 'BUY', 'HOLD', 'SELL', 'AVOID'
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    analysis_version VARCHAR DEFAULT '1.0',
    data_range_start DATE,
    data_range_end DATE,
    total_data_points INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_pokequant_products_type_id ON pokequant_products(product_type, product_id);
CREATE INDEX IF NOT EXISTS idx_pokequant_products_name ON pokequant_products(product_name);
CREATE INDEX IF NOT EXISTS idx_pokequant_products_set ON pokequant_products(set_name);
CREATE INDEX IF NOT EXISTS idx_pokequant_products_last_update ON pokequant_products(last_data_update);

CREATE INDEX IF NOT EXISTS idx_pokequant_price_series_product ON pokequant_price_series(pokequant_product_id);
CREATE INDEX IF NOT EXISTS idx_pokequant_price_series_date ON pokequant_price_series(price_date);
CREATE INDEX IF NOT EXISTS idx_pokequant_price_series_source ON pokequant_price_series(source);
CREATE INDEX IF NOT EXISTS idx_pokequant_price_series_product_date ON pokequant_price_series(pokequant_product_id, price_date);

CREATE INDEX IF NOT EXISTS idx_pokequant_analyses_product ON pokequant_analyses(pokequant_product_id);
CREATE INDEX IF NOT EXISTS idx_pokequant_analyses_date ON pokequant_analyses(analysis_date);
CREATE INDEX IF NOT EXISTS idx_pokequant_analyses_recommendation ON pokequant_analyses(recommendation);

-- 5. Create updated_at trigger for pokequant_products
CREATE OR REPLACE FUNCTION update_pokequant_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_pokequant_products_updated_at 
    BEFORE UPDATE ON pokequant_products 
    FOR EACH ROW EXECUTE FUNCTION update_pokequant_updated_at_column();

-- 6. Helpful views for common queries
CREATE OR REPLACE VIEW pokequant_latest_analyses AS
SELECT DISTINCT ON (pokequant_product_id) 
    pa.*,
    pp.product_name,
    pp.set_name,
    pp.product_type
FROM pokequant_analyses pa
JOIN pokequant_products pp ON pa.pokequant_product_id = pp.id
ORDER BY pokequant_product_id, analysis_date DESC;

CREATE OR REPLACE VIEW pokequant_product_summary AS
SELECT 
    pp.*,
    COUNT(ps.id) as total_price_points,
    MIN(ps.price_date) as earliest_price_date,
    MAX(ps.price_date) as latest_price_date,
    AVG(ps.price) as avg_price,
    MIN(ps.price) as min_price,
    MAX(ps.price) as max_price,
    la.recommendation as latest_recommendation,
    la.confidence_score as latest_confidence,
    la.analysis_date as latest_analysis_date
FROM pokequant_products pp
LEFT JOIN pokequant_price_series ps ON pp.id = ps.pokequant_product_id
LEFT JOIN pokequant_latest_analyses la ON pp.id = la.pokequant_product_id
GROUP BY pp.id, la.recommendation, la.confidence_score, la.analysis_date;

-- 7. Insert some example data for testing
INSERT INTO pokequant_products (product_type, product_id, product_name, set_name) VALUES
('card', '1', 'Charizard V', 'Evolving Skies'),
('card', '2', 'Rayquaza VMAX', 'Evolving Skies'), 
('sealed', '1', 'Evolving Skies Booster Box', 'Evolving Skies')
ON CONFLICT (product_type, product_id) DO NOTHING;

-- 8. Comments for documentation
COMMENT ON TABLE pokequant_products IS 'Products tracked by PokeQuant for analysis';
COMMENT ON TABLE pokequant_price_series IS 'Aggregated price data from multiple sources';
COMMENT ON TABLE pokequant_analyses IS 'Quantitative analysis results and recommendations';

COMMENT ON COLUMN pokequant_products.product_type IS 'Either "card" or "sealed"';
COMMENT ON COLUMN pokequant_products.product_id IS 'References pokemon_cards.id or sealed_products.id';
COMMENT ON COLUMN pokequant_products.data_quality_score IS 'Quality score from 0.00 to 1.00 based on data completeness';

COMMENT ON COLUMN pokequant_price_series.source IS 'Data source: "ebay" or "pricecharting"';
COMMENT ON COLUMN pokequant_price_series.condition_category IS 'Condition grouping for analysis';
COMMENT ON COLUMN pokequant_price_series.data_confidence IS 'Confidence in this price point from 0.00 to 1.00';

COMMENT ON COLUMN pokequant_analyses.metrics IS 'JSON containing all calculated metrics (CAGR, volatility, etc.)';
COMMENT ON COLUMN pokequant_analyses.recommendation IS 'Investment recommendation: BUY, HOLD, SELL, or AVOID'; 