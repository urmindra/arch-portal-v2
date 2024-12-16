import streamlit as st
import os
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from models.entities import EntityManager
from utils.auth import (
    check_password, logout, hash_password, is_super_admin,
    get_current_username, get_all_admins, create_admin,
    update_admin_password, delete_admin
)
from utils.audit import log_admin_action, get_audit_logs, get_audit_summary

def render_admin_dashboard():
    """Render the admin activity dashboard with metrics and visualizations."""
    st.header("Admin Activity Dashboard")
    
    # Get audit summary for metrics
    summary = get_audit_summary()
    
    # Display key metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Actions Today",
            summary.get('recent_count', 0),
            help="Number of admin actions in the last 24 hours"
        )
    
    with col2:
        # Get action distribution
        action_counts = summary.get('action_counts', {})
        total_actions = sum(action_counts.values()) if action_counts else 0
        st.metric(
            "Total Actions",
            total_actions,
            help="Total number of admin actions recorded"
        )
    
    with col3:
        # Get role distribution
        role_counts = summary.get('role_counts', {})
        active_admins = len(role_counts) if role_counts else 0
        st.metric(
            "Active Admins",
            active_admins,
            help="Number of admins who have performed actions"
        )
    
    # Display action type distribution
    st.subheader("Action Distribution")
    if summary.get('action_counts'):
        # Create DataFrame and format action types
        action_data = pd.DataFrame(
            list(summary['action_counts'].items()),
            columns=['Action Type', 'Count']
        )
        # Format action types to be more readable
        action_data['Action Type'] = action_data['Action Type'].apply(
            lambda x: x.replace('_', ' ').title()
        )
        # Sort by count in descending order
        action_data = action_data.sort_values('Count', ascending=True)
        
        # Create horizontal bar chart using Altair
        chart = alt.Chart(action_data).mark_bar().encode(
            y=alt.Y('Action Type:N', sort='-x', title=None),
            x=alt.X('Count:Q', 
                   title='Number of Actions',
                   axis=alt.Axis(tickCount=10, format='d')),  # 'd' for decimal format
            tooltip=['Action Type', 'Count']
        ).properties(
            height=max(100, len(action_data) * 47)  # Increased spacing by 7px per item
        )
        
        # Display the chart
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No actions recorded yet")
    
    # Display recent activity
    st.subheader("Recent Activity")
    recent_logs = get_audit_logs({"date_from": datetime.now() - timedelta(days=1)})
    
    if recent_logs:
        for log in recent_logs[:5]:  # Show last 5 activities
            with st.expander(
                f"{log['action_type']} by {log['admin_username']} "
                f"({log['created_at'].strftime('%H:%M:%S')})"
            ):
                st.write(f"**Role:** {log['admin_role']}")
                if log['entity_type']:
                    st.write(f"**Entity Type:** {log['entity_type']}")
                if log['details']:
                    st.write("**Details:**")
                    st.json(log['details'])
    else:
        st.info("No recent activity to display")

