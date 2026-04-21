#!/bin/bash
set -e

# =============================================================================
# 安全生产 BMS - 腾讯云一键部署脚本
# =============================================================================
# 用法：
#   1. 将项目代码上传到服务器（git clone 或 scp）
#   2. cd /path/to/safety-bms
#   3. sudo bash scripts/deploy.sh
# =============================================================================

PROJECT_NAME="safety-bms"
COMPOSE_FILE="docker-compose.yml"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}>>> $1${NC}"
}

# ---------------------------------------------------------------------------
# 检查前置条件
# ---------------------------------------------------------------------------
check_prerequisites() {
    log_step "检查前置条件"

    if ! command -v docker &> /dev/null; then
        log_error "未检测到 Docker，请先运行: sudo bash scripts/setup-server.sh"
        exit 1
    fi

    if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
        log_error "未检测到 Docker Compose，请先运行: sudo bash scripts/setup-server.sh"
        exit 1
    fi

    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "未找到 $COMPOSE_FILE，请确保在项目根目录运行此脚本"
        exit 1
    fi

    log_info "前置条件检查通过"
}

# ---------------------------------------------------------------------------
# 生成生产环境 .env 文件
# ---------------------------------------------------------------------------
setup_env() {
    log_step "配置环境变量"

    if [ -f ".env" ]; then
        log_warn ".env 文件已存在"
        read -p "是否覆盖? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            log_info "跳过 .env 配置，使用现有文件"
            return
        fi
    fi

    # 获取服务器公网 IP
    SERVER_IP=$(curl -s -4 https://api.ip.sb/ip 2>/dev/null || curl -s -4 https://httpbin.org/ip 2>/dev/null | grep -oP '"origin":\s*"\K[^"]+' || echo "")
    if [ -z "$SERVER_IP" ]; then
        read -p "请输入服务器公网 IP 或域名: " SERVER_IP
    else
        log_info "检测到公网 IP: $SERVER_IP"
        read -p "使用此 IP? (Y/n) 或输入域名: " confirm
        if [[ "$confirm" =~ ^[Nn]$ ]]; then
            read -p "请输入服务器公网 IP 或域名: " SERVER_IP
        fi
    fi

    # 生成随机密码和密钥
    DB_PASSWORD=$(openssl rand -base64 24 2>/dev/null || head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 24)
    MINIO_SECRET_KEY=$(openssl rand -base64 24 2>/dev/null || head -c 24 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 24)
    SECRET_KEY=$(openssl rand -base64 48 2>/dev/null || head -c 48 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 48)

    cat > .env <<EOF
# =============================================================================
# 安全生产 BMS - 生产环境配置
# 生成时间: $(date '+%Y-%m-%d %H:%M:%S')
# =============================================================================

# ---------------------------------------------------------------------------
# 数据库 (Docker 内部网络，使用服务名连接)
# ---------------------------------------------------------------------------
DB_HOST=postgres
DB_PORT=5432
DB_NAME=safety_bms
DB_USER=postgres
DB_PASSWORD=$DB_PASSWORD

# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# ---------------------------------------------------------------------------
# JWT 安全 (务必使用强密钥，至少 32 位)
# ---------------------------------------------------------------------------
SECRET_KEY=$SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7

# ---------------------------------------------------------------------------
# 调试模式 (生产环境必须为 false)
# ---------------------------------------------------------------------------
DEBUG=false

# ---------------------------------------------------------------------------
# CORS 允许来源 (精确设置为你的域名或 IP)
# 示例: ["https://bms.example.com"] 或 ["http://$SERVER_IP"]
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS=["http://$SERVER_IP"]

# ---------------------------------------------------------------------------
# MinIO 对象存储
# ---------------------------------------------------------------------------
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=$MINIO_SECRET_KEY
MINIO_BUCKET=safety-bms
MINIO_SECURE=false
EOF

    log_info ".env 文件已生成"
    log_warn "请检查 .env 文件中的配置，特别是 ALLOWED_ORIGINS 是否需要改为域名"
    echo ""
    echo "========================================"
    echo "数据库密码: $DB_PASSWORD"
    echo "MinIO 密钥: $MINIO_SECRET_KEY"
    echo "JWT 密钥:   $SECRET_KEY"
    echo "========================================"
    echo ""
    read -p "确认配置无误后按 Enter 继续..."
}

# ---------------------------------------------------------------------------
# 创建必要目录
# ---------------------------------------------------------------------------
setup_directories() {
    log_step "创建数据目录"
    mkdir -p backups ssl
    log_info "目录创建完成: backups/, ssl/"
}

# ---------------------------------------------------------------------------
# 拉取/构建镜像并启动
# ---------------------------------------------------------------------------
deploy() {
    log_step "拉取基础镜像并构建"
    docker compose pull
    docker compose build --no-cache

    log_step "启动服务"
    docker compose up -d

    log_step "等待服务就绪 (约 30 秒)..."
    sleep 10

    # 等待 backend 健康检查通过
    for i in {1..30}; do
        if docker compose ps backend | grep -q "healthy"; then
            log_info "Backend 服务已就绪"
            break
        fi
        echo -n "."
        sleep 2
    done
    echo ""
}

# ---------------------------------------------------------------------------
# 显示部署结果
# ---------------------------------------------------------------------------
show_result() {
    log_step "部署完成"

    SERVER_IP=$(curl -s -4 https://api.ip.sb/ip 2>/dev/null || echo "服务器")

    echo ""
    echo "========================================"
    echo "  🎉 安全生产 BMS 部署成功!"
    echo "========================================"
    echo ""
    echo "📍 访问地址:"
    echo "   前端页面: http://$SERVER_IP"
    echo ""
    echo "👤 初始账号:"
    echo "   用户名: admin"
    echo "   密码:   admin123"
    echo ""
    echo "📁 数据持久化:"
    echo "   PostgreSQL: Docker Volume (postgres_data)"
    echo "   备份目录:   ./backups/"
    echo ""
    echo "🔧 常用命令:"
    echo "   查看日志:   docker compose logs -f backend"
    echo "   重启服务:   docker compose restart"
    echo "   停止服务:   docker compose down"
    echo "   更新部署:   docker compose pull && docker compose up -d --build"
    echo ""
    echo "⚠️  安全提醒:"
    echo "   1. 生产环境请务必配置 HTTPS (将 SSL 证书放入 ./ssl/ 目录)"
    echo "   2. 尽快修改 admin 密码"
    echo "   3. 定期查看 ./backups/ 目录的数据库备份"
    echo ""
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
main() {
    log_info "开始部署安全生产 BMS..."

    check_prerequisites
    setup_env
    setup_directories
    deploy
    show_result
}

main "$@"
