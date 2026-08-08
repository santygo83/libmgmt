#!/usr/bin/env bash
#
# Deploy the TaskBoard static site with Nginx on Amazon Linux 2023.
# Run from the project root:
#
#   bash deploy/setup_ec2.sh
#
# For Ubuntu: replace `dnf` with `apt-get`, and the conf.d path with
# sites-available + a symlink into sites-enabled.

set -euo pipefail

WEB_ROOT="${WEB_ROOT:-/var/www/taskboard}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ">>> Installing Nginx..."
sudo dnf install -y nginx

echo ">>> Copying site files to ${WEB_ROOT}..."
sudo mkdir -p "${WEB_ROOT}"
sudo cp -r "${PROJECT_DIR}/index.html" "${PROJECT_DIR}/css" "${PROJECT_DIR}/js" "${WEB_ROOT}/"

echo ">>> Installing Nginx site config..."
sudo cp "${PROJECT_DIR}/deploy/nginx-taskboard.conf" /etc/nginx/conf.d/taskboard.conf

# Amazon Linux's default nginx.conf ships a sample server on port 80 that can
# clash with ours. If you hit a conflict, comment out the `server { }` block in
# /etc/nginx/nginx.conf, then re-run `sudo nginx -t`.

echo ">>> Testing and starting Nginx..."
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx

echo ">>> Done."
echo "    Visit: http://<EC2-PUBLIC-IP>/   (open port 80 in the security group)"
echo "    Health: http://<EC2-PUBLIC-IP>/health"
