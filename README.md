# Enterprise Architecture Catalog

A comprehensive enterprise architecture catalog portal built with Streamlit and PostgreSQL, featuring interactive graph visualization for mapping relationships between capabilities, use cases, tools, and products.

## 🌟 Key Features

- **Interactive Graph Visualization**: Explore relationships through an interactive graph interface with color-coded nodes
- **Multi-role Admin System**: Secure CRUD operations with Super Admin and Admin roles
- **Advanced Filtering**: Comprehensive filtering with entity types, tags, and relationships
- **Smart Suggestions**: Automated relationship suggestions using compatibility scoring
- **Audit Logging**: Track all administrative actions with detailed logging
- **Secure Authentication**: Protected admin interface with account lockout and session management
- **Bulk Operations**: Secure bulk deletion with preview functionality
- **Activity Dashboard**: Monitor admin activities with visual metrics

## 🛠️ Tech Stack

- **Frontend**: Streamlit with Quicksand Light Font, Custom CSS Navigation
- **Backend**: PostgreSQL, Python 3.11, Transaction Management
- **Infrastructure**: Docker containerization
- **Security**: Password Hashing, Session Management, Re-authentication, Account Lockout
- **Features**: Interactive Graph Visualization, Multi-role Admin Dashboard, Entity Management, Tag Management, Audit Logging, Activity Metrics Dashboard
- **Core Functions**: CRUD Operations, Relationship Mapping, Compatibility Scoring, Bulk Data Management
- **Documentation**: Setup Guide, Database Schema, Usage Guidelines, Entity Type Guide
- **Search & Filter**: Entity Type Filtering, Tag Filtering, Relationship Filters
- **UI**: Custom Input Styling (#e0e0e0), Streamlined Home Interface

## 📋 Getting Started

For detailed installation and deployment instructions, please refer to [INSTRUCTIONS.md](INSTRUCTIONS.md).

## 💡 Usage Guide

### Catalog Navigation
- Use the sidebar navigation to switch between different views:
  - **Home**: Introduction and overview
  - **Catalog**: Interactive graph visualization
  - **Capabilities**: Card-based view of enterprise capabilities
  - **Admin**: Entity and relationship management

### Graph Interaction
- Click and drag to move around the graph
- Scroll to zoom in/out
- Click nodes to view entity details
- Hover over connections to see relationship types
- Double-click nodes to focus on connections
- Toggle full screen mode for better visualization
- View color-coded legend for different entity types
- Access quick graph instructions via collapsible card

### Filtering Options
- Entity Type Filter with color-coded nodes
- Advanced Tag-based Filtering
- Search in Names/Descriptions
- Minimum Connections Filter
- Relationship Type Filter
- Date Range Filter
- Smart Search with field selection

### Admin Features
- Entity Management (Create, Update, Delete)
- Relationship Management
- Tag Administration
- Metadata Management

## 🗄️ Database Schema

### Tables
- `entities`: Stores core entity information
- `relationships`: Manages entity relationships
- `tags`: Global tag definitions
- `entity_tags`: Entity-tag associations

### Entity Types
- **Capabilities**: Enterprise-level capabilities
- **Use Cases**: Business scenarios
- **Tools**: Implementation technologies
- **Products**: Business solutions

### Relationship Types
- enables
- implemented by
- uses
- supports
- powered by
- delivers

## ⚙️ Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `ADMIN_PASSWORD`: Admin interface password
- `PGHOST`: Database host
- `PGPORT`: Database port
- `PGUSER`: Database user
- `PGPASSWORD`: Database password
- `PGDATABASE`: Database name

### Customization
Custom styling can be modified in `assets/styles.css`:
- Font settings (Quicksand Light)
- Color schemes
- Component styling
- Responsive design elements

## 🔍 Features in Detail

### Entity Management
- Create and modify entities with metadata
- Add and manage tags
- Update descriptions and relationships
- Delete entities with cascade

### Relationship Management
- Create directional relationships
- Update relationship types
- View and manage existing connections
- Automated relationship suggestions

### Visualization Options
- Interactive graph layout
- Color-coded entity types
- Relationship arrows with tooltips
- Zoom and pan controls

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with Streamlit
- Powered by PostgreSQL
- Graph visualization using PyVis