def render_relationship_manager():
    """Render the relationship management interface."""
    st.header("Manage Relationships")
    
    # Add entity type filter for relationships
    entity_types = ["All", "Capability", "Use Case", "Tool", "Product"]
    selected_type = st.selectbox("Filter by Entity Type", entity_types, key="rel_type_filter")
    
    # Get filtered entities based on type
    entities = EntityManager.get_entities(
        entity_type=selected_type if selected_type != "All" else None
    )
    
    if not entities:
        st.info("No entities available. Please create some entities first.")
        return
        
    # Create new relationship section
    st.subheader("Create New Relationship")
    source_entity = st.selectbox(
        "Source Entity",
        options=entities,
        format_func=lambda x: f"{x['name']} ({x['type']})",
        key="source_entity"
    )
    
    target_entity = st.selectbox(
        "Target Entity",
        options=entities,
        format_func=lambda x: f"{x['name']} ({x['type']})",
        key="target_entity"
    )
    
    relationship_type = st.selectbox(
        "Relationship Type",
        options=["enables", "implemented by", "uses", "supports", "powered by", "delivers"]
    )
    
    if st.button("Create Relationship"):
        try:
            EntityManager.create_relationship(
                source_entity['id'],
                target_entity['id'],
                relationship_type
            )
            st.success("Relationship created successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error creating relationship: {str(e)}")
    
    # View and manage existing relationships
    st.subheader("Existing Relationships")
    filtered_entities = [e for e in entities if selected_type == "All" or e['type'] == selected_type]
    
    # Initialize session state for relationship selection if not exists
    if 'selected_relationships' not in st.session_state:
        st.session_state.selected_relationships = set()
    
    # Track all visible relationships for select all functionality
    all_visible_relationship_ids = set()
    
    for entity in filtered_entities:
        with st.expander(f"Relationships for {entity['name']} ({entity['type']})"):
            relationships = EntityManager.get_entity_relationships(entity['id'])
            if relationships:
                # Add relationship IDs to visible set
                for rel in relationships:
                    all_visible_relationship_ids.add(rel['id'])
                
                # Add select all checkbox for this entity's relationships
                entity_select_all = st.checkbox(
                    "Select All Relationships",
                    key=f"select_all_rel_{entity['id']}"
                )
                if entity_select_all:
                    st.session_state.selected_relationships.update(
                        rel['id'] for rel in relationships
                    )
                elif not entity_select_all and all(
                    rel['id'] in st.session_state.selected_relationships 
                    for rel in relationships
                ):
                    for rel in relationships:
                        st.session_state.selected_relationships.discard(rel['id'])
                
                # Add delete selected button if any relationships are selected
                if st.session_state.selected_relationships:
                    if st.button(
                        f"Delete Selected Relationships ({len(st.session_state.selected_relationships)})",
                        key=f"del_selected_rel_{entity['id']}"
                    ):
                        try:
                            EntityManager.delete_multiple_relationships(
                                list(st.session_state.selected_relationships)
                            )
                            st.success(f"Successfully deleted {len(st.session_state.selected_relationships)} relationships")
                            st.session_state.selected_relationships.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting relationships: {str(e)}")
                
                for idx, rel in enumerate(relationships):
                    checkbox_col, col1, col2, col3, col4 = st.columns([0.5, 2, 2, 2, 1])
                    
                    with checkbox_col:
                        relationship_selected = st.checkbox(
                            "",
                            value=rel['id'] in st.session_state.selected_relationships,
                            key=f"rel_select_{entity['id']}_{rel['id']}"
                        )
                        if relationship_selected:
                            st.session_state.selected_relationships.add(rel['id'])
                        else:
                            st.session_state.selected_relationships.discard(rel['id'])
                    
                    with col1:
                        # Add dropdown to select new target entity
                        other_entities = [e for e in entities if e['id'] != entity['id']]
                        current_related = next((e for e in entities if e['name'] == rel['related_entity_name']), None)
                        
                        new_target = st.selectbox(
                            "With",
                            options=other_entities,
                            format_func=lambda x: f"{x['name']} ({x['type']})",
                            index=other_entities.index(current_related) if current_related else 0,
                            key=f"target_{entity['id']}_{rel['id']}_{idx}"
                        )
                    
                    with col2:
                        new_rel_type = st.selectbox(
                            "Type",
                            options=["enables", "implemented by", "uses", "supports", "powered by", "delivers"],
                            key=f"rel_type_{entity['id']}_{rel['id']}_{idx}",
                            index=["enables", "implemented by", "uses", "supports", "powered by", "delivers"].index(rel['relationship_type'])
                        )
                    
                    with col3:
                        # Update button for both relationship type and target
                        if (new_rel_type != rel['relationship_type'] or 
                            new_target['name'] != rel['related_entity_name']):
                            if st.button("Update", key=f"update_rel_{entity['id']}_{rel['id']}_{idx}"):
                                try:
                                    if new_target['name'] != rel['related_entity_name']:
                                        # Delete old relationship and create new one
                                        EntityManager.delete_relationship(entity['id'], rel['related_entity_name'])
                                        EntityManager.create_relationship(
                                            entity['id'],
                                            new_target['id'],
                                            new_rel_type
                                        )
                                    else:
                                        # Just update the relationship type
                                        EntityManager.update_relationship(rel['id'], new_rel_type)
                                    st.success("Relationship updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating relationship: {str(e)}")
                    
                    with col4:
                        if st.button(
                            "Delete",
                            key=f"del_rel_{entity['id']}_{rel['id']}_{idx}"
                        ):
                            EntityManager.delete_relationship(entity['id'], rel['related_entity_name'])
                            st.success("Relationship deleted successfully!")
                            st.rerun()
                    st.divider()
            else:
                st.info("No relationships found for this entity.")

