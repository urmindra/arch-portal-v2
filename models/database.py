import os
import psycopg2
from psycopg2.extras import RealDictCursor
import time

class Database:
    def __init__(self):
        self.conn = None
        self.connect_with_retry()
        self.create_tables()

    def connect_with_retry(self, max_retries=5):
        """Establish database connection with retry mechanism"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                self.conn = psycopg2.connect(
                    database=os.getenv('PGDATABASE'),
                    user=os.getenv('PGUSER'),
                    password=os.getenv('PGPASSWORD'),
                    host=os.getenv('PGHOST'),
                    port=os.getenv('PGPORT')
                )
                print("Database connection established successfully!")
                return
            except psycopg2.OperationalError as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
                print(f"Connection attempt {retry_count} failed, retrying in 2 seconds...")
                time.sleep(2)

    def ensure_connection(self):
        """Ensure database connection is alive and reconnect if necessary"""
        try:
            with self.conn.cursor() as cur:
                cur.execute('SELECT 1')
        except (psycopg2.OperationalError, psycopg2.InterfaceError, AttributeError):
            print("Database connection lost, reconnecting...")
            self.connect_with_retry()

    def create_tables(self):
        """Create necessary database tables if they don't exist"""
        self.ensure_connection()
        with self.conn.cursor() as cur:
            try:
                # Create entities table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS entities (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        type VARCHAR(50) NOT NULL,
                        description TEXT,
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create relationships table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS relationships (
                        id SERIAL PRIMARY KEY,
                        source_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        target_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        relationship_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create tags table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE
                    )
                """)
                
                # Create entity_tags table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS entity_tags (
                        entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                        PRIMARY KEY (entity_id, tag_id)
                    )
                """)
                
                # Create admins table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) NOT NULL UNIQUE,
                        password_hash VARCHAR(64) NOT NULL,
                        role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'super_admin')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create audit_logs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        admin_id INTEGER REFERENCES admins(id),
                        admin_role VARCHAR(20) NOT NULL,
                        action_type VARCHAR(50) NOT NULL,
                        entity_type VARCHAR(50),
                        entity_id INTEGER,
                        details JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                self.conn.commit()
                print("Database tables created successfully!")
            except Exception as e:
                self.conn.rollback()
                raise Exception(f"Error creating tables: {str(e)}")

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

_db_instance = Database()

def get_db_connection():
    """Get a database connection from the pool"""
    try:
        _db_instance.ensure_connection()
        if not _db_instance.conn:
            print("ERROR: No database connection available")
            return None
        # Test connection
        with _db_instance.conn.cursor() as cur:
            cur.execute('SELECT 1')
            if not cur.fetchone():
                raise Exception("Database connection test failed")
        return _db_instance.conn
    except Exception as e:
        print(f"Error getting database connection: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

db = _db_instance  # Keep backward compatibility
