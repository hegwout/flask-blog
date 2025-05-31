#!/bin/bash

# 更新系统包
sudo apt-get update
sudo apt-get upgrade -y

# 安装必要的系统包
sudo apt-get install -y python3-pip python3-venv nginx

# 创建应用目录
sudo mkdir -p /var/www/cursor-blog
sudo chown -R $USER:$USER /var/www/cursor-blog

# 复制应用文件
cp -r ./* /var/www/cursor-blog/

# 创建并激活虚拟环境
cd /var/www/cursor-blog
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置 Nginx
sudo cp nginx.conf /etc/nginx/sites-available/cursor-blog
sudo ln -s /etc/nginx/sites-available/cursor-blog /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 启动 Gunicorn
gunicorn -c gunicorn_config.py app:app

# 设置开机自启
sudo tee /etc/systemd/system/cursor-blog.service << EOF
[Unit]
Description=Gunicorn instance to serve cursor-blog
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/cursor-blog
Environment="PATH=/var/www/cursor-blog/venv/bin"
ExecStart=/var/www/cursor-blog/venv/bin/gunicorn -c gunicorn_config.py app:app

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start cursor-blog
sudo systemctl enable cursor-blog 