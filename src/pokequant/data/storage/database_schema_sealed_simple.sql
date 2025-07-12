-- Simple Database Schema for Sealed Products Support
-- Just add the two tables we need, nothing fancy

-- 1. Create sealed_products table
CREATE TABLE IF NOT EXISTS sealed_products (
    id BIGSERIAL PRIMARY KEY,
    product_name VARCHAR NOT NULL,
    set_name VARCHAR NOT NULL,
    product_type VARCHAR NOT NULL, -- 'Booster Box', 'Elite Trainer Box', etc.
    msrp DECIMAL(10,2), -- Manufacturer's Suggested Retail Price
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicates
    UNIQUE(product_name, set_name, product_type)
);

-- 2. Create table for eBay listings of sealed products
CREATE TABLE IF NOT EXISTS ebay_sealed_listings (
    id BIGSERIAL PRIMARY KEY,
    sealed_product_id BIGINT REFERENCES sealed_products(id),
    
    -- Same core columns as ebay_sold_listings
    title VARCHAR NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    listing_url TEXT NOT NULL,
    search_terms VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
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
    condition_category VARCHAR,
    search_strategy VARCHAR,
    grade_numeric INTEGER
);

-- 3. Create indexes
CREATE INDEX IF NOT EXISTS idx_sealed_products_set_name ON sealed_products(set_name);
CREATE INDEX IF NOT EXISTS idx_sealed_products_product_type ON sealed_products(product_type);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_product_id ON ebay_sealed_listings(sealed_product_id);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_price ON ebay_sealed_listings(price);
CREATE INDEX IF NOT EXISTS idx_ebay_sealed_listings_created_at ON ebay_sealed_listings(created_at);

-- 4. Insert the 10 sealed products we want to track
INSERT INTO sealed_products (product_name, set_name, product_type, msrp) VALUES
('Brilliant Stars Booster Box', 'Brilliant Stars', 'Booster Box', 143.64),
('Brilliant Stars Elite Trainer Box', 'Brilliant Stars', 'Elite Trainer Box', 49.99),
('Evolving Skies Booster Box', 'Evolving Skies', 'Booster Box', 143.64),
('Evolving Skies Elite Trainer Box', 'Evolving Skies', 'Elite Trainer Box', 49.99),
('Silver Tempest Booster Box', 'Silver Tempest', 'Booster Box', 143.64),
('Silver Tempest Elite Trainer Box', 'Silver Tempest', 'Elite Trainer Box', 49.99),
('Lost Origin Booster Box', 'Lost Origin', 'Booster Box', 143.64),
('Lost Origin Elite Trainer Box', 'Lost Origin', 'Elite Trainer Box', 49.99),
('Base Set Booster Box', 'Base Set', 'Booster Box', NULL),
('Base Set 1st Edition Booster Box', 'Base Set', 'Booster Box (1st Edition)', NULL)
ON CONFLICT (product_name, set_name, product_type) DO NOTHING; 