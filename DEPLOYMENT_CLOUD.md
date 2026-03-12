# Spirit 云数据库部署方案

## 推荐方案对比

### 方案1：腾讯云轻量应用服务器 + 自建数据库（最便宜）

**购买一台包含数据库的轻量服务器：**
- **腾讯云轻量应用服务器 2核2G**
  - 价格：约 ¥40-50/月
  - 存储：60GB SSD
  - 包含：MySQL/PostgreSQL 可选

**部署架构：**
```
┌─────────────────────────────────┐
│     腾讯云轻量服务器 (2核2G)    │
│  ┌─────────────────────────┐   │
│  │    Docker 容器          │   │
│  │  ┌─────┐  ┌──────────┐  │   │
│  │  │API  │  │  Nginx   │  │   │
│  │  └─────┘  └──────────┘  │   │
│  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │
│  │    PostgreSQL          │   │
│  │    (原生安装)          │   │
│  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │
│  │    Redis               │   │
│  │    (原生安装)          │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
```

### 方案2：1核1G服务器 + 腾讯云托管数据库

| 服务 | 配置 | 月费用 | 优惠价 |
|------|------|--------|--------|
| CVM 1核1G | 20G SSD | ¥30 | 首年 ¥240 |
| PostgreSQL | 1核1G | ¥40 | 首年 ¥360 |
| Redis | 1核512MB | ¥25 | 首年 ¥225 |
| **合计** | | **¥95** | **首年 ¥825** |

### 方案3：1核1G服务器 + 第三方云数据库（性价比最高）

| 服务 | 提供商 | 配置 | 月费用 |
|------|--------|------|--------|
| CVM 1核1G | 腾讯云/阿里云 | 20G SSD | ¥30 |
| PostgreSQL | ElephantSQL | 20MB-1GB | **免费** |
| Redis | Redis Cloud | 30MB | **免费** |

---

## 具体操作：方案3（最省钱）

### Step 1：免费云数据库注册

**PostgreSQL - ElephantSQL（免费版）**
1. 访问 https://www.elephantsql.com/
2. 注册账号
3. 创建实例选择 "Free" 计划
4. 获取连接信息：
   - Host
   - Port
   - Database name
   - User
   - Password

**Redis - Redis Cloud（免费版）**
1. 访问 https://redis.cloud/
2. 注册账号
3. 创建免费订阅
4. 获取连接信息

### Step 2：购买腾讯云服务器

```bash
# 1. 访问 https://cloud.tencent.com/
# 2. 购买轻量应用服务器
#    - 地域：广州/上海
#    - 1核1G 20G SSD
#    - 系统：Ubuntu 20.04
#    - 价格：约 ¥30/月
```

### Step 3：服务器配置

```bash
# 连接服务器
ssh root@你的服务器IP

# 安装Docker
curl -fsSL https://get.docker.com | sh

# 启动Docker
systemctl start docker
systemctl enable docker
```

### Step 4：部署Spirit

```bash
# 创建目录
mkdir -p /opt/spirit && cd /opt/spirit

# 创建 .env 文件
cat > .env << 'EOF'
DEBUG=false
DATABASE_URL="postgresql://用户名:密码@主机地址:5432/数据库名"
REDIS_URL="redis://:密码@redis主机地址:6379"
SECRET_KEY="生成随机密钥"
OPENAI_API_KEY=""
EOF

# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  api:
    build: .
    container_name: spirit-api
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '0.8'
          memory: 600M

  nginx:
    image: nginx:alpine
    container_name: spirit-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api
    restart: unless-stopped

networks:
  default:
    name: spirit-network
EOF

# 创建 nginx.conf
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            root /usr/share/nginx/html;
            index index.html;
        }

        location /api/ {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /docs {
            proxy_pass http://api;
        }
    }
}
EOF

# 启动服务
docker-compose up -d
```

### Step 5：验证部署

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 测试API
curl http://localhost:8000/health
```

---

## 成本汇总

| 项目 | 价格 | 备注 |
|------|------|------|
| 腾讯云 1核1G | ¥30/月 | 首年优惠约 ¥240 |
| ElephantSQL | **免费** | 20MB-1GB |
| Redis Cloud | **免费** | 30MB |
| **首年总计** | **约 ¥240** | |

---

## 数据安全说明

 ElephantSQL 和 Redis Cloud 都是托管服务：
- ✅ 免费版有数据加密
- ✅ 自动备份
- ⚠️ 数据存储在境外服务器

如果对数据隐私要求高，建议：
1. 敏感思考内容开启端到端加密（系统已支持）
2. 或加钱用腾讯云国内数据库（¥90/月起）

---

## 常见问题

**Q：免费版够用吗？**
A：对于个人使用，免费版完全够用。ElephantSQL免费版有20MB-1GB，足够存储几万条思考记录。

**Q：连接速度慢吗？**
A：免费云数据库服务器在境外，国内访问可能有延迟。建议正式使用后升级到腾讯云数据库。

**Q：如何备份数据？**
A：系统已有数据导出功能（Markdown/JSON/PDF），建议定期手动导出备份。