def render_entity_list():
    """Render the entity list management interface."""
    st.header("Manage Existing Entities")
    
    # Add entity type filter
    entity_types = ["All", "Capability", "Use Case", "Tool", "Product"]
    selected_type = st.selectbox("Filter by Entity Type", entity_types, key="entity_type_filter")
    
    # Get filtered entities
    entities = EntityManager.get_entities(
        entity_type=selected_type if selected_type != "All" else None
    )
    
    if not entities:
        st.info("No entities found.")
        return

    # Initialize session state for entity selection if not exists
    if 'selected_entities' not in st.session_state:
        st.session_state.selected_entities = set()

    # Add select all checkbox
    select_all = st.checkbox("Select All Entities", key="select_all_entities")
    if select_all:
        st.session_state.selected_entities = {entity['id'] for entity in entities}
    elif not select_all and len(st.session_state.selected_entities) == len(entities):
        st.session_state.selected_entities.clear()

    # Add delete selected button
    if st.session_state.selected_entities:
        if st.button(f"Delete Selected Entities ({len(st.session_state.selected_entities)})"):
            try:
                EntityManager.delete_multiple_entities(list(st.session_state.selected_entities))
                st.success(f"Successfully deleted {len(st.session_state.selected_entities)} entities")
                st.session_state.selected_entities.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error deleting entities: {str(e)}")
        
    # Display entities in expandable sections
    for entity in entities:
        col1, col2 = st.columns([0.5, 11.5])
        with col1:
            entity_selected = st.checkbox("", value=entity['id'] in st.session_state.selected_entities,
                                       key=f"entity_select_{entity['id']}")
            if entity_selected:
                st.session_state.selected_entities.add(entity['id'])
            else:
                st.session_state.selected_entities.discard(entity['id'])
        
        with col2:
            with st.expander(f"{entity['name']} ({entity['type']})"):
                description = st.text_area("Description", entity['description'], key=f"desc_{entity['id']}")
                
                # Get and display current tags
                current_tags = EntityManager.get_entity_tags(entity['id'])
                current_tag_names = [tag['name'] for tag in current_tags]
                
                # Get all available tags
                all_tags = EntityManager.get_tags()
                selected_tags = st.multiselect(
                    "Tags",
                    options=all_tags,
                    default=current_tag_names,
                    key=f"tags_{entity['id']}"
                )
                
                # Update entity if changes are made
                if st.button("Update", key=f"update_{entity['id']}"):
                    try:
                        # Update description if changed
                        if description != entity['description']:
                            EntityManager.update_entity(entity['id'], description=description)
                        
                        # Update tags if changed
                        if set(selected_tags) != set(current_tag_names):
                            EntityManager.update_entity_tags(entity['id'], selected_tags)
                        
                        st.success("Entity updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating entity: {str(e)}")
                
                # Delete entity
                if st.button("Delete", key=f"delete_{entity['id']}"):
                    try:
                        # Log before deletion
                        log_admin_action(
                            action_type="delete_entity",
                            entity_type=entity['type'],
                            entity_id=entity['id'],
                            details={"name": entity['name']}
                        )
                        
                        EntityManager.delete_entity(entity['id'])
                        st.success("Entity deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting entity: {str(e)}")

