# 📦 库存管理系统 - 一键部署指南

本项目基于 Flask + SQLite，支持设备入库/出库管理。以下是在 **Ubuntu/Debian 系统** 上快速部署的完整步骤。

> ✅ 适用于干净的 Linux 服务器、LXC 容器或云主机（如 AWS EC2、阿里云 ECS）。

---

## 🚀 快速部署步骤

### 1. 更新系统并安装依赖

```bash
# 更新包列表
sudo apt update

# 安装 Python、pip、SQLite 和 Git
sudo apt install -y python3 python3-pip sqlite3 git unzip
```

---

### 2. 下载项目代码

```bash
# 从 GitHub 下载最新代码（ZIP 方式）
wget https://github.com/lutao114/inventory-system/archive/refs/heads/main.zip -O /tmp/main.zip

# 解压并复制到 /opt/inventory-system
sudo mkdir -p /opt/inventory-system
sudo unzip -q /tmp/main.zip -d /tmp/
sudo cp -r /tmp/inventory-system-main/* /opt/inventory-system/
sudo rm -rf /tmp/main.zip /tmp/inventory-system-main
```

---

### 3. 安装 Python 依赖

```bash
cd /opt/inventory-system
sudo pip3 install -r requirements.txt
```

> 💡 **建议**：生产环境应使用虚拟环境，此处为简化流程直接使用系统 pip。

---

### 4. 测试服务是否正常

```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 60 app:app
```

- 打开浏览器访问 `http://<你的服务器IP>:8000`
- 如果看到登录页面，说明服务正常 ✅
- 按 `Ctrl + C` 停止测试

---

### 5. 配置开机自启（systemd 服务）

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/inventory.service
```

粘贴以下内容：

```ini
[Unit]
Description=Inventory Management System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/inventory-system
ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 60 app:app
Restart=always
RestartSec=5
Environment=PATH=/usr/local/bin:/usr/bin

[Install]
WantedBy=multi-user.target
```

> ⚠️ 注意：`WorkingDirectory` 路径必须与实际项目路径一致（这里是 `/opt/inventory-system`）。

---

### 6. 启动并启用服务

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用开机自启
sudo systemctl enable inventory

# 启动服务
sudo systemctl start inventory

# 检查状态
sudo systemctl status inventory
```

验证是否已设置开机自启：
```bash
sudo systemctl is-enabled inventory  # 应返回 "enabled"
```

---

## 🔧 常用管理命令

| 操作 | 命令 |
|------|------|
| **停止服务** | `sudo systemctl stop inventory` |
| **重启服务** | `sudo systemctl restart inventory` |
| **查看实时日志** | `sudo journalctl -u inventory -f` |
| **禁用开机自启** | `sudo systemctl disable inventory` |

---

## 🌐 访问应用

部署完成后，通过以下地址访问系统：

```
http://<你的服务器公网IP>:8000
```

> 🔒 **安全建议**：  
> - 生产环境建议配置 Nginx 反向代理 + HTTPS（Let's Encrypt）  
> - 不要以 `root` 用户运行服务（可创建专用用户 `inventory`）  
> - 数据库 `inventory.db` 默认位于项目根目录，首次运行自动创建，请定期备份

---

## 📂 项目结构说明

```
/opt/inventory-system/
├── app.py              # 主程序
├── requirements.txt    # Python 依赖
├── inventory.db        # SQLite 数据库（首次运行自动创建）
├── uploads/            # 设备照片存储目录
└── init_db.py          # （如有）数据库初始化脚本
```

---
