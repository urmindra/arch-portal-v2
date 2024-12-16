# Installation and Configuration Instructions

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Required environment variables (see Configuration section)

## 🐳 Docker Pre-requisites

### Required Docker Images
- `python:3.11-slim`: Base Python image (will be pulled automatically)
- `postgres:latest`: Required if running PostgreSQL in a container

### Docker Configuration
1. **Docker Installation**
   - Install Docker Engine from https://docs.docker.com/engine/install/
   - Verify installation: `docker --version`

2. **Network Setup**
```bash
# Create a dedicated network for service communication
docker network create enterprise-catalog-network
```

3. **PostgreSQL Container** (Optional, if not using external database)
```bash
# Run PostgreSQL container with proper configuration
docker run -d \
  --name postgres-db \
  --network enterprise-catalog-network \
  --restart unless-stopped \
  -e POSTGRES_USER=your_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=your_db \
  -v pgdata:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:latest
```

4. **Environment Setup**
   - Create `.env` file with all required credentials:
     ```
     PGHOST=postgres-db
     PGPORT=5432
     PGDATABASE=your_db
     PGUSER=your_user
     PGPASSWORD=your_password
     ADMIN_PASSWORD=your_secure_admin_password
     ```
   - Set appropriate file permissions: `chmod 600 .env`
   - Ensure network connectivity between containers

## 🐳 Docker Deployment

### Building the Docker Image
```bash
# Build the Docker image
docker build -t enterprise-catalog .
```

### Running the Container
```bash
# Run the container with environment variables
docker run -d \
  -p 5000:5000 \
  -e PGHOST=your_db_host \
  -e PGPORT=your_db_port \
  -e PGDATABASE=your_db_name \
  -e PGUSER=your_db_user \
  -e PGPASSWORD=your_db_password \
  -e ADMIN_PASSWORD=your_admin_password \
  enterprise-catalog
```

### Important Notes
- Ensure PostgreSQL is accessible from the container
- All environment variables must be properly configured
- The application will be available on http://localhost:5000
- Database connection will be retried automatically if initial connection fails

### Container Configuration
- Base image: Python 3.11-slim
- Exposed port: 5000
- Working directory: /app
- System dependencies: postgresql-client, python3-dev, libpq-dev
- Python packages: 
  - streamlit: Web interface framework
  - psycopg2-binary: PostgreSQL adapter
  - pyvis: Graph visualization
  - altair: Data visualization
  - itsdangerous: Security helpers
  - networkx: Graph operations
  - pandas: Data manipulation

## 🖥️ Linux VM Deployment Guide

### System Requirements
- Ubuntu 20.04 LTS or newer
- Root/sudo access
- Git (for cloning repository)

### Quick Installation (Automated)
Use the provided installation script for automated setup:

```bash
# Clone the repository
git clone <repository-url> enterprise-catalog
cd enterprise-catalog

# Make the installation script executable
chmod +x scripts/install.sh

# Run the installation script
sudo ./scripts/install.sh
```

The script will:
- Prompt for configuration values
- Install system dependencies
- Set up PostgreSQL database
- Configure the application
- Set up process management
- Start the application

### Manual Installation

If you prefer manual installation, follow these steps:

### Step 1: System Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.11 python3.11-dev python3-pip postgresql postgresql-contrib libpq-dev supervisor nginx

# Install Python packages
pip3 install streamlit psycopg2-binary pyvis altair itsdangerous networkx pandas
```

### Step 2: Database Setup
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE USER your_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE your_db OWNER your_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE your_db TO your_user;"
```

### Step 3: Application Setup
```bash
# Create application directory
sudo mkdir -p /opt/enterprise-catalog
sudo chown -R $USER:$USER /opt/enterprise-catalog

# Clone application repository
git clone <repository-url> /opt/enterprise-catalog
cd /opt/enterprise-catalog

# Create and configure environment file
cat > .env << EOL
PGHOST=localhost
PGPORT=5432
PGDATABASE=your_db
PGUSER=your_user
PGPASSWORD=your_password
ADMIN_PASSWORD=your_secure_admin_password
EOL

chmod 600 .env
```

### Step 4: Database Schema Creation

#### Option 1: Manual Schema Creation
Connect to your database and create the required tables:

```sql
-- Connect to database
psql -h localhost -U your_user -d your_db

-- Create entities table
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create relationships table
CREATE TABLE relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, relationship_type)
);

-- Create tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create entity_tags junction table
CREATE TABLE entity_tags (
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (entity_id, tag_id)
);

-- Create audit_log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    admin_user VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create admin_users table
CREATE TABLE admin_users (
    username VARCHAR(100) PRIMARY KEY,
    role VARCHAR(20) NOT NULL,
    failed_attempts INTEGER DEFAULT 0,
    last_failed_attempt TIMESTAMP,
    account_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_relationships_source ON relationships(source_id);
CREATE INDEX idx_relationships_target ON relationships(target_id);
CREATE INDEX idx_audit_log_admin ON audit_log(admin_user);
CREATE INDEX idx_audit_log_created ON audit_log(created_at);
```

#### Option 2: Database Migration from Development
If you prefer to migrate existing data from a development instance:

```bash
# Export data from development instance
pg_dump -h $PGHOST -U $PGUSER -d $PGDATABASE -F c -f backup.dump

# Copy backup file to production server
scp backup.dump user@production-server:/opt/enterprise-catalog/

# Import data on production server
pg_restore -h localhost -U your_user -d your_db backup.dump

# Clean up
rm backup.dump
```

### Step 5: Process Management
Create Supervisor configuration:
```bash
sudo nano /etc/supervisor/conf.d/enterprise-catalog.conf
```

Add the following content:
```ini
[program:enterprise-catalog]
directory=/opt/enterprise-catalog
command=/usr/local/bin/streamlit run main.py --server.port 5000 --server.address 0.0.0.0
user=your_username
autostart=true
autorestart=true
stderr_logfile=/var/log/enterprise-catalog/err.log
stdout_logfile=/var/log/enterprise-catalog/out.log
environment=
    PGHOST="localhost",
    PGPORT="5432",
    PGDATABASE="your_db",
    PGUSER="your_user",
    PGPASSWORD="your_password",
    ADMIN_PASSWORD="your_secure_admin_password"
```

Create log directory:
```bash
sudo mkdir -p /var/log/enterprise-catalog
sudo chown -R your_username:your_username /var/log/enterprise-catalog
```

### Step 6: Start Application
```bash
# Reload supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update

# Start the application
sudo supervisorctl start enterprise-catalog

# Check status
sudo supervisorctl status enterprise-catalog
```

### Step 7: Nginx Configuration (Optional)
If you want to serve the application through Nginx:

```bash
sudo nano /etc/nginx/sites-available/enterprise-catalog
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/enterprise-catalog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Troubleshooting
- Check application logs: `sudo tail -f /var/log/enterprise-catalog/out.log`
- Check error logs: `sudo tail -f /var/log/enterprise-catalog/err.log`
- Supervisor status: `sudo supervisorctl status`
- Database connection: `psql -h localhost -U your_user -d your_db`
- Process status: `ps aux | grep streamlit`
