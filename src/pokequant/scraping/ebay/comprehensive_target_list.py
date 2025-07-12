#!/usr/bin/env python3
"""
Comprehensive Target List for Quant Analysis
- All major sealed products from Sword & Shield and Scarlet & Violet series
- 50 high-value cards that have shown growth patterns
"""

# SEALED PRODUCTS: Sword & Shield Series (2020-2022)
SWSH_SEALED_PRODUCTS = [
    # Major sets with Booster Boxes and ETBs
    {"product_name": "Sword & Shield Booster Box", "set_name": "Sword & Shield", "product_type": "Booster Box"},
    {"product_name": "Sword & Shield Elite Trainer Box", "set_name": "Sword & Shield", "product_type": "Elite Trainer Box"},
    {"product_name": "Rebel Clash Booster Box", "set_name": "Rebel Clash", "product_type": "Booster Box"},
    {"product_name": "Rebel Clash Elite Trainer Box", "set_name": "Rebel Clash", "product_type": "Elite Trainer Box"},
    {"product_name": "Darkness Ablaze Booster Box", "set_name": "Darkness Ablaze", "product_type": "Booster Box"},
    {"product_name": "Darkness Ablaze Elite Trainer Box", "set_name": "Darkness Ablaze", "product_type": "Elite Trainer Box"},
    {"product_name": "Vivid Voltage Booster Box", "set_name": "Vivid Voltage", "product_type": "Booster Box"},
    {"product_name": "Vivid Voltage Elite Trainer Box", "set_name": "Vivid Voltage", "product_type": "Elite Trainer Box"},
    {"product_name": "Battle Styles Booster Box", "set_name": "Battle Styles", "product_type": "Booster Box"},
    {"product_name": "Battle Styles Elite Trainer Box", "set_name": "Battle Styles", "product_type": "Elite Trainer Box"},
    {"product_name": "Chilling Reign Booster Box", "set_name": "Chilling Reign", "product_type": "Booster Box"},
    {"product_name": "Chilling Reign Elite Trainer Box", "set_name": "Chilling Reign", "product_type": "Elite Trainer Box"},
    {"product_name": "Evolving Skies Booster Box", "set_name": "Evolving Skies", "product_type": "Booster Box"},
    {"product_name": "Evolving Skies Elite Trainer Box", "set_name": "Evolving Skies", "product_type": "Elite Trainer Box"},
    {"product_name": "Fusion Strike Booster Box", "set_name": "Fusion Strike", "product_type": "Booster Box"},
    {"product_name": "Fusion Strike Elite Trainer Box", "set_name": "Fusion Strike", "product_type": "Elite Trainer Box"},
    {"product_name": "Brilliant Stars Booster Box", "set_name": "Brilliant Stars", "product_type": "Booster Box"},
    {"product_name": "Brilliant Stars Elite Trainer Box", "set_name": "Brilliant Stars", "product_type": "Elite Trainer Box"},
    {"product_name": "Astral Radiance Booster Box", "set_name": "Astral Radiance", "product_type": "Booster Box"},
    {"product_name": "Astral Radiance Elite Trainer Box", "set_name": "Astral Radiance", "product_type": "Elite Trainer Box"},
    {"product_name": "Pokemon GO Elite Trainer Box", "set_name": "Pokemon GO", "product_type": "Elite Trainer Box"},
    {"product_name": "Lost Origin Booster Box", "set_name": "Lost Origin", "product_type": "Booster Box"},
    {"product_name": "Lost Origin Elite Trainer Box", "set_name": "Lost Origin", "product_type": "Elite Trainer Box"},
    {"product_name": "Silver Tempest Booster Box", "set_name": "Silver Tempest", "product_type": "Booster Box"},
    {"product_name": "Silver Tempest Elite Trainer Box", "set_name": "Silver Tempest", "product_type": "Elite Trainer Box"},
]

