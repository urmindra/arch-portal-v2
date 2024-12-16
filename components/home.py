import streamlit as st

def render_home_page():
    st.title("Welcome to Enterprise Architecture Catalog")
    
    # Introduction
    st.markdown("""
    The Enterprise Architecture Catalog is a comprehensive platform for mapping and visualizing relationships 
    between enterprise capabilities, use cases, tools, and products. This interactive system helps you understand 
    and manage your organization's architectural landscape.
    """)
    
    # Key Features
    st.header("Key Features")

    st.subheader("Interactive Visualization")
    st.write("Explore relationships between different components through an interactive graph visualization.")

    st.subheader("Advanced Search")
    st.write("Find exactly what you need with powerful filtering and search capabilities.")

    st.subheader("Relationship Management")
    st.write("Create and manage relationships between different components of your enterprise architecture.")

    st.subheader("Smart Suggestions")
    st.write("Get intelligent relationship suggestions based on compatibility scoring.")

    # Entity Types Legend
    st.header("Entity Types")
    legend_col1, legend_col2 = st.columns(2)
    
    with legend_col1:
        st.markdown("""
        - **Capabilities**: Core enterprise capabilities
        - **Use Cases**: Business scenarios and applications
        """)
    
    with legend_col2:
        st.markdown("""
        - **Tools**: Implementation technologies
        - **Products**: Business solutions and offerings
        """)

    # Quick Start Guide
    st.header("Quick Start Guide")
    
    with st.expander("How to Use the Catalog"):
        st.markdown("""
        1. **Browse the Catalog**:
           - Use the navigation menu to switch between views
           - Click on nodes in the graph to see detailed information
           
        2. **Search and Filter**:
           - Use the sidebar filters to narrow down your view
           - Filter by entity type, tags, or search terms
           
        3. **View Relationships**:
           - Hover over connections to see relationship types
           - Use the minimum connections filter to focus on key entities
           
        4. **Admin Functions** (requires authentication):
           - Manage entities and relationships
           - Add new components to the catalog
        """)
    
    with st.expander("Understanding Relationships"):
        st.markdown("""
        Relationships in the catalog represent how different entities interact:
        
        - **enables**: One entity enables functionality in another
        - **implemented by**: Shows implementation relationships
        - **uses**: Indicates usage relationships
        - **supports**: Shows supporting relationships
        - **powered by**: Indicates underlying technology
        - **delivers**: Shows delivery relationships
        """)
    
    with st.expander("Tips and Best Practices"):
        st.markdown("""
        - Start with high-level capabilities and drill down
        - Use tags to group related entities
        - Regularly update relationships to maintain accuracy
        - Review suggested relationships for new insights
        - Keep descriptions clear and concise
        """)

    
