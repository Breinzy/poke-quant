-- Sealed Products Enhancements
-- Additional useful features now that basic tables exist

-- 1. Combined view (now that both tables exist, with proper type casting)
CREATE OR REPLACE VIEW all_ebay_listings AS
SELECT 
    'card' as listing_type,
    id,
    title,
    price,
    condition,
    sold_date,
    listing_url,
    image_url,
    search_terms,
    created_at,
    condition_category,
    search_strategy,
    grade_numeric,
    card_id::TEXT as product_id,
    (SELECT CONCAT(card_name, ' - ', set_name) FROM pokemon_cards WHERE id = card_id) as product_description
FROM ebay_sold_listings
WHERE card_id IS NOT NULL

UNION ALL

SELECT 
    'sealed' as listing_type,
    id,
    title,
    price,
    condition,
    sold_date,
    listing_url,
    image_url,
    search_terms,
    created_at,
    condition_category,
    search_strategy,
    grade_numeric,
    sealed_product_id::TEXT as product_id,
    (SELECT CONCAT(product_name, ' (', product_type, ')') FROM sealed_products WHERE id = sealed_product_id) as product_description
FROM ebay_sealed_listings
WHERE sealed_product_id IS NOT NULL;

-- 2. Market summary table for sealed products (similar to cards)
CREATE TABLE IF NOT EXISTS sealed_market_summary (
    id BIGSERIAL PRIMARY KEY,
    sealed_product_id BIGINT REFERENCES sealed_products(id) UNIQUE,
    avg_price DECIMAL(10,2),
    lowest_price DECIMAL(10,2),
    highest_price DECIMAL(10,2),
    total_sales INTEGER DEFAULT 0,
    sales_last_30_days INTEGER DEFAULT 0,
    price_trend VARCHAR, -- 'rising', 'falling', 'stable'
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Investment tracking table (for portfolio management)
CREATE TABLE IF NOT EXISTS investment_targets (
    id BIGSERIAL PRIMARY KEY,
    target_type VARCHAR NOT NULL, -- 'card' or 'sealed'
    target_id TEXT NOT NULL, -- card_id or sealed_product_id (as text to handle both)
    target_name VARCHAR NOT NULL,
    investment_category VARCHAR, -- 'high_value', 'emerging', 'stable', 'speculative'
    watch_priority INTEGER DEFAULT 1, -- 1=highest, 5=lowest
    target_buy_price DECIMAL(10,2), -- Price we want to buy at
    target_sell_price DECIMAL(10,2), -- Price we want to sell at
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(target_type, target_id)
);

-- 4. Useful indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_sold_date ON ebay_sealed_listings(sold_date);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_condition_category ON ebay_sealed_listings(condition_category);
CREATE INDEX IF NOT EXISTS idx_investment_targets_category ON investment_targets(investment_category);
CREATE INDEX IF NOT EXISTS idx_investment_targets_priority ON investment_targets(watch_priority);

-- 5. Populate investment targets with our curated list
INSERT INTO investment_targets (target_type, target_id, target_name, investment_category, watch_priority) VALUES
-- High-value sealed products
('sealed', '1', 'Brilliant Stars Booster Box', 'high_value', 1),
('sealed', '3', 'Evolving Skies Booster Box', 'high_value', 1),
('sealed', '9', 'Base Set Booster Box', 'high_value', 1),

-- Emerging sealed products
('sealed', '5', 'Silver Tempest Booster Box', 'emerging', 2),
('sealed', '7', 'Lost Origin Booster Box', 'emerging', 2),

-- Elite Trainer Boxes (stable investments)
('sealed', '2', 'Brilliant Stars Elite Trainer Box', 'stable', 3),
('sealed', '4', 'Evolving Skies Elite Trainer Box', 'stable', 3)

ON CONFLICT (target_type, target_id) DO NOTHING;

-- 6. Useful functions for analysis
CREATE OR REPLACE FUNCTION get_recent_sealed_sales(product_id BIGINT, days INTEGER DEFAULT 30)
RETURNS TABLE(
    title VARCHAR,
    price DECIMAL,
    sold_date TIMESTAMP WITH TIME ZONE,
    condition VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        esl.title,
        esl.price,
        esl.sold_date,
        esl.condition
    FROM ebay_sealed_listings esl
    WHERE esl.sealed_product_id = product_id
      AND esl.sold_date >= NOW() - INTERVAL '1 day' * days
    ORDER BY esl.sold_date DESC;
END;
$$ LANGUAGE plpgsql;

-- 7. Function to get price summary for any product (card or sealed)
CREATE OR REPLACE FUNCTION get_price_summary(product_type VARCHAR, product_id TEXT)
RETURNS TABLE(
    avg_price DECIMAL,
    min_price DECIMAL,
    max_price DECIMAL,
    total_sales INTEGER,
    recent_sales INTEGER
) AS $$
BEGIN
    IF product_type = 'card' THEN
        RETURN QUERY
        SELECT 
            AVG(price)::DECIMAL as avg_price,
            MIN(price)::DECIMAL as min_price,
            MAX(price)::DECIMAL as max_price,
            COUNT(*)::INTEGER as total_sales,
            COUNT(CASE WHEN sold_date >= NOW() - INTERVAL '30 days' THEN 1 END)::INTEGER as recent_sales
        FROM ebay_sold_listings
        WHERE card_id::TEXT = product_id;
    ELSE
        RETURN QUERY
        SELECT 
            AVG(price)::DECIMAL as avg_price,
            MIN(price)::DECIMAL as min_price,
            MAX(price)::DECIMAL as max_price,
            COUNT(*)::INTEGER as total_sales,
            COUNT(CASE WHEN sold_date >= NOW() - INTERVAL '30 days' THEN 1 END)::INTEGER as recent_sales
        FROM ebay_sealed_listings
        WHERE sealed_product_id::TEXT = product_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 8. Test query to verify everything is working
-- SELECT 
--     listing_type,
--     COUNT(*) as listing_count,
--     AVG(price) as avg_price,
--     MIN(price) as min_price,
--     MAX(price) as max_price
-- FROM all_ebay_listings 
-- GROUP BY listing_type; 