from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables from root .env file
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://placeholder.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "placeholder_key")

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Test connection function
def test_connection():
    """Test the Supabase connection"""
    try:
        # Try to query the pokemon_sets table
        result = supabase.table("pokemon_sets").select("*").limit(1).execute()
        print(f"✅ Supabase connection successful! Found {len(result.data)} records in pokemon_sets table.")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection() 