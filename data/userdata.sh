#!/bin/bash

# Update and install nginx
sudo apt-get update
sudo apt-get install -y nginx git

cd /home/ubuntu

# Clone your repository (replace 'repo' with the actual URL of your Git repository)
git clone https://github.com/UnpredictablePrashant/TravelMemory.git

# Remove existing nodejs and npm
sudo apt-get remove -y nodejs npm
sudo apt-get autoremove -y

# Install Node.js
curl -sL https://deb.nodesource.com/setup_current.x | sudo -E bash -
sudo apt-get install -y nodejs

# Set up your .env file
cd TravelMemory/backend
echo "MONGO_URI='mongodb+srv://*******:********@hvassign01.bzxol7m.mongodb.net/travelmem'" > .env
echo "PORT=\"3000\"" >> .env

# Install node packages and run the app
sudo npm install
nohup node index.js &

# Configure Nginx as a reverse proxy
sudo tee /etc/nginx/sites-available/default > /dev/null <<EOL
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Restart Nginx to apply changes
sudo systemctl restart nginx