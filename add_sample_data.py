from models.entities import EntityManager

def add_sample_data():
    # Dictionary to store entity IDs
    entity_ids = {}
    
    # Add Capabilities with metadata
    capabilities = [
        {
            "name": "Cloud Infrastructure Management",
            "metadata": {
                "domain": "Infrastructure",
                "maturity": "High",
                "criticality": "High",
                "technology_stack": ["Cloud", "DevOps"]
            }
        },
        {
            "name": "Data Analytics Platform",
            "metadata": {
                "domain": "Analytics",
                "maturity": "Medium",
                "criticality": "High",
                "technology_stack": ["Big Data", "Analytics"]
            }
        },
        {
            "name": "Security & Compliance",
            "metadata": {
                "domain": "Security",
                "maturity": "High",
                "criticality": "High",
                "technology_stack": ["Security", "Compliance"]
            }
        },
        {
            "name": "API Management",
            "metadata": {
                "domain": "Integration",
                "maturity": "High",
                "criticality": "High",
                "technology_stack": ["API", "Integration"]
            }
        }
    ]
    
    for cap in capabilities:
        try:
            entity_ids[cap["name"]] = EntityManager.create_entity(
                name=cap["name"],
                entity_type="Capability",
                description=f"Enterprise capability for {cap['name']}",
                metadata=cap["metadata"]
            )
            print(f"Created capability: {cap['name']}")
        except Exception as e:
            print(f"Error creating entity {cap['name']}: {str(e)}")

    # Add Use Cases with metadata
    use_cases = [
        {
            "name": "Real-time Data Processing",
            "metadata": {
                "domain": "Analytics",
                "complexity": "High",
                "priority": "High",
                "technology_stack": ["Big Data", "Stream Processing"]
            }
        },
        {
            "name": "User Authentication",
            "metadata": {
                "domain": "Security",
                "complexity": "Medium",
                "priority": "High",
                "technology_stack": ["Security", "IAM"]
            }
        },
        {
            "name": "Resource Monitoring",
            "metadata": {
                "domain": "Infrastructure",
                "complexity": "Medium",
                "priority": "High",
                "technology_stack": ["Monitoring", "DevOps"]
            }
        },
        {
            "name": "API Gateway Integration",
            "metadata": {
                "domain": "Integration",
                "complexity": "High",
                "priority": "High",
                "technology_stack": ["API", "Integration"]
            }
        }
    ]

    for uc in use_cases:
        try:
            entity_ids[uc["name"]] = EntityManager.create_entity(
                name=uc["name"],
                entity_type="Use Case",
                description=f"Use case for {uc['name']}",
                metadata=uc["metadata"]
            )
            print(f"Created use case: {uc['name']}")
        except Exception as e:
            print(f"Error creating entity {uc['name']}: {str(e)}")

    # Add Tools with metadata
    tools = [
        {
            "name": "AWS Cloud Services",
            "metadata": {
                "vendor": "AWS",
                "deployment": "Cloud",
                "technology_stack": ["Cloud", "Infrastructure"]
            }
        },
        {
            "name": "Kubernetes",
            "metadata": {
                "vendor": "CNCF",
                "deployment": "Hybrid",
                "technology_stack": ["Container", "DevOps"]
            }
        },
        {
            "name": "Elasticsearch",
            "metadata": {
                "vendor": "Elastic",
                "deployment": "Hybrid",
                "technology_stack": ["Search", "Analytics"]
            }
        },
        {
            "name": "Kong API Gateway",
            "metadata": {
                "vendor": "Kong",
                "deployment": "Hybrid",
                "technology_stack": ["API", "Integration"]
            }
        }
    ]

    for tool in tools:
        try:
            entity_ids[tool["name"]] = EntityManager.create_entity(
                name=tool["name"],
                entity_type="Tool",
                description=f"Implementation tool: {tool['name']}",
                metadata=tool["metadata"]
            )
            print(f"Created tool: {tool['name']}")
        except Exception as e:
            print(f"Error creating entity {tool['name']}: {str(e)}")

    # Create relationships
    relationships = [
        # Cloud Infrastructure Management relationships
        (entity_ids["Cloud Infrastructure Management"], entity_ids["Resource Monitoring"], "enables"),
        (entity_ids["Cloud Infrastructure Management"], entity_ids["AWS Cloud Services"], "implemented by"),
        (entity_ids["Cloud Infrastructure Management"], entity_ids["Kubernetes"], "uses"),

        # Data Analytics Platform relationships
        (entity_ids["Data Analytics Platform"], entity_ids["Real-time Data Processing"], "supports"),
        (entity_ids["Data Analytics Platform"], entity_ids["Elasticsearch"], "powered by"),

        # API Management relationships
        (entity_ids["API Management"], entity_ids["API Gateway Integration"], "enables"),
        (entity_ids["API Management"], entity_ids["Kong API Gateway"], "implemented by")
    ]

    for source_id, target_id, rel_type in relationships:
        try:
            EntityManager.create_relationship(source_id, target_id, rel_type)
            print(f"Created relationship: {rel_type}")
        except Exception as e:
            print(f"Error creating relationship: {str(e)}")

    print("Sample data processing completed!")

if __name__ == "__main__":
    add_sample_data()
