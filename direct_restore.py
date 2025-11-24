import os
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Set the default file to restore based on the last successful attempt
DEFAULT_RESTORE_FILE = "full_backup_20251125_000420.sql"
# --- End Configuration ---

def get_config():
    """Load configuration from .env and validate."""
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT', '6543')
    user = os.getenv('DB_USER')
    password = os.getenv('PASS')
    
    if not host or not user or not password:
        print("❌ Configuration Error: Missing DB_HOST, DB_USER, or PASS in .env file.")
        return None
        
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password
    }

def restore_supabase_data():
    """Restores a SQL file to the Supabase database using psql."""
    
    config = get_config()
    if not config:
        return

    # Prompt user for the file name to ensure they select the right one
    restore_file = input(f"Enter the backup file to restore (default: {DEFAULT_RESTORE_FILE}): ").strip()
    if not restore_file:
        restore_file = DEFAULT_RESTORE_FILE

    if not os.path.exists(restore_file):
        print(f"❌ File not found: {restore_file}")
        return

    print("\n=======================================================")
    print("⚠️ WARNING: This operation will OVERWRITE existing data!")
    print("=======================================================")
    
    confirm = input("Type 'YES' to proceed with the database RESTORE: ")
    if confirm.upper() != 'YES':
        print("Restore cancelled by user.")
        return

    print(f"\n🚀 Restoring {restore_file} to Supabase...")
    print(f"Connecting to Host: {config['host']}")
    
    # 1. Define psql path
    # Try to use the full path you had before, but fallback to 'psql' if not found
    psql_path = '/opt/homebrew/opt/postgresql@15/bin/psql'
    if not os.path.exists(psql_path):
        psql_path = 'psql'
        
    # 2. Base command structure for psql
    cmd = [
        psql_path,
        f'--host={config["host"]}',
        f'--port={config["port"]}',
        f'--username={config["user"]}',
        '--dbname=postgres',
        '--file=' + restore_file,
        '--echo-errors', # Show any SQL errors encountered
        '--quiet'        # Suppress command output, only show errors
    ]
    
    # 3. Set PGPASSWORD environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    # 4. Execute
    try:
        # Use a timeout for safety, restoring large files can take time
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300) 
        
        if result.returncode == 0:
            print(f"\n✅ RESTORE COMPLETE! Database restored from {restore_file}.")
        else:
            print(f"\n❌ psql failed: Restore attempt failed with return code {result.returncode}.")
            print("--- Output from psql (Errors Only) ---")
            # psql sends errors to stdout and stderr, print both for debugging
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
            print("---------------------------------------")
            print("💡 Hint: If you see a 'Wrong password' error, reset the password and update .env.")

    except FileNotFoundError:
        print(f"❌ Could not find psql at: {psql_path}")
        print("   Ensure PostgreSQL client tools are installed (e.g., brew install postgresql).")
    except subprocess.TimeoutExpired:
        print("❌ Restore timed out after 300 seconds (5 minutes). The file may be too large or the connection too slow.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    restore_supabase_data()