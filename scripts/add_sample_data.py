from models.entities import EntityManager

def add_sample_data():
    # Dictionary to store entity IDs
    entity_ids = {}
    
    # Add Capabilities
    capabilities = [
        "Cloud Infrastructure Management",
        "Data Analytics Platform",
        "Security & Compliance",
        "API Management"
    ]
    for cap in capabilities:
        entity_ids[cap] = EntityManager.create_entity(cap, "Capability", f"Enterprise {cap} capability")

    # Add Use Cases
    use_cases = [
        "Real-time Data Processing",
        "User Authentication",
        "Resource Monitoring",
        "API Gateway Integration"
    ]
    for uc in use_cases:
        entity_ids[uc] = EntityManager.create_entity(uc, "Use Case", f"{uc} use case")

    # Add Tools
    tools = [
        "AWS Cloud Services",
        "Kubernetes",
        "Elasticsearch",
        "Kong API Gateway"
    ]
    for tool in tools:
        entity_ids[tool] = EntityManager.create_entity(tool, "Tool", f"{tool} implementation")

    # Add Products
    products = [
        "Customer Portal",
        "Analytics Dashboard",
        "Mobile App",
        "Payment Gateway"
    ]
    for product in products:
        entity_ids[product] = EntityManager.create_entity(product, "Product", f"{product} solution")

    # Create relationships
    relationships = [
        # Cloud Infrastructure Management relationships
        (entity_ids["Cloud Infrastructure Management"], entity_ids["Resource Monitoring"], "enables"),
        (entity_ids["Cloud Infrastructure Management"], entity_ids["AWS Cloud Services"], "implemented by"),
        (entity_ids["Cloud Infrastructure Management"], entity_ids["Kubernetes"], "uses"),

        # Data Analytics Platform relationships
        (entity_ids["Data Analytics Platform"], entity_ids["Real-time Data Processing"], "supports"),
        (entity_ids["Data Analytics Platform"], entity_ids["Elasticsearch"], "powered by"),
        (entity_ids["Data Analytics Platform"], entity_ids["Analytics Dashboard"], "delivers"),

        # API Management relationships
        (entity_ids["API Management"], entity_ids["API Gateway Integration"], "enables"),
        (entity_ids["API Management"], entity_ids["Kong API Gateway"], "implemented by"),
        (entity_ids["API Management"], entity_ids["Customer Portal"], "supports")
    ]

    for source_id, target_id, rel_type in relationships:
        EntityManager.create_relationship(source_id, target_id, rel_type)

    print("Sample data added successfully!")

if __name__ == "__main__":
    add_sample_data()
