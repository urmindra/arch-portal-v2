import streamlit as st
from models.entities import EntityManager

def show_entity_details(entity_id):
    entity = EntityManager.get_entity(entity_id)
    if not entity:
        return
    
    st.subheader(entity['name'])
    st.write(f"Type: {entity['type']}")
    st.write(f"Description: {entity['description']}")
    
    # Show metadata if available
    if entity.get('metadata'):
        st.subheader("Metadata")
        for key, value in entity['metadata'].items():
            if isinstance(value, list):
                st.write(f"{key}: {', '.join(value)}")
            else:
                st.write(f"{key}: {value}")
    
    # Show related entities
    st.subheader("Related Entities")
    relationships = EntityManager.get_entity_relationships(entity_id)
    
    if relationships:
        for rel in relationships:
            st.write(f"{rel['relationship_type']}: {rel['related_entity_name']}")
    else:
        st.info("No existing relationships")
    
    # Show tags
    tags = EntityManager.get_entity_tags(entity_id)
    if tags:
        st.subheader("Tags")
        st.write(", ".join([tag['name'] for tag in tags]))
    
    # Show enhanced relationship suggestions
    st.subheader("Suggested Relationships")
    suggestions = EntityManager.suggest_relationships(entity_id)
    
    if suggestions:
        for suggestion in suggestions:
            target = suggestion['target_entity']
            score = suggestion['score']
            score_breakdown = suggestion['score_breakdown']
            
            with st.expander(f"🔍 {target['name']} (Overall Score: {score:.2f})"):
                # Score Breakdown
                st.write("**Score Breakdown:**")
                for component, component_score in score_breakdown.items():
                    st.write(f"- {component.replace('_', ' ').title()}: {component_score:.2f}")
                
                # Detailed Reasons
                st.write("\n**Why Suggested:**")
                for reason in suggestion['reasons']:
                    st.write(f"- {reason}")
                
                # Suggested Relationship Type
                if suggestion['suggested_relationship_type']:
                    st.write(f"\n**Suggested Relationship Type:** {suggestion['suggested_relationship_type']}")
                    relationship_type = suggestion['suggested_relationship_type']
                else:
                    # Allow custom relationship type if none suggested
                    relationship_type = st.text_input(
                        "Relationship Type",
                        value="related_to",
                        key=f"rel_type_{entity_id}_{target['id']}"
                    )
                
                # Create Relationship Button
                if st.button(f"Create Relationship with {target['name']}", 
                           key=f"create_rel_{entity_id}_{target['id']}"):
                    try:
                        EntityManager.create_relationship(entity_id, target['id'], relationship_type)
                        st.success("Relationship created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating relationship: {str(e)}")
    else:
        st.info("No relationship suggestions found.")
