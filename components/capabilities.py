import streamlit as st
from models.entities import EntityManager

def render_capabilities_page():
    st.title("Enterprise Capabilities")
    
    # Fetch capabilities from database
    capabilities = EntityManager.get_entities(entity_type="Capability")
    
    if not capabilities:
        st.info("No capabilities found. Please add some capabilities through the admin interface.")
        return
    
    # Sort capabilities alphabetically by name
    capabilities = sorted(capabilities, key=lambda x: x['name'])
    
    # Display capabilities in a grid layout
    cols = st.columns(2)  # Create 2 columns for the grid
    col_idx = 0
    
    for capability in capabilities:
        with cols[col_idx]:
            with st.expander(f"🔷 {capability['name']}"):
                with st.container():
                    # Create a card-like container with custom styling
                    st.markdown("""
                        <div style="
                            border: 1px solid #e6e6e6;
                            border-radius: 10px;
                            padding: 1.5rem;
                            margin-bottom: 1rem;
                            background-color: white;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                    """, unsafe_allow_html=True)
                    
                    # Display metadata in an organized way
                    if capability.get('metadata'):
                        st.markdown("**Details:**")
                        metadata = capability['metadata']
                        
                        # Display domain and maturity if available
                        if metadata.get('domain'):
                            st.write(f"🏢 Domain: {metadata['domain']}")
                        if metadata.get('maturity'):
                            st.write(f"📈 Maturity: {metadata['maturity']}")
                        if metadata.get('criticality'):
                            st.write(f"⚡ Criticality: {metadata['criticality']}")
                        
                        # Display technology stack as tags
                        if metadata.get('technology_stack'):
                            st.markdown("**Technology Stack:**")
                            tech_stack = metadata['technology_stack']
                            if isinstance(tech_stack, list):
                                for tech in tech_stack:
                                    st.markdown(f"""
                                        <span style="
                                            background-color: #e6e6e6;
                                            padding: 0.2rem 0.6rem;
                                            border-radius: 15px;
                                            margin-right: 0.5rem;
                                            font-size: 0.8rem;
                                        ">{tech}</span>
                                    """, unsafe_allow_html=True)
                    
                    # Get relationships for this capability
                    relationships = EntityManager.get_entity_relationships(capability['id'])
                    if relationships:
                        st.markdown("**Related Items:**")
                        for rel in relationships:
                            st.write(f"- {rel['related_entity_name']} ({rel['relationship_type']})")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # Toggle between columns for grid layout
        col_idx = (col_idx + 1) % 2

    # Add helpful tooltips
    st.sidebar.markdown("""
    ### Tips
    - Click on a capability card to expand/collapse details
    - Use the admin interface to add new capabilities
    - Capabilities show their relationships and tech stack
    """)