# SEALED PRODUCTS: Scarlet & Violet Series (2023-present)
SV_SEALED_PRODUCTS = [
    {"product_name": "Scarlet & Violet Booster Box", "set_name": "Scarlet & Violet", "product_type": "Booster Box"},
    {"product_name": "Scarlet & Violet Elite Trainer Box", "set_name": "Scarlet & Violet", "product_type": "Elite Trainer Box"},
    {"product_name": "Paldea Evolved Booster Box", "set_name": "Paldea Evolved", "product_type": "Booster Box"},
    {"product_name": "Paldea Evolved Elite Trainer Box", "set_name": "Paldea Evolved", "product_type": "Elite Trainer Box"},
    {"product_name": "Obsidian Flames Booster Box", "set_name": "Obsidian Flames", "product_type": "Booster Box"},
    {"product_name": "Obsidian Flames Elite Trainer Box", "set_name": "Obsidian Flames", "product_type": "Elite Trainer Box"},
    {"product_name": "151 Elite Trainer Box", "set_name": "151", "product_type": "Elite Trainer Box"},
    {"product_name": "151 Ultra Premium Collection", "set_name": "151", "product_type": "Ultra Premium Collection"},
    {"product_name": "Paradox Rift Booster Box", "set_name": "Paradox Rift", "product_type": "Booster Box"},
    {"product_name": "Paradox Rift Elite Trainer Box", "set_name": "Paradox Rift", "product_type": "Elite Trainer Box"},
    {"product_name": "Paldean Fates Elite Trainer Box", "set_name": "Paldean Fates", "product_type": "Elite Trainer Box"},
    {"product_name": "Temporal Forces Booster Box", "set_name": "Temporal Forces", "product_type": "Booster Box"},
    {"product_name": "Temporal Forces Elite Trainer Box", "set_name": "Temporal Forces", "product_type": "Elite Trainer Box"},
    {"product_name": "Twilight Masquerade Booster Box", "set_name": "Twilight Masquerade", "product_type": "Booster Box"},
    {"product_name": "Twilight Masquerade Elite Trainer Box", "set_name": "Twilight Masquerade", "product_type": "Elite Trainer Box"},
    {"product_name": "Shrouded Fable Elite Trainer Box", "set_name": "Shrouded Fable", "product_type": "Elite Trainer Box"},
    {"product_name": "Stellar Crown Booster Box", "set_name": "Stellar Crown", "product_type": "Booster Box"},
    {"product_name": "Stellar Crown Elite Trainer Box", "set_name": "Stellar Crown", "product_type": "Elite Trainer Box"},
    {"product_name": "Surging Sparks Booster Box", "set_name": "Surging Sparks", "product_type": "Booster Box"},
    {"product_name": "Surging Sparks Elite Trainer Box", "set_name": "Surging Sparks", "product_type": "Elite Trainer Box"},
]

