import json
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
from models.database import get_db_connection
import streamlit as st
import time

def log_admin_action(action_type, entity_type=None, entity_id=None, details=None):
    """
    Log an admin action to the audit_logs table.
    
    Args:
        action_type: Type of action (e.g., 'create_entity', 'delete_entity', 'login', etc.)
        entity_type: Optional - Type of entity involved (e.g., 'Capability', 'Use Case', etc.)
        entity_id: Optional - ID of the entity involved
        details: Optional - Additional details about the action (will be stored as JSONB)
    """
    conn = None
    try:
        # Debug session state
        print("\n=== Audit Logging Start ===")
        print("Session State:")
        for key, value in st.session_state.items():
            print(f"{key}: {value}")
        
        # Validate session state
        admin_role = st.session_state.get("admin_role")
        if not admin_role:
            print("ERROR: No admin role in session")
            return False
            
        # Get admin username with multiple fallback options
        admin_username = None
        possible_keys = ["admin_username", "username_display", "username"]
        for key in possible_keys:
            if key in st.session_state and st.session_state[key]:
                admin_username = st.session_state[key]
                break
        
        if not admin_username:
            print("ERROR: No admin username in session")
            print(f"Available keys: {st.session_state.keys()}")
            return False
            
        # Validate and clean the details for JSON storage
        if details:
            try:
                # Test JSON serialization
                json.dumps(details)
            except (TypeError, ValueError) as e:
                print(f"WARNING: Invalid JSON in details: {e}")
                details = str(details)  # Fallback to string representation
            
        print(f"\nLogging action: {action_type}")
        print(f"Admin: {admin_username} ({admin_role})")
        print(f"Entity: {entity_type} (ID: {entity_id})")
        print(f"Details: {details}")
        
        # Get database connection with retry
        retry_count = 0
        while retry_count < 3 and not conn:
            conn = get_db_connection()
            if not conn:
                retry_count += 1
                print(f"Database connection attempt {retry_count} failed")
                time.sleep(1)
                
        if not conn:
            print("ERROR: Failed to establish database connection after 3 attempts")
            return False
        
        # Start transaction
        conn.autocommit = False
        
        try:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Get admin_id
                cur.execute("""
                    SELECT id, username, role 
                    FROM admins 
                    WHERE username = %s
                """, (admin_username,))
                admin_result = cur.fetchone()
                
                if not admin_result:
                    print(f"Error: No admin found with username: {admin_username}")
                    return False
                    
                admin_id = admin_result['id']
                
                # Insert audit log
                cur.execute("""
                    INSERT INTO audit_logs 
                    (admin_id, admin_role, action_type, entity_type, entity_id, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """, (
                    admin_id,
                    admin_role,
                    action_type,
                    entity_type,
                    entity_id,
                    json.dumps(details) if details else None
                ))
                
                log_result = cur.fetchone()
                if not log_result:
                    print("Error: Failed to create audit log entry")
                    conn.rollback()
                    return False
                
                # Commit transaction
                conn.commit()
                print(f"Successfully created audit log with ID: {log_result['id']} at {log_result['created_at']}")
                return True
                
        except Exception as db_error:
            if conn:
                conn.rollback()
            print(f"Database error in audit logging: {str(db_error)}")
            import traceback
            print(traceback.format_exc())
            return False
            
    except Exception as e:
        print(f"General error in audit logging: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False
        
    finally:
        if conn:
            try:
                conn.autocommit = True
            except Exception:
                pass

def get_audit_logs(filters=None):
    """
    Retrieve audit logs with optional filtering.
    
    Args:
        filters: Optional dict with filter parameters (admin_id, action_type, date_range, etc.)
    
    Returns:
        List of audit log entries
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                query = """
                    SELECT 
                        al.id,
                        a.username as admin_username,
                        al.admin_role,
                        al.action_type,
                        al.entity_type,
                        al.entity_id,
                        al.details,
                        al.created_at
                    FROM audit_logs al
                    JOIN admins a ON al.admin_id = a.id
                """
                
                where_clauses = []
                params = []
                
                if filters:
                    if filters.get('admin_id'):
                        where_clauses.append("al.admin_id = %s")
                        params.append(filters['admin_id'])
                    if filters.get('action_type') and filters['action_type'] != "All":
                        where_clauses.append("al.action_type = %s")
                        params.append(filters['action_type'])
                    if filters.get('date_from'):
                        where_clauses.append("al.created_at >= %s")
                        params.append(filters['date_from'])
                    if filters.get('date_to'):
                        where_clauses.append("al.created_at <= %s")
                        params.append(filters['date_to'])
                
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                
                query += " ORDER BY al.created_at DESC"
                
                print(f"Executing query: {query} with params: {params}")
                cur.execute(query, params)
                results = cur.fetchall()
                print(f"Found {len(results)} audit logs")
                return results
    except Exception as e:
        print(f"Error retrieving audit logs: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []

def get_audit_summary():
    """
    Get a summary of audit logs for dashboard display.
    
    Returns:
        Dict containing summary statistics
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get total actions by type
                cur.execute("""
                    SELECT action_type, COUNT(*) 
                    FROM audit_logs 
                    GROUP BY action_type
                """)
                action_counts = dict(cur.fetchall())
                
                # Get actions by role
                cur.execute("""
                    SELECT admin_role, COUNT(*) 
                    FROM audit_logs 
                    GROUP BY admin_role
                """)
                role_counts = dict(cur.fetchall())
                
                # Get recent activity count (last 24 hours)
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM audit_logs 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                recent_count = cur.fetchone()[0]
                
                return {
                    'action_counts': action_counts,
                    'role_counts': role_counts,
                    'recent_count': recent_count
                }
    except Exception as e:
        print(f"Error getting audit summary: {str(e)}")
        return {}
