import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Schemas managed by Supabase that should NOT be included in a complete backup.
EXCLUDED_SCHEMAS = [
    'auth',
    'storage',
    'realtime',
    'supabase_functions',
    'supabase_migrations',
]
# --- End Configuration ---

def get_config():
    """Load configuration from .env and validate."""
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT', '6543')
    user = os.getenv('DB_USER')
    password = os.getenv('PASS')
    
    if not host or not user:
        print("❌ Configuration Error: Missing DB_HOST or DB_USER in .env file.")
        return None, None
        
    if not password:
        password = input("Enter your database password: ").strip()
        if not password:
            print("❌ Password cannot be empty.")
            return None, None
            
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password
    }, password

def run_pg_dump(config, output_file, mode):
    """Utility function to execute pg_dump."""
    
    # 1. Define pg_dump path
    # Try to use the full path you had before, but fallback to 'pg_dump' if not found
    pg_dump_path = '/opt/homebrew/opt/postgresql@15/bin/pg_dump'
    if not os.path.exists(pg_dump_path):
        pg_dump_path = 'pg_dump'
        
    # 2. Base command structure
    cmd = [
        pg_dump_path,
        f'--host={config["host"]}',
        f'--port={config["port"]}',
        f'--username={config["user"]}',
        '--dbname=postgres',
        '--clean',         # Add DROP TABLE IF EXISTS statements
        '--if-exists',     # Only use IF EXISTS with DROP
        '--no-owner',      # Prevents ownership errors on restore
        '--no-privileges', # Prevents grant errors on restore
        f'--file={output_file}'
    ]
    
    # 3. Mode-specific flags
    if mode == 'SCHEMA_ONLY':
        cmd.append('--schema-only')
        print(f"\n🚀 Creating SCHEMA-ONLY backup: {output_file}")
    
    elif mode == 'FULL_BACKUP':
        # Exclude managed schemas for a clean, restorable full backup
        for schema in EXCLUDED_SCHEMAS:
            cmd.append(f'--exclude-schema={schema}')
        print(f"\n🚀 Creating FULL BACKUP (Schema + Data, excluding system tables): {output_file}")

    # 4. Set PGPASSWORD environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    # 5. Execute
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_file)
            print(f"✅ SUCCESS! Backup saved: {output_file} ({file_size} bytes)")
        else:
            print(f"❌ pg_dump failed for {mode}: {result.stderr}")
            if "Wrong password" in result.stderr:
                print("💡 Hint: Password is still incorrect. Please reset and update 'PASS' in .env.")
            
    except FileNotFoundError:
        print(f"❌ Could not find pg_dump at: {pg_dump_path}")
        print("   Ensure PostgreSQL client tools are installed (e.g., brew install postgresql).")
    except Exception as e:
        print(f"❌ An error occurred during {mode} backup: {e}")

def main():
    config, password = get_config()
    if not config:
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # --- 1. Schema-Only Backup ---
    schema_file = f"schema_only_{timestamp}.sql"
    run_pg_dump(config, schema_file, 'SCHEMA_ONLY')
    
    # --- 2. Full Backup (Schema + Data) ---
    full_file = f"full_backup_{timestamp}.sql"
    run_pg_dump(config, full_file, 'FULL_BACKUP')


if __name__ == "__main__":
    main()