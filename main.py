import streamlit as st
from components.graph import create_graph_visualization, display_graph_filters
from components.admin import render_admin_interface
from components.entity_details import show_entity_details
from components.home import render_home_page
from components.capabilities import render_capabilities_page
from models.entities import EntityManager
from utils.auth import check_password

st.set_page_config(
    page_title="Enterprise Architecture Catalog",
    page_icon="🏢",
    layout="wide"
)

def load_css():
    with open('assets/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load CSS
load_css()

# Initialize session state
if 'selected_entity' not in st.session_state:
    st.session_state.selected_entity = None

def main():
    # Top navigation
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    
    # Get current page
    current_page = st.query_params.get("page", "Home")
    
    cols = st.columns([6,1,1,1,1])  # Balanced spacing
    
    _, col1, col2, col3, col4 = cols
    
    with col1:
        if st.button("Home", key="nav_home", 
                    help="Go to Home page",
                    use_container_width=True,
                    type="primary" if current_page == "Home" else "secondary"):
            st.query_params["page"] = "Home"
            st.rerun()
    
    with col2:
        if st.button("Catalog", key="nav_catalog",
                    help="View Enterprise Catalog",
                    use_container_width=True,
                    type="primary" if current_page == "Catalog" else "secondary"):
            st.query_params["page"] = "Catalog"
            st.rerun()
    
    with col3:
        if st.button("Capabilities", key="nav_capabilities",
                    help="View Enterprise Capabilities",
                    use_container_width=True,
                    type="primary" if current_page == "Capabilities" else "secondary"):
            st.query_params["page"] = "Capabilities"
            st.rerun()
    
    with col4:
        if st.button("Admin", key="nav_admin",
                    help="Access Admin Dashboard",
                    use_container_width=True,
                    type="primary" if current_page == "Admin" else "secondary"):
            st.query_params["page"] = "Admin"
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get the current page from query parameters
    page = st.query_params.get("page", "Home")
    
    if page == "Home":
        render_home_page()
    
    elif page == "Capabilities":
        render_capabilities_page()
    
    elif page == "Catalog":
        st.title("Enterprise Architecture Catalog")
        # Get enhanced filters
        filters = display_graph_filters()
        
        # Get filtered data with enhanced parameters
        entities = EntityManager.get_entities(
            entity_type=filters["type"],
            search_term=filters["search"],
            search_type=filters["search_type"],
            tags=filters["tags"],
            date_filter=filters["date_filter"],
            relationship_types=filters["relationship_types"]
        )
        
        relationships = EntityManager.get_relationships(
            entity_type=filters["type"],
            search_term=filters["search"],
            relationship_types=filters["relationship_types"]
        ) if filters["show_relationships"] else []
        
        # Filter based on minimum connections if specified
        if filters["min_connections"] > 0:
            entity_connections = {}
            for rel in relationships:
                entity_connections[rel['source_id']] = entity_connections.get(rel['source_id'], 0) + 1
                entity_connections[rel['target_id']] = entity_connections.get(rel['target_id'], 0) + 1
            
            entities = [e for e in entities if entity_connections.get(e['id'], 0) >= filters["min_connections"]]
        
        # Initialize fullscreen state if not exists
        if 'graph_fullscreen' not in st.session_state:
            st.session_state.graph_fullscreen = False

        if not entities:
            st.warning("No entities found matching the current filters.")
        else:
            if st.session_state.graph_fullscreen:
                # Full screen mode - create visualization directly
                create_graph_visualization(entities, relationships)
                st.info(f"Showing {len(entities)} entities and {len(relationships)} relationships")
                
                # Show entity details in the sidebar when in fullscreen
                if st.session_state.selected_entity:
                    with st.sidebar:
                        show_entity_details(st.session_state.selected_entity)
            else:
                # Normal split view - create visualization in left column
                col1, col2 = st.columns([7, 3])
                with col1:
                    create_graph_visualization(entities, relationships)
                    st.info(f"Showing {len(entities)} entities and {len(relationships)} relationships")
                
                if st.session_state.selected_entity:
                    with col2:
                        show_entity_details(st.session_state.selected_entity)
                
                # Add filter summary (shown in both modes)
                with st.expander("Active Filters"):
                    if filters["type"] != "All":
                        st.write(f"Type: {filters['type']}")
                    if filters["search"]:
                        st.write(f"Search: '{filters['search']}' in {filters['search_type']}")
                    if filters["tags"]:
                        st.write(f"Tags: {', '.join(filters['tags'])}")
                    if filters["relationship_types"]:
                        st.write(f"Relationship Types: {', '.join(filters['relationship_types'])}")
                    if filters["date_filter"]:
                        st.write(f"Created After: {filters['date_filter']}")
        
        if not st.session_state.graph_fullscreen:
            with col2:
                if st.session_state.selected_entity:
                    show_entity_details(st.session_state.selected_entity)
    
    elif page == "Admin":
        # First check if already authenticated
        if "admin_role" in st.session_state and st.session_state["admin_role"]:
            render_admin_interface()
        # If not authenticated, try to authenticate
        elif check_password():
            render_admin_interface()
        # Authentication failed or not attempted yet
        else:
            st.stop()

if __name__ == "__main__":
    main()
