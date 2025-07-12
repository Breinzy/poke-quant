-- Database Schema for Sealed Products Support (CORRECTED)
-- User will apply these changes manually

-- 1. Create sealed_products table
CREATE TABLE IF NOT EXISTS sealed_products (
    id BIGSERIAL PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    set_name VARCHAR NOT NULL,
    product_type VARCHAR NOT NULL, -- 'Booster Box', 'Elite Trainer Box', 'Collection Box', etc.
    release_date DATE,
    msrp DECIMAL(10,2), -- Manufacturer's Suggested Retail Price
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicates
    UNIQUE(product_name, set_name, product_type)
);

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sealed_products_set_name ON sealed_products(set_name);
CREATE INDEX IF NOT EXISTS idx_sealed_products_product_type ON sealed_products(product_type);
CREATE INDEX IF NOT EXISTS idx_sealed_products_product_name ON sealed_products(product_name);

-- 3. Create table for eBay listings of sealed products (matching structure of ebay_sold_listings)
CREATE TABLE IF NOT EXISTS ebay_sealed_listings (
    id BIGSERIAL PRIMARY KEY,
    sealed_product_id BIGINT REFERENCES sealed_products(id),
    
    -- Core listing fields (matching ebay_sold_listings structure)
    title VARCHAR NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    listing_url TEXT NOT NULL,
    search_terms VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Enhanced fields from Phase 6
    condition_category VARCHAR, -- 'graded', 'raw', 'sealed'
    search_strategy VARCHAR,    -- 'psa_10', 'psa_9', 'raw_nm', 'sealed_box'
    grade_numeric INTEGER,      -- Numeric grade for sorting (NULL for sealed)
    
    -- Optional fields
    condition VARCHAR,
    is_graded BOOLEAN DEFAULT false,
    grading_company VARCHAR,
    grade VARCHAR,
    image_url TEXT,
    is_auction BOOLEAN DEFAULT false,
    bids INTEGER DEFAULT 0,
    shipping VARCHAR,
    sold_date TIMESTAMP WITH TIME ZONE,
    
    -- Quality metrics
    quality_score DECIMAL(3,2), -- 0.00 to 1.00
    is_authentic BOOLEAN DEFAULT true
);

-- 4. Create indexes for ebay_sealed_listings
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_product_id ON ebay_sealed_listings(sealed_product_id);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_sold_date ON ebay_sealed_listings(sold_date);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_price ON ebay_sealed_listings(price);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_created_at ON ebay_sealed_listings(created_at);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_condition_category ON ebay_sealed_listings(condition_category);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_search_strategy ON ebay_sealed_listings(search_strategy);

-- 5. Insert initial sealed products data
INSERT INTO sealed_products (product_name, set_name, product_type, msrp) VALUES
-- Brilliant Stars
('Brilliant Stars Booster Box', 'Brilliant Stars', 'Booster Box', 143.64),
('Brilliant Stars Elite Trainer Box', 'Brilliant Stars', 'Elite Trainer Box', 49.99),

-- Evolving Skies  
('Evolving Skies Booster Box', 'Evolving Skies', 'Booster Box', 143.64),
('Evolving Skies Elite Trainer Box', 'Evolving Skies', 'Elite Trainer Box', 49.99),

-- Silver Tempest
('Silver Tempest Booster Box', 'Silver Tempest', 'Booster Box', 143.64),
('Silver Tempest Elite Trainer Box', 'Silver Tempest', 'Elite Trainer Box', 49.99),

-- Lost Origin
('Lost Origin Booster Box', 'Lost Origin', 'Booster Box', 143.64),
('Lost Origin Elite Trainer Box', 'Lost Origin', 'Elite Trainer Box', 49.99),

-- Vintage Base Set
('Base Set Booster Box', 'Base Set', 'Booster Box', NULL), -- No MSRP for vintage
('Base Set 1st Edition Booster Box', 'Base Set', 'Booster Box (1st Edition)', NULL)

ON CONFLICT (product_name, set_name, product_type) DO NOTHING;

-- 6. Create view for combined listings (cards + sealed products)
-- CORRECTED: Only using columns that exist in both tables
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
    quality_score,
    created_at,
    condition_category,
    search_strategy,
    grade_numeric,
    card_id as product_id,
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
    quality_score,
    created_at,
    condition_category,
    search_strategy,
    grade_numeric,
    sealed_product_id as product_id,
    (SELECT CONCAT(product_name, ' (', product_type, ')') FROM sealed_products WHERE id = sealed_product_id) as product_description
FROM ebay_sealed_listings
WHERE sealed_product_id IS NOT NULL;

-- 7. Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Only create trigger if it doesn't exist
DROP TRIGGER IF EXISTS update_sealed_products_updated_at ON sealed_products;
CREATE TRIGGER update_sealed_products_updated_at 
    BEFORE UPDATE ON sealed_products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. Create a simple query to test the schema
-- SELECT 'Cards: ' || COUNT(*) FROM ebay_sold_listings 
-- UNION ALL 
-- SELECT 'Sealed: ' || COUNT(*) FROM ebay_sealed_listings
-- UNION ALL
-- SELECT 'Products: ' || COUNT(*) FROM sealed_products; 