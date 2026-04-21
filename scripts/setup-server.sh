#!/bin/bash
set -e

# =============================================================================
# 腾讯云服务器环境初始化脚本
# 支持 Ubuntu 20.04+/Debian 10+ 和 CentOS 7+/Rocky/AlmaLinux
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    else
        log_error "无法检测操作系统"
        exit 1
    fi
    log_info "检测到操作系统: $OS $VER"
}

install_docker_ubuntu() {
    log_info "安装 Docker (Ubuntu/Debian)..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg lsb-release

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/$OS/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl start docker
    systemctl enable docker
}

install_docker_centos() {
    log_info "安装 Docker (CentOS/RHEL/Rocky)..."
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    systemctl start docker
    systemctl enable docker
}

install_docker() {
    if command -v docker &> /dev/null; then
        log_warn "Docker 已安装，跳过"
        docker --version
    else
        detect_os
        case $OS in
            ubuntu|debian)
                install_docker_ubuntu
                ;;
            centos|rhel|rocky|almalinux|fedora)
                install_docker_centos
                ;;
            *)
                log_error "不支持的操作系统: $OS"
                exit 1
                ;;
        esac
        log_info "Docker 安装完成"
    fi
}

setup_docker_compose() {
    if docker compose version &> /dev/null; then
        log_info "Docker Compose Plugin 已安装"
        docker compose version
    elif command -v docker-compose &> /dev/null; then
        log_info "Docker Compose (standalone) 已安装"
        docker-compose --version
    else
        log_info "安装 Docker Compose..."
        # 安装 compose plugin 作为 fallback
        detect_os
        case $OS in
            ubuntu|debian)
                apt-get install -y docker-compose-plugin
                ;;
            centos|rhel|rocky|almalinux|fedora)
                yum install -y docker-compose-plugin
                ;;
        esac
    fi
}

setup_firewall() {
    log_info "配置防火墙..."
    # 开放 80/443 端口
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
        log_info "UFW 防火墙已配置"
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        log_info "firewalld 防火墙已配置"
    else
        log_warn "未检测到 UFW 或 firewalld，请手动开放 80/443 端口"
    fi
}

setup_swap() {
    # 腾讯云轻量服务器通常内存较小，建议配置 Swap
    if [ -f /swapfile ]; then
        log_warn "Swap 文件已存在，跳过"
        return
    fi

    MEM_MB=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$MEM_MB" -lt 4096 ]; then
        log_info "内存 ${MEM_MB}MB，创建 2GB Swap..."
        fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        log_info "Swap 创建完成"
    else
        log_info "内存 ${MEM_MB}MB，无需 Swap"
    fi
}

add_user_to_docker() {
    CURRENT_USER=${SUDO_USER:-$USER}
    if [ "$CURRENT_USER" != "root" ]; then
        usermod -aG docker "$CURRENT_USER"
        log_info "已将 $CURRENT_USER 添加到 docker 组，请重新登录后生效"
    fi
}

main() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用 sudo 运行此脚本"
        exit 1
    fi

    log_info "开始初始化服务器环境..."

    install_docker
    setup_docker_compose
    setup_firewall
    setup_swap
    add_user_to_docker

    log_info "服务器环境初始化完成！"
    log_info "建议执行: sudo reboot 或重新登录以应用用户组变更"
}

main "$@"
