#!/usr/bin/env bash
#
# One-time EC2 setup for the Library Management System on Amazon Linux 2023.
# Run from the project root as a sudo-capable user (e.g. ec2-user):
#
#   cd ~/library-management
#   bash deploy/setup_ec2.sh
#
# It installs Python, Nginx, and (optionally) MySQL, creates a virtualenv,
# installs the app, and wires up systemd + Nginx. Review before running.
#
# For Ubuntu, swap the `dnf` lines for `apt-get` equivalents and set
# APP_USER=ubuntu.

set -euo pipefail

APP_USER="${APP_USER:-ec2-user}"
APP_DIR="${APP_DIR:-/home/${APP_USER}/library-management}"
INSTALL_LOCAL_MYSQL="${INSTALL_LOCAL_MYSQL:-yes}"   # set to "no" if using RDS

echo ">>> Installing system packages..."
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip nginx git gcc

echo ">>> Creating virtualenv and installing dependencies..."
cd "${APP_DIR}"
python3.11 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

if [ "${INSTALL_LOCAL_MYSQL}" = "yes" ]; then
  echo ">>> Installing MariaDB (MySQL-compatible) server locally..."
  sudo dnf install -y mariadb105-server
  sudo systemctl enable --now mariadb
  echo ">>> Creating database and user (edit password in .env to match)..."
  sudo mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS library_db CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'library_user'@'localhost' IDENTIFIED BY 'library_pass';
GRANT ALL PRIVILEGES ON library_db.* TO 'library_user'@'localhost';
FLUSH PRIVILEGES;
SQL
fi

echo ">>> Ensuring .env exists..."
if [ ! -f "${APP_DIR}/.env" ]; then
  cp "${APP_DIR}/.env.production.example" "${APP_DIR}/.env"
  echo "    Created .env from example. EDIT IT NOW to set SECRET_KEY and DATABASE_URL."
fi

echo ">>> Creating database tables and seeding demo data..."
set -a; . "${APP_DIR}/.env"; set +a
./.venv/bin/python seed.py

echo ">>> Installing systemd service..."
sudo cp deploy/library.service /etc/systemd/system/library.service
sudo systemctl daemon-reload
sudo systemctl enable --now library

echo ">>> Configuring Nginx..."
sudo cp deploy/nginx-library.conf /etc/nginx/conf.d/library.conf
# SELinux (Amazon Linux) blocks Nginx from talking to the socket by default:
if command -v setsebool >/dev/null 2>&1; then
  sudo setsebool -P httpd_can_network_connect 1 || true
fi
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx

echo ">>> Done."
echo "    App: http://<EC2-PUBLIC-IP>/   (open port 80 in the security group)"
echo "    Service logs:  sudo journalctl -u library -f"
echo "    CHANGE the demo passwords and SECRET_KEY before real use."
