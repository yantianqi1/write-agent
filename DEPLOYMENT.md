# Write-Agent Deployment Guide

This guide covers deploying Write-Agent in a production environment using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Monitoring Setup](#monitoring-setup)
- [Backup Strategy](#backup-strategy)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 2GB RAM
- 10GB disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/write-agent.git
cd write-agent
```

### 2. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DATABASE_TYPE=sqlite
DATABASE_PATH=data/write_agent.db

# LLM Provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here

# Application
APP_NAME=WriteAgent
APP_ENV=production
LOG_LEVEL=info
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Check Health

```bash
curl http://localhost/health
```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_TYPE` | Database type (sqlite/postgresql) | sqlite |
| `LLM_PROVIDER` | LLM provider (anthropic/openai) | anthropic |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `APP_ENV` | Environment (development/production) | production |
| `LOG_LEVEL` | Logging level (debug/info/warning/error) | info |

### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | redis://localhost:6379/0 |
| `MAX_TOKENS` | Maximum tokens for LLM responses | 4096 |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | true |
| `RATE_LIMIT_PER_MINUTE` | Requests per minute | 60 |

## SSL/TLS Setup

### Using Let's Encrypt

1. Install Certbot:

```bash
sudo apt-get install certbot
```

2. Generate certificates:

```bash
sudo certbot certonly --standalone -d yourdomain.com
```

3. Copy certificates to SSL directory:

```bash
mkdir -p ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/chain.pem ssl/chain.pem
```

4. Update docker-compose.yml to use SSL nginx config:

```yaml
nginx:
  volumes:
    - ./nginx-ssl.conf:/etc/nginx/nginx.conf:ro
    - ./ssl:/etc/nginx/ssl:ro
  ports:
    - "80:80"
    - "443:443"
```

### Using Self-Signed Certificates (Development)

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

## Monitoring Setup

### Start Monitoring Stack

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

### Access Dashboards

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

### Configure Metrics in Application

The application exposes metrics at `/metrics` for Prometheus scraping.

## Backup Strategy

### Automated Backups

Set up a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/write-agent/scripts/backup.sh
```

### Manual Backup

```bash
./scripts/backup.sh
```

### Restore from Backup

```bash
./scripts/restore.sh backups/write_agent_backup_20240101_020000.db.gz
```

### Backup Retention

By default, backups are retained for 7 days. Adjust `RETENTION_DAYS` in the backup script.

## Troubleshooting

### Database Connection Issues

```bash
# Check database status
docker-compose exec api ls -la data/

# Reset database (WARNING: deletes all data)
docker-compose exec api rm data/write_agent.db
docker-compose restart api
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Adjust container limits in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
```

### LLM API Errors

Check your API key configuration and rate limits:

```bash
# View logs
docker-compose logs api | grep -i error

# Test API key
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: YOUR_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":1,"messages":[{"role":"user","content":"test"}]}'
```

### Nginx 502 Errors

```bash
# Check if backend is running
docker-compose ps

# Check backend logs
docker-compose logs api

# Restart services
docker-compose restart api nginx
```

## Security Checklist

- [ ] Change default passwords (Grafana, database)
- [ ] Enable SSL/TLS
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Backup strategy in place
- [ ] Monitor for suspicious activity

## Performance Tuning

### Database Optimization

For high-traffic deployments, use PostgreSQL:

```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=writeagent
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=writeagent
```

### Caching

Enable Redis for distributed caching:

```env
REDIS_URL=redis://redis:6379/0
CACHE_ENABLED=true
```

### Worker Scaling

Scale API workers:

```bash
docker-compose up -d --scale api=3
```

## Updates and Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Run database migrations
docker-compose exec api alembic upgrade head
```

### Monitor Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f api
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/write-agent/issues
- Documentation: https://github.com/yourusername/write-agent/wiki
