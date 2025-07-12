-- Database Schema for Sealed Products Support
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

-- 3. Create table for eBay listings of sealed products
CREATE TABLE IF NOT EXISTS ebay_sealed_listings (
    id BIGSERIAL PRIMARY KEY,
    sealed_product_id BIGINT REFERENCES sealed_products(id),
    
    -- eBay listing details
    title VARCHAR NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    condition VARCHAR,
    sold_date TIMESTAMP WITH TIME ZONE,
    
    -- eBay metadata
    item_id VARCHAR UNIQUE,
    seller_name VARCHAR,
    listing_url TEXT,
    image_url TEXT,
    
    -- Search metadata
    search_term VARCHAR,
    page_number INTEGER,
    position_on_page INTEGER,
    
    -- Quality metrics
    quality_score DECIMAL(3,2), -- 0.00 to 1.00
    condition_grade VARCHAR,
    is_authentic BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create indexes for ebay_sealed_listings
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_product_id ON ebay_sealed_listings(sealed_product_id);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_sold_date ON ebay_sealed_listings(sold_date);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_price ON ebay_sealed_listings(price);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_created_at ON ebay_sealed_listings(created_at);

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
CREATE OR REPLACE VIEW all_ebay_listings AS
SELECT 
    'card' as listing_type,
    id,
    title,
    price,
    condition,
    sold_date,
    item_id,
    seller_name,
    listing_url,
    image_url,
    search_term,
    quality_score,
    created_at,
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
    item_id,
    seller_name,
    listing_url,
    image_url,
    search_term,
    quality_score,
    created_at,
    sealed_product_id as product_id,
    (SELECT CONCAT(product_name, ' (', product_type, ')') FROM sealed_products WHERE id = sealed_product_id) as product_description
FROM ebay_sealed_listings
WHERE sealed_product_id IS NOT NULL;

-- 7. Add RLS policies (if using Row Level Security)
-- ALTER TABLE sealed_products ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ebay_sealed_listings ENABLE ROW LEVEL SECURITY;

-- 8. Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sealed_products_updated_at 
    BEFORE UPDATE ON sealed_products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ebay_sealed_listings_updated_at 
    BEFORE UPDATE ON ebay_sealed_listings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 