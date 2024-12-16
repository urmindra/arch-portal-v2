import streamlit as st
import os
from datetime import datetime, timedelta
from psycopg2.extras import DictCursor
from models.database import get_db_connection

def hash_password(password):
    """Simple password hashing."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    """
    Check login credentials and handle login attempts/lockouts.
    Returns: role on success, None on failure, 'locked' if account is locked
    """
    if not username or not password:
        return None
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Check if account exists and get status
            cur.execute(
                """
                SELECT role, password_hash, login_attempts, last_login_attempt, is_active
                FROM admins WHERE username = %s
                """,
                (username,)
            )
            result = cur.fetchone()
            
            if not result:
                return None
            
            # Check if account is active
            if not result.get('is_active', True):
                return 'inactive'
                
            # Check for account lockout
            if result.get('login_attempts', 0) >= 5:
                # Check if enough time has passed to unlock
                if result.get('last_login_attempt'):
                    lockout_duration = datetime.now() - result['last_login_attempt']
                    remaining_seconds = max(300 - lockout_duration.total_seconds(), 0)  # 5 minutes lockout
                    if remaining_seconds > 0:
                        minutes = int(remaining_seconds // 60)
                        seconds = int(remaining_seconds % 60)
                        return f'locked:{minutes}:{seconds:02d}'
                
            if hash_password(password) == result['password_hash']:
                # Reset login attempts on successful login
                cur.execute(
                    """
                    UPDATE admins 
                    SET login_attempts = 0,
                        last_login = CURRENT_TIMESTAMP
                    WHERE username = %s
                    """,
                    (username,)
                )
                conn.commit()
                return result['role']
            else:
                # Increment login attempts
                cur.execute(
                    """
                    UPDATE admins 
                    SET login_attempts = COALESCE(login_attempts, 0) + 1,
                        last_login_attempt = CURRENT_TIMESTAMP
                    WHERE username = %s
                    """,
                    (username,)
                )
                conn.commit()
                return None

def check_password():
    """Returns `True` if the user has valid credentials."""
    if "admin_role" not in st.session_state:
        st.session_state["admin_role"] = None
    if "login_failed" not in st.session_state:
        st.session_state["login_failed"] = False
    
    def credentials_entered():
        """Checks whether entered credentials are correct."""
        if "username" in st.session_state and "password" in st.session_state:
            role = check_credentials(
                st.session_state["username"],
                st.session_state["password"]
            )
            if isinstance(role, str) and role.startswith('locked:'):
                _, time_remaining = role.split(':', 1)
                minutes, seconds = time_remaining.split(':')
                st.error(f"🔒 Account is temporarily locked due to too many failed attempts. Please try again in {minutes} minutes and {seconds} seconds.")
                return
            elif role == 'inactive':
                st.error("❌ Account is inactive. Please contact a super admin to reactivate your account.")
                return
            elif role is None and st.session_state.get("login_failed"):
                st.error("❌ Invalid username or password. Please try again.")
                return
            elif role:
                print(f"Login successful for user {st.session_state['username']} with role {role}")
                st.session_state["admin_role"] = role
                st.session_state["username_display"] = st.session_state["username"]
                st.session_state["admin_username"] = st.session_state["username"]  # Add explicit admin username
                st.session_state["login_failed"] = False
                del st.session_state["username"]
                del st.session_state["password"]
                print(f"Updated session state: {st.session_state}")
            else:
                st.session_state["admin_role"] = None
                st.session_state["login_failed"] = True
                print("Login failed - credentials did not match")

    # Return True if already authenticated
    if st.session_state["admin_role"]:
        return True

    # First-time users and incorrect credential attempts
    st.markdown("""
    ### Admin Authentication Required
    Please enter your credentials to access the admin dashboard.
    """)
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", type="password", key="password", on_change=credentials_entered)
    
    # Only show error if there was a failed login attempt
    if st.session_state["login_failed"]:
        st.error("😕 Invalid credentials. Please try again.")
    
    return False

def ensure_super_admin_exists():
    """Ensure that at least one super admin exists in the system."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if super admin exists
            cur.execute("SELECT COUNT(*) FROM admins WHERE role = 'super_admin'")
            if cur.fetchone()[0] == 0:
                # Create default super admin if ADMIN_PASSWORD is set
                admin_password = os.environ.get("ADMIN_PASSWORD")
                if admin_password:
                    cur.execute(
                        """
                        INSERT INTO admins (
                            username, password_hash, role, is_active, 
                            login_attempts, last_login, created_at, updated_at
                        ) VALUES (%s, %s, %s, true, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """,
                        ("superadmin", hash_password(admin_password), "super_admin")
                    )
                    conn.commit()
                    print("Created default super admin account")

def create_admin(username, password, role='admin'):
    """Create a new admin account."""
    if not is_super_admin():
        raise ValueError("Only super admin can create new admins")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if username already exists
            cur.execute("SELECT COUNT(*) FROM admins WHERE username = %s", (username,))
            if cur.fetchone()[0] > 0:
                raise ValueError(f"Username '{username}' already exists")
            
            # Create new admin
            cur.execute(
                """
                INSERT INTO admins (username, password_hash, role) 
                VALUES (%s, %s, %s)
                """,
                (username, hash_password(password), role)
            )
            conn.commit()

def update_admin_password(username, new_password):
    """Update admin password."""
    current_user = get_current_username()
    if not is_super_admin() and current_user != username:
        raise ValueError("Only super admin can change other admin passwords")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE admins 
                SET password_hash = %s,
                    login_attempts = 0
                WHERE username = %s
                """,
                (hash_password(new_password), username)
            )
            if cur.rowcount == 0:
                raise ValueError(f"Admin '{username}' not found")
            conn.commit()

def delete_admin(username):
    """Delete an admin account."""
    if not is_super_admin():
        raise ValueError("Only super admin can delete admin accounts")
    
    if username == get_current_username():
        raise ValueError("Cannot delete your own account")
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check if it's the last super admin
            if username == 'superadmin':
                cur.execute("SELECT COUNT(*) FROM admins WHERE role = 'super_admin'")
                if cur.fetchone()[0] <= 1:
                    raise ValueError("Cannot delete the last super admin")
            
            cur.execute("DELETE FROM admins WHERE username = %s", (username,))
            if cur.rowcount == 0:
                raise ValueError(f"Admin '{username}' not found")
            conn.commit()

def check_permission(required_role='admin'):
    """Check if current user has required role permission."""
    if not st.session_state.get("admin_role"):
        raise ValueError("Authentication required")
    
    current_role = st.session_state["admin_role"]
    if required_role == 'super_admin' and current_role != 'super_admin':
        raise ValueError("Super Admin privileges required for this operation")
    return True

def require_active_session():
    """Decorator to ensure active admin session."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not st.session_state.get("admin_role"):
                raise ValueError("Active admin session required")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_all_admins():
    """Get list of all admins. Only accessible by super admin."""
    if not is_super_admin():
        raise ValueError("Only super admin can view all admins")
    
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                """
                SELECT id, username, role, created_at, updated_at, 
                       last_login, login_attempts, is_active
                FROM admins 
                ORDER BY role, username
                """
            )
            return cur.fetchall()

def is_super_admin():
    """Check if current user is a super admin."""
    return st.session_state.get("admin_role") == "super_admin"

def get_current_username():
    """Get the username of currently logged in admin."""
    return st.session_state.get("username_display")

def logout():
    """Clear the session state to log out the user."""
    if "admin_role" in st.session_state:
        del st.session_state["admin_role"]
    if "username_display" in st.session_state:
        del st.session_state["username_display"]