# 50 HIGH-VALUE CARDS (Cards that have shown growth patterns)
HIGH_VALUE_CARDS = [
    # Charizard Premium Cards
    {"card_name": "Charizard V", "set_name": "Brilliant Stars", "card_number": "154", "category": "charizard_premium"},
    {"card_name": "Charizard VSTAR", "set_name": "Brilliant Stars", "card_number": "18", "category": "charizard_premium"},
    {"card_name": "Charizard", "set_name": "Base Set", "card_number": "4", "category": "vintage_icon"},
    {"card_name": "Charizard ex", "set_name": "151", "card_number": "6", "category": "151_premium"},
    {"card_name": "Charizard ex", "set_name": "Obsidian Flames", "card_number": "125", "category": "sv_premium"},
    
    # Pikachu Premium Cards
    {"card_name": "Pikachu VMAX", "set_name": "Vivid Voltage", "card_number": "188", "category": "pikachu_premium"},
    {"card_name": "Pikachu", "set_name": "Base Set", "card_number": "25", "category": "vintage_icon"},
    {"card_name": "Pikachu V", "set_name": "Vivid Voltage", "card_number": "43", "category": "pikachu_premium"},
    {"card_name": "Pikachu", "set_name": "151", "card_number": "25", "category": "151_growth"},
    
    # Eeveelution Cards (Strong growth category)
    {"card_name": "Umbreon V", "set_name": "Evolving Skies", "card_number": "189", "category": "eeveelution_premium"},
    {"card_name": "Espeon V", "set_name": "Evolving Skies", "card_number": "64", "category": "eeveelution_premium"},
    {"card_name": "Leafeon V", "set_name": "Evolving Skies", "card_number": "7", "category": "eeveelution_premium"},
    {"card_name": "Glaceon V", "set_name": "Evolving Skies", "card_number": "40", "category": "eeveelution_premium"},
    {"card_name": "Sylveon V", "set_name": "Evolving Skies", "card_number": "74", "category": "eeveelution_premium"},
    {"card_name": "Eevee", "set_name": "151", "card_number": "133", "category": "151_growth"},
    
    # Legendary Premium Cards
    {"card_name": "Rayquaza V", "set_name": "Evolving Skies", "card_number": "110", "category": "legendary_premium"},
    {"card_name": "Rayquaza VMAX", "set_name": "Evolving Skies", "card_number": "111", "category": "legendary_premium"},
    {"card_name": "Lugia V", "set_name": "Silver Tempest", "card_number": "138", "category": "current_meta"},
    {"card_name": "Lugia VSTAR", "set_name": "Silver Tempest", "card_number": "139", "category": "current_meta"},
    {"card_name": "Mewtwo ex", "set_name": "151", "card_number": "150", "category": "151_premium"},
    {"card_name": "Mew ex", "set_name": "151", "card_number": "151", "category": "151_premium"},
    
    # Vintage Base Set Icons
    {"card_name": "Blastoise", "set_name": "Base Set", "card_number": "2", "category": "vintage_icon"},
    {"card_name": "Venusaur", "set_name": "Base Set", "card_number": "15", "category": "vintage_icon"},
    {"card_name": "Alakazam", "set_name": "Base Set", "card_number": "1", "category": "vintage_rare"},
    {"card_name": "Machamp", "set_name": "Base Set", "card_number": "8", "category": "vintage_rare"},
    {"card_name": "Gyarados", "set_name": "Base Set", "card_number": "6", "category": "vintage_rare"},
    
    # Modern Alt Art & Secret Rares
    {"card_name": "Mew V", "set_name": "Fusion Strike", "card_number": "113", "category": "modern_alt_art"},
    {"card_name": "Giratina V", "set_name": "Lost Origin", "card_number": "130", "category": "modern_legendary"},
    {"card_name": "Giratina VSTAR", "set_name": "Lost Origin", "card_number": "131", "category": "modern_legendary"},
    {"card_name": "Arceus V", "set_name": "Brilliant Stars", "card_number": "122", "category": "competitive_meta"},
    {"card_name": "Arceus VSTAR", "set_name": "Brilliant Stars", "card_number": "123", "category": "competitive_meta"},
    
    # 151 Growth Cards
    {"card_name": "Charmander", "set_name": "151", "card_number": "4", "category": "151_growth"},
    {"card_name": "Squirtle", "set_name": "151", "card_number": "7", "category": "151_growth"},
    {"card_name": "Bulbasaur", "set_name": "151", "card_number": "1", "category": "151_growth"},
    {"card_name": "Snorlax", "set_name": "151", "card_number": "143", "category": "151_growth"},
    
    # Scarlet & Violet New Meta
    {"card_name": "Miraidon ex", "set_name": "Scarlet & Violet", "card_number": "81", "category": "sv_legendary"},
    {"card_name": "Koraidon ex", "set_name": "Scarlet & Violet", "card_number": "54", "category": "sv_legendary"},
    {"card_name": "Iron Valiant ex", "set_name": "Paradox Rift", "card_number": "89", "category": "paradox_pokemon"},
    {"card_name": "Roaring Moon ex", "set_name": "Paradox Rift", "card_number": "124", "category": "paradox_pokemon"},
    
    # Pokemon GO Special Cards
    {"card_name": "Mewtwo V", "set_name": "Pokemon GO", "card_number": "30", "category": "modern_premium"},
    {"card_name": "Dragonite V", "set_name": "Pokemon GO", "card_number": "131", "category": "modern_alt_art"},
    {"card_name": "Radiant Charizard", "set_name": "Pokemon GO", "card_number": "11", "category": "radiant_premium"},
    {"card_name": "Radiant Venusaur", "set_name": "Pokemon GO", "card_number": "4", "category": "radiant_premium"},
    
    # Neo Era Classics
    {"card_name": "Lugia", "set_name": "Neo Genesis", "card_number": "9", "category": "neo_classic"},
    {"card_name": "Ho-Oh", "set_name": "Neo Revelation", "card_number": "7", "category": "neo_classic"},
    
    # Fossil Era
    {"card_name": "Dragonite", "set_name": "Fossil", "card_number": "4", "category": "vintage_rare"},
    
    # Key Trainer Card
    {"card_name": "Professor Oak", "set_name": "Base Set", "card_number": "88", "category": "vintage_trainer"},
    
    # Additional Growth Tracking
    {"card_name": "Rayquaza", "set_name": "Skyridge", "card_number": "149", "category": "vintage_rare"},
    {"card_name": "Charizard", "set_name": "Base Set 2", "card_number": "4", "category": "vintage_icon"},
    {"card_name": "Charizard V", "set_name": "Champion's Path", "card_number": "20", "category": "charizard_premium"},
]

# COMBINED LISTS
ALL_SEALED_PRODUCTS = SWSH_SEALED_PRODUCTS + SV_SEALED_PRODUCTS
ALL_TARGET_CARDS = HIGH_VALUE_CARDS

def get_comprehensive_target_list():
    """Get complete list for scraping"""
    return {
        "sealed_products": ALL_SEALED_PRODUCTS,
        "cards": ALL_TARGET_CARDS,
        "total_sealed": len(ALL_SEALED_PRODUCTS),
        "total_cards": len(ALL_TARGET_CARDS),
        "total_targets": len(ALL_SEALED_PRODUCTS) + len(ALL_TARGET_CARDS)
    }

if __name__ == "__main__":
    targets = get_comprehensive_target_list()
    print(f"📊 COMPREHENSIVE TARGET LIST:")
    print(f"   Sealed Products: {targets['total_sealed']}")
    print(f"   High-Value Cards: {targets['total_cards']}")
    print(f"   Total Targets: {targets['total_targets']}")
    
    print(f"\n📦 SEALED PRODUCT BREAKDOWN:")
    print(f"   SWSH Series: {len(SWSH_SEALED_PRODUCTS)} products")
    print(f"   SV Series: {len(SV_SEALED_PRODUCTS)} products")
    
    print(f"\n🎯 SAMPLE CARDS BY CATEGORY:")
    categories = {}
    for card in ALL_TARGET_CARDS:
        category = card.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1
    
    for category, count in categories.items():
        print(f"   {category}: {count} cards") 