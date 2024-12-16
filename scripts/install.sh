#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to prompt for environment variables
get_env_var() {
    local var_name=$1
    local var_desc=$2
    local current_value=$3
    local new_value=""

    if [ -n "$current_value" ]; then
        read -p "$var_desc (current: $current_value) - Press Enter to keep or enter new value: " new_value
        if [ -z "$new_value" ]; then
            new_value=$current_value
        fi
    else
        while [ -z "$new_value" ]; do
            read -p "$var_desc: " new_value
        done
    fi
    echo $new_value
}

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Create installation directory
INSTALL_DIR="/opt/enterprise-catalog"
mkdir -p $INSTALL_DIR
print_status "Created installation directory: $INSTALL_DIR"

# Load existing environment variables if present
if [ -f "$INSTALL_DIR/.env" ]; then
    source "$INSTALL_DIR/.env"
    print_warning "Found existing environment configuration"
fi

# Collect environment variables
print_status "Configuring environment variables..."
PGHOST=$(get_env_var "PGHOST" "Database host" "$PGHOST")
PGPORT=$(get_env_var "PGPORT" "Database port" "${PGPORT:-5432}")
PGDATABASE=$(get_env_var "PGDATABASE" "Database name" "${PGDATABASE:-enterprise_catalog}")
PGUSER=$(get_env_var "PGUSER" "Database user" "$PGUSER")
PGPASSWORD=$(get_env_var "PGPASSWORD" "Database password" "$PGPASSWORD")
ADMIN_PASSWORD=$(get_env_var "ADMIN_PASSWORD" "Admin interface password" "$ADMIN_PASSWORD")

# Write environment variables
cat > "$INSTALL_DIR/.env" << EOL
PGHOST=$PGHOST
PGPORT=$PGPORT
PGDATABASE=$PGDATABASE
PGUSER=$PGUSER
PGPASSWORD=$PGPASSWORD
ADMIN_PASSWORD=$ADMIN_PASSWORD
EOL
chmod 600 "$INSTALL_DIR/.env"
print_status "Environment configuration saved"

# Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y || {
    print_error "Failed to update system packages"
    exit 1
}

# Install system dependencies
print_status "Installing system dependencies..."
apt install -y python3.11 python3.11-dev python3-pip postgresql postgresql-contrib \
    libpq-dev supervisor nginx git || {
    print_error "Failed to install system dependencies"
    exit 1
}

# Start and enable PostgreSQL
print_status "Configuring PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER $PGUSER WITH PASSWORD '$PGPASSWORD';
CREATE DATABASE $PGDATABASE OWNER $PGUSER;
GRANT ALL PRIVILEGES ON DATABASE $PGDATABASE TO $PGUSER;
EOF

print_status "Database configured successfully"

# Install Python packages
print_status "Installing Python packages..."
pip3 install streamlit psycopg2-binary pyvis altair itsdangerous networkx pandas || {
    print_error "Failed to install Python packages"
    exit 1
}

# Clone repository
print_status "Cloning application repository..."
if [ -d "$INSTALL_DIR/.git" ]; then
    print_warning "Repository already exists, pulling latest changes..."
    cd $INSTALL_DIR
    git pull
else
    git clone https://github.com/yourusername/enterprise-catalog.git $INSTALL_DIR
fi

# Configure Supervisor
print_status "Configuring Supervisor..."
cat > /etc/supervisor/conf.d/enterprise-catalog.conf << EOF
[program:enterprise-catalog]
directory=$INSTALL_DIR
command=/usr/local/bin/streamlit run main.py --server.port 5000 --server.address 0.0.0.0
user=$SUDO_USER
autostart=true
autorestart=true
stderr_logfile=/var/log/enterprise-catalog/err.log
stdout_logfile=/var/log/enterprise-catalog/out.log
environment=
    PGHOST="$PGHOST",
    PGPORT="$PGPORT",
    PGDATABASE="$PGDATABASE",
    PGUSER="$PGUSER",
    PGPASSWORD="$PGPASSWORD",
    ADMIN_PASSWORD="$ADMIN_PASSWORD"
EOF

# Create log directory
mkdir -p /var/log/enterprise-catalog
chown -R $SUDO_USER:$SUDO_USER /var/log/enterprise-catalog

# Configure Nginx
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/enterprise-catalog << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

ln -sf /etc/nginx/sites-available/enterprise-catalog /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Start application
print_status "Starting application..."
supervisorctl reread
supervisorctl update
supervisorctl start enterprise-catalog

# Final status check
if supervisorctl status enterprise-catalog | grep -q RUNNING; then
    print_status "Installation completed successfully!"
    echo -e "\nApplication is now running and accessible at: http://localhost:5000"
    echo "Check logs with: sudo tail -f /var/log/enterprise-catalog/out.log"
else
    print_error "Installation completed but application failed to start"
    echo "Check logs with: sudo tail -f /var/log/enterprise-catalog/err.log"
fi
