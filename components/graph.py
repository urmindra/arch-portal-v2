import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile

def create_graph_visualization(entities, relationships):
    # Graph visualization section
    
    # Instructions in collapsed expander
    with st.expander("Graph Instructions", expanded=False):
        st.markdown("""
        - **Navigation**: Click and drag to move, scroll to zoom
        - **Interaction**: Click nodes to view details
        - **Relationships**: Hover over lines to see relationship types
        - **Focus**: Double-click nodes to focus on their connections
        """)
    
    # Legend in collapsed expander
    with st.expander("Graph Legend", expanded=False):
        cols = st.columns(4)
        with cols[0]:
            st.markdown('<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #ff7f0e; margin-right: 5px;"></span> **Capability**', unsafe_allow_html=True)
        with cols[1]:
            st.markdown('<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #1f77b4; margin-right: 5px;"></span> **Use Case**', unsafe_allow_html=True)
        with cols[2]:
            st.markdown('<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #2ca02c; margin-right: 5px;"></span> **Tool**', unsafe_allow_html=True)
        with cols[3]:
            st.markdown('<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #d62728; margin-right: 5px;"></span> **Product**', unsafe_allow_html=True)
    
    # Add full screen toggle button
    _, button_col = st.columns([6, 1])
    with button_col:
        if st.button(
            ("Exit Full Screen" if st.session_state.graph_fullscreen else "View Full Screen"),
            help="Toggle between full screen and normal view",
            use_container_width=True
        ):
            st.session_state.graph_fullscreen = not st.session_state.graph_fullscreen
            st.rerun()

    # Create network
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#333333")
    
    # Add nodes
    entity_colors = {
        "capability": "#ff7f0e",
        "use case": "#1f77b4",  # Fixed use case color mapping
        "tool": "#2ca02c",
        "product": "#d62728"
    }
    
    # Add nodes and track existing node IDs
    existing_node_ids = set()
    for entity in entities:
        net.add_node(
            entity['id'],
            label=entity['name'],
            title=f"{entity['type']}: {entity['description']}",
            color=entity_colors.get(entity['type'].lower(), "#gray"),
            size=30
        )
        existing_node_ids.add(entity['id'])
    
    # Add edges only between existing nodes
    for rel in relationships:
        source_id = rel['source_id']
        target_id = rel['target_id']
        
        # Only create edge if both nodes exist in our filtered set
        if source_id in existing_node_ids and target_id in existing_node_ids:
            net.add_edge(
                source_id,
                target_id,
                title=f"{rel['relationship_type']}\n{rel['source_name']} → {rel['target_name']}"
            )
    
    # Set network options with properly formatted JSON
    net.set_options('''{
    "physics": {
        "stabilization": {
            "iterations": 100,
            "fit": true
        },
        "barnesHut": {
            "gravitationalConstant": -2000,
            "springLength": 200,
            "springConstant": 0.04
        }
    },
    "nodes": {
        "font": {
            "size": 14,
            "face": "arial"
        },
        "borderWidth": 2,
        "shadow": true
    },
    "edges": {
        "smooth": {
            "type": "continuous"
        },
        "arrows": {
            "to": {
                "enabled": true,
                "scaleFactor": 0.5
            }
        },
        "shadow": true
    },
    "interaction": {
        "hover": true,
        "tooltipDelay": 200
    }
}''')
    
    # Generate HTML file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
        net.save_graph(tmp_file.name)
        with open(tmp_file.name, 'r', encoding='utf-8') as f:
            components.html(f.read(), height=600)

def display_graph_filters():
    st.sidebar.header("Filters")
    
    # Entity type filter with count
    entity_types = ["All", "Capability", "Use Case", "Tool", "Product"]
    selected_type = st.sidebar.selectbox("Entity Type", entity_types)
    
    # Enhanced search with multiple fields
    st.sidebar.subheader("Search")
    search_type = st.sidebar.radio("Search In:", ["Name", "Description", "All Fields"])
    search_term = st.sidebar.text_input(
        "Search Term", 
        help="Search in entity names, descriptions, and metadata"
    )
    
    # Tags filter with select all option
    from models.entities import EntityManager
    available_tags = EntityManager.get_tags()
    if available_tags:
        st.sidebar.subheader("Tags")
        select_all = st.sidebar.checkbox("Select All Tags")
        if select_all:
            selected_tags = available_tags
        else:
            selected_tags = st.sidebar.multiselect("Select Tags", available_tags)
    else:
        selected_tags = []
    
    # Advanced filters
    with st.sidebar.expander("Advanced Filters"):
        show_relationships = st.checkbox("Show Relationships", True)
        min_connections = st.slider("Minimum Connections", 0, 10, 0)
        relationship_types = st.multiselect(
            "Relationship Types",
            ["enables", "implemented by", "uses", "supports", "powered by", "delivers"]
        )
        
    # Date range filter
    with st.sidebar.expander("Date Filter"):
        date_filter = st.date_input(
            "Created After",
            value=None,
            help="Filter entities created after this date"
        )
    
    return {
        "type": selected_type,
        "search": search_term,
        "search_type": search_type,
        "tags": selected_tags,
        "show_relationships": show_relationships,
        "min_connections": min_connections,
        "relationship_types": relationship_types,
        "date_filter": date_filter
    }
