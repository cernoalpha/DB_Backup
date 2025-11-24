import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_password():
    """Get the actual database password"""
    print("You need your Supabase database password (not the API key).")
    print("Find it in: Supabase Dashboard > Project Settings > Database > Connection string")
    print("Or reset it in: Database > Settings > Database password")
    
    password = input("Enter your database password: ").strip()
    return password

def backup_supabase_schema():
    """Direct schema backup using pg_dump"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    if not supabase_url:
        print("❌ SUPABASE_URL not found in .env")
        return
    
    # Extract host from URL and add db prefix
    host = supabase_url.replace('https://', '').replace('http://', '')
    host = 'db.' + host  # Add db. prefix for direct connection
    
    # Get database password
    password = get_db_password()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Schema-only backup (no data)
    schema_file = f"schema_backup_{timestamp}.sql"
    
    print(f"🚀 Creating schema backup: {schema_file}")
    
    # pg_dump command for schema only (using PostgreSQL 15)
    cmd = [
        '/opt/homebrew/opt/postgresql@15/bin/pg_dump',
        f'--host={host}',
        '--port=5432',
        '--username=postgres',
        '--dbname=postgres',
        '--schema-only',  # Only structure, no data
        '--no-owner',     # Don't include ownership commands
        '--no-privileges', # Don't include privilege commands
        '--clean',        # Include DROP commands
        '--if-exists',    # Use IF EXISTS with DROP commands
        '--no-sync',      # Ignore version mismatch
        '--file=' + schema_file
    ]
    
    # Set password via environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = password
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Schema backup completed: {schema_file}")
            
            # Check file size
            file_size = os.path.getsize(schema_file)
            print(f"📊 Backup file size: {file_size} bytes")
            
            if file_size > 0:
                print("\n🎉 SUCCESS! Your complete database schema is backed up.")
                print(f"📁 File: {schema_file}")
                print("\nThis file contains:")
                print("  ✅ All table structures")
                print("  ✅ All constraints and indexes") 
                print("  ✅ All functions and procedures")
                print("  ✅ All triggers")
                print("  ✅ All policies")
                print("  ✅ Everything needed to recreate your database")
                
                # Also create a complete backup (with data) option
                create_data_backup = input("\nDo you also want a backup WITH data? (y/n): ").strip().lower()
                
                if create_data_backup == 'y':
                    data_file = f"complete_backup_{timestamp}.sql"
                    print(f"🚀 Creating complete backup: {data_file}")
                    
                    cmd_data = cmd.copy()
                    cmd_data.remove('--schema-only')  # Remove schema-only flag
                    cmd_data[-1] = '--file=' + data_file  # Update filename
                    
                    result_data = subprocess.run(cmd_data, env=env, capture_output=True, text=True)
                    
                    if result_data.returncode == 0:
                        data_size = os.path.getsize(data_file)
                        print(f"✅ Complete backup finished: {data_file} ({data_size} bytes)")
                    else:
                        print(f"❌ Data backup failed: {result_data.stderr}")
            else:
                print("❌ Backup file is empty. Check your credentials.")
                
        else:
            print(f"❌ pg_dump failed: {result.stderr}")
            if "password authentication failed" in result.stderr:
                print("💡 Wrong password. Get the correct one from Supabase Dashboard > Settings > Database")
            elif "could not connect" in result.stderr:
                print("💡 Connection failed. Check if pg_dump is installed: brew install postgresql")
                
    except FileNotFoundError:
        print("❌ pg_dump not found. Install PostgreSQL tools:")
        print("   macOS: brew install postgresql")
        print("   Ubuntu: sudo apt-get install postgresql-client")
        print("   Windows: Download from postgresql.org")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

if __name__ == "__main__":
    backup_supabase_schema()