# TaskBoard — a no-database static web app

A tiny task board built with plain **HTML, CSS, and JavaScript**. There is no database and no
application server: Nginx serves the files directly, and all logic runs in the browser. Your
tasks are saved in the browser's `localStorage`, so they persist per-browser without any backend.

This is the simplest possible thing to deploy — ideal when you just need Nginx.

## What's inside

```
simple-webapp/
├── index.html                  # the page
├── css/style.css               # styling
├── js/app.js                   # app logic (add/complete/delete/filter tasks)
├── deploy/
│   ├── nginx-taskboard.conf    # Nginx server block
│   └── setup_ec2.sh            # one-shot deploy script (Amazon Linux 2023)
└── README.md
```

## Preview locally (optional)

Because it's all static, you can just open `index.html` in a browser. To mimic a real server:

```bash
# Python's built-in server — no install needed
python -m http.server 8000
# then visit http://localhost:8000
```

On Windows, `python -m http.server 8000` works the same in PowerShell from the project folder.

## Deploy on EC2 with Nginx

### 1. Launch an instance
Amazon Linux 2023, t2.micro/t3.micro. Security group: allow **SSH (22)** from your IP and
**HTTP (80)** from anywhere.

### 2. Get the files onto the instance
Either clone from GitHub:

```bash
sudo dnf install -y git
git clone <your-repo-url> taskboard && cd taskboard
```

…or copy from your laptop with scp:

```bash
scp -i your-key.pem -r D:\path\to\simple-webapp ec2-user@<EC2-PUBLIC-IP>:~/taskboard
```

### 3. Run the deploy script

```bash
bash deploy/setup_ec2.sh
```

It installs Nginx, copies the site to `/var/www/taskboard`, installs the server config, and
starts Nginx. Then visit `http://<EC2-PUBLIC-IP>/`.

### Manual version (what the script does)

```bash
sudo dnf install -y nginx
sudo mkdir -p /var/www/taskboard
sudo cp -r index.html css js /var/www/taskboard/
sudo cp deploy/nginx-taskboard.conf /etc/nginx/conf.d/taskboard.conf
sudo nginx -t
sudo systemctl enable --now nginx
```

## Updating the site later

Just replace the files and reload isn't even needed (static files are read per request):

```bash
sudo cp -r index.html css js /var/www/taskboard/
```

## Health check

`GET /health` returns `{"status":"UP"}` — handy for a load balancer or uptime monitor.

## Notes

- **Windows line endings:** if `bash deploy/setup_ec2.sh` fails with `$'\r'` errors, run
  `sudo dnf install -y dos2unix && dos2unix deploy/setup_ec2.sh` first.
- **Port 80 conflict:** Amazon Linux's default `nginx.conf` includes a sample `server` block on
  port 80. If `nginx -t` complains about a conflicting server name, comment out that default block
  in `/etc/nginx/nginx.conf` and re-test.
- **HTTPS:** add TLS with `sudo dnf install -y certbot python3-certbot-nginx && sudo certbot --nginx -d your-domain.com`.
