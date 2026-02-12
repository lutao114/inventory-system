#!/bin/bash

set -e  # 遇错退出

PROJECT_NAME="inventory-system"
INSTALL_DIR="/opt/$PROJECT_NAME"
USER="inventory"
SERVICE_NAME="inventory.service"

echo "🚀 开始部署库存管理系统..."

# 1. 安装依赖
echo "📦 安装系统依赖..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git

# 2. 创建专用用户（安全最佳实践）
echo "👤 创建专用用户 $USER..."
sudo useradd -r -s /bin/false -d "$INSTALL_DIR" "$USER" 2>/dev/null || true

# 3. 克隆/复制代码
echo "📥 获取项目代码..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R "$USER:$USER" "$INSTALL_DIR"

if [ -d ".git" ]; then
    # 从当前目录部署（开发机）
    sudo cp -r . "$INSTALL_DIR/"
else
    # 从 GitHub 克隆（生产部署）
    sudo -u "$USER" git clone https://github.com/lutao114/inventory-system.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 4. 初始化虚拟环境
echo "🐍 创建 Python 虚拟环境..."
sudo -u "$USER" python3 -m venv venv
sudo -u "$USER" venv/bin/pip install --upgrade pip
sudo -u "$USER" venv/bin/pip install -r requirements.txt

# 5. 初始化数据库和上传目录
echo "🗃️ 初始化数据库..."
sudo -u "$USER" venv/bin/python init_db.py

echo "📂 创建上传目录..."
sudo -u "$USER" mkdir -p uploads
sudo -u "$USER" chmod 755 uploads

# 6. 创建 systemd 服务
echo "⚙️ 配置 systemd 服务..."
sudo tee "/etc/systemd/system/$SERVICE_NAME" > /dev/null <<EOF
[Unit]
Description=Inventory System
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# 7. 配置 Nginx（反向代理）
echo "🌐 配置 Nginx..."
sudo tee "/etc/nginx/sites-available/inventory" > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /uploads/ {
        alias $INSTALL_DIR/uploads/;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "🎉 部署成功！"
echo "👉 访问 http://$(hostname -I | awk '{print $1}')"

echo "📝 默认管理员账号请自行创建（通过注册页或手动插入数据库）"