def render_admin_management():
    """Render admin management interface for super admins."""
    st.header("Admin Management")
    
    try:
        admins = get_all_admins()
        current_username = get_current_username()
        
        # Create new admin section
        st.subheader("Create New Admin")
        
        # Display role management guidelines in a collapsible expander
        with st.expander("🔑 Role Guidelines", expanded=False):
            st.markdown("""
            - **Super Admin:** Full access to all features, including admin management and bulk operations
            - **Admin:** Access to entity and relationship management
            
            Note: At least one Super Admin must exist in the system.
            """)
        
        new_username = st.text_input("Username", key="new_admin_username")
        new_password = st.text_input("Password", type="password", key="new_admin_password")
        new_role = st.selectbox(
            "Role",
            ["admin", "super_admin"],
            help="Super Admin has full access, Admin has limited access",
            key="new_admin_role"
        )
        
        if st.button("Create Admin", type="primary"):
            if not new_username or not new_password:
                st.error("Username and password are required")
            else:
                try:
                    create_admin(new_username, new_password, new_role)
                    st.success(f"Admin '{new_username}' created successfully!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        
        # Existing admins section
        st.subheader("Manage Existing Admins")
        for admin in admins:
            with st.expander(f"{admin['username']} ({admin['role']})"):
                # Show admin status with colored badge
                status_color = "#28a745" if admin.get('is_active', True) else "#dc3545"
                attempts = admin.get('login_attempts', 0)
                status_text = "🟢 Active" if admin.get('is_active', True) else "🔴 Inactive"
                if attempts >= 5:
                    status_text = "🔒 Locked (too many attempts)"
                    status_color = "#ffc107"
                
                st.markdown(f"""
                    <div style='margin-bottom: 10px;'>
                        <span style='color: {status_color}; font-weight: bold;'>{status_text}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # Show last login and attempts
                if admin.get('last_login'):
                    st.text(f"Last Login: {admin['last_login']}")
                st.text(f"Login Attempts: {attempts}")
                
                # Password reset section
                new_pass = st.text_input(
                    "New Password",
                    type="password",
                    key=f"pass_{admin['username']}_{admin['id']}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Reset Password", key=f"reset_{admin['username']}"):
                        try:
                            update_admin_password(admin['username'], new_pass)
                            st.success(f"Password updated for {admin['username']}")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
                
                with col2:
                    if admin['username'] != 'superadmin':  # Prevent deletion of superadmin
                        if st.button("Delete Admin", key=f"delete_{admin['username']}"):
                            try:
                                delete_admin(admin['username'])
                                st.success(f"Admin {admin['username']} deleted successfully!")
                                st.rerun()
                            except ValueError as e:
                                st.error(str(e))
                
                # Show additional info
                st.text(f"Created: {admin['created_at']}")
                st.text(f"Last Updated: {admin['updated_at']}")
    
    except ValueError as e:
        st.error(str(e))

def render_admin_interface():
    """Main function to render the admin interface."""
    st.title("Admin Dashboard")
    
    # Add user info and logout in the top right
    col1, col2, col3 = st.columns([6, 3, 1])
    with col2:
        if get_current_username():
            role_badge = "🔑 Super Admin" if is_super_admin() else "👤 Admin"
            st.markdown(f"""
                <div style='text-align: right'>
                    <p>Logged in as: <b>{get_current_username()}</b></p>
                    <p style='color: #0066cc;'>{role_badge}</p>
                </div>
                """, unsafe_allow_html=True)
    with col3:
        if st.button("Logout", key="logout_button"):
            logout()
            st.rerun()
    
    # Check authentication before showing admin content
    if not check_password():
        return
    
    # Create tabs - super admin sees all tabs, regular admin sees limited tabs
    if is_super_admin():
        tabs = st.tabs([
            "Dashboard",
            "Create Entity",
            "Manage Entities",
            "Manage Relationships",
            "Admin Management",
            "Bulk Delete",
            "Audit Logs"
        ])
    else:
        tabs = st.tabs([
            "Create Entity",
            "Manage Entities",
            "Manage Relationships"
        ])
    
    # Admin Dashboard Tab (Super Admin only)
    if is_super_admin():
        with tabs[0]:
            render_admin_dashboard()
    
    # Entity Creation Tab
    tab_index = 1 if is_super_admin() else 0
    with tabs[tab_index]:
        st.header("Create New Entity")
        
        entity_type = st.selectbox("Entity Type", ["Capability", "Use Case", "Tool", "Product"])
        name = st.text_input("Name")
        description = st.text_area("Description")
        
        # Tag Management Section
        all_tags = EntityManager.get_tags()
        selected_tags = st.multiselect("Select Tags", all_tags)
        
        # Add new tag input
        new_tag = st.text_input("Add New Tag")
        if st.button("Add Tag"):
            if new_tag:
                if new_tag not in all_tags:
                    EntityManager.add_tag(None, new_tag)
                    st.success(f"Tag '{new_tag}' added successfully!")
                    st.rerun()
                else:
                    st.warning(f"Tag '{new_tag}' already exists!")
        
        if st.button("Create Entity"):
            if not name:
                st.error("Name is required!")
            else:
                try:
                    entity_id = EntityManager.create_entity(name, entity_type, description)
                    
                    # Add selected tags to the entity
                    for tag in selected_tags:
                        EntityManager.add_tag(entity_id, tag)
                    
                    # Log the entity creation
                    log_admin_action(
                        action_type="create_entity",
                        entity_type=entity_type,
                        entity_id=entity_id,
                        details={
                            "name": name,
                            "tags": selected_tags
                        }
                    )
                    
                    st.success("Entity created successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating entity: {str(e)}")
    
    # Manage Entities Tab
    with tabs[tab_index + 1]:
        render_entity_list()
    
    # Manage Relationships Tab
    with tabs[tab_index + 2]:
        render_relationship_manager()
    
    # Admin Management Tab (Super Admin only)
    if is_super_admin():
        with tabs[4]:
            render_admin_management()
        
        with tabs[5]:
            render_bulk_delete()
            
        with tabs[6]:
            render_audit_logs()

def render_bulk_delete():
    """Render the secure bulk delete interface with preview functionality."""
    st.header("Secure Bulk Delete")
    
    # Add warning message
    st.warning("⚠️ This is a powerful tool that allows bulk deletion of entities. Please use with caution.")
    
    # Entity type filter
    entity_types = ["All", "Capability", "Use Case", "Tool", "Product"]
    selected_type = st.selectbox(
        "Filter by Entity Type",
        entity_types,
        key="bulk_delete_type_filter"
    )
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        date_from = st.date_input("Created From", key="bulk_delete_date_from")
    with col2:
        date_to = st.date_input("Created To", key="bulk_delete_date_to")
    
    # Get filtered entities for preview
    entities = EntityManager.get_entities(
        entity_type=selected_type if selected_type != "All" else None,
        date_filter=date_from if date_from else None,
        date_to=date_to if date_to else None
    )
    
    if not entities:
        st.info("No entities found matching the selected criteria.")
        return
    
    # Preview section
    st.subheader(f"Preview ({len(entities)} entities)")
    
    # Initialize session state for entity selection
    if 'bulk_delete_selected' not in st.session_state:
        st.session_state.bulk_delete_selected = set()
    
    # Select all checkbox
    select_all = st.checkbox("Select All for Deletion", key="bulk_delete_select_all")
    if select_all:
        st.session_state.bulk_delete_selected = {entity['id'] for entity in entities}
    elif not select_all and len(st.session_state.bulk_delete_selected) == len(entities):
        st.session_state.bulk_delete_selected.clear()
    
    # Display entities in a scrollable container
    with st.container():
        for entity in entities:
            col1, col2, col3 = st.columns([0.5, 2, 8])
            with col1:
                entity_selected = st.checkbox(
                    "",
                    value=entity['id'] in st.session_state.bulk_delete_selected,
                    key=f"bulk_delete_{entity['id']}"
                )
                if entity_selected:
                    st.session_state.bulk_delete_selected.add(entity['id'])
                else:
                    st.session_state.bulk_delete_selected.discard(entity['id'])
            
            with col2:
                st.write(entity['type'])
            with col3:
                st.write(f"{entity['name']} - {entity['description'][:100]}...")
    
    # Delete button with confirmation
    if st.session_state.bulk_delete_selected:
        st.markdown("---")
        st.warning(f"🗑️ {len(st.session_state.bulk_delete_selected)} entities selected for deletion")
        
        if st.button("Confirm Bulk Delete", type="primary"):
            try:
                # Log the bulk delete action before deletion
                log_admin_action(
                    action_type="bulk_delete",
                    details={
                        "count": len(st.session_state.bulk_delete_selected),
                        "entity_type": selected_type,
                        "date_range": f"{date_from} to {date_to}" if date_from and date_to else "All dates"
                    }
                )
                
                # Perform deletion
                EntityManager.delete_multiple_entities(list(st.session_state.bulk_delete_selected))
                st.success(f"Successfully deleted {len(st.session_state.bulk_delete_selected)} entities")
                st.session_state.bulk_delete_selected.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error during bulk deletion: {str(e)}")

def render_audit_logs():
    """Render the audit logs viewer interface."""
    st.header("Audit Logs")
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter by action type
        action_types = ["All", "create_entity", "update_entity", "delete_entity", "create_relationship", "update_relationship", "delete_relationship"]
        selected_action = st.selectbox("Filter by Action", action_types)
    
    with col2:
        # Date range filter
        date_from = st.date_input("From Date")
    
    with col3:
        date_to = st.date_input("To Date")
    
    # Prepare filters
    filters = {}
    if selected_action != "All":
        filters['action_type'] = selected_action
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    
    # Get and display audit logs
    logs = get_audit_logs(filters)
    
    if not logs:
        st.info("No audit logs found matching the filters.")
        return
    
    # Display summary metrics
    summary = get_audit_summary()
    
    # Show summary metrics in a clean layout with better formatting
    metrics_cols = st.columns(3)
    with metrics_cols[0]:
        st.metric(
            "Total Actions", 
            len(logs),
            help="Total number of audit log entries matching current filters"
        )
    with metrics_cols[1]:
        st.metric(
            "Recent Actions (24h)", 
            summary.get('recent_count', 0),
            help="Number of actions in the last 24 hours"
        )
    with metrics_cols[2]:
        # Most common action with improved formatting
        action_counts = summary.get('action_counts', {})
        if action_counts:
            most_common = max(action_counts.items(), key=lambda x: x[1])
            action_name = most_common[0].replace('_', ' ').title()
            st.metric(
                "Most Common Action", 
                action_name,
                f"Count: {most_common[1]}",
                help="Most frequently performed action with its count"
            )
    
    # Display logs in an expandable table
    for log in logs:
        with st.expander(f"{log['action_type']} by {log['admin_username']} ({log['admin_role']})"):
            st.write(f"**Time:** {log['created_at']}")
            if log['entity_type']:
                st.write(f"**Entity Type:** {log['entity_type']}")
            if log['entity_id']:
                st.write(f"**Entity ID:** {log['entity_id']}")
            if log['details']:
                st.write("**Details:**")
                st.json(log['details'])