# 公网部署说明

这套项目当前最适合部署为：

- `Streamlit` 应用进程
- `Nginx` 反向代理
- `HTTPS` 域名访问
- `Docker Compose` 常驻运行

## 1. 推荐公网结构

```text
Internet
  -> Nginx (80/443)
  -> Streamlit (8501)
```

## 2. 直接用 Docker 运行

先准备环境变量文件：

```bash
cp .env.public.example .env.public
```

然后修改：

- `APP_USERNAME`
- `APP_ACCESS_CODE_HASH`
- `PUBLIC_BASE_URL`

再启动：

```bash
docker compose --env-file .env.public -f docker-compose.public.yml up -d --build
```

默认登录账号：

```text
admin
```

默认密码采用 `SHA-256` 哈希配置在：

```text
.env.public
```

## 3. 修改公网登录密码

把你自己的密码做 SHA-256 后，填入：

```yaml
APP_ACCESS_CODE_HASH: "your_sha256_hash"
```

例如 Python 生成方式：

```python
import hashlib
print(hashlib.sha256("你的密码".encode("utf-8")).hexdigest())
```

## 4. 绑定域名

修改：

- `.env.public`
- `nginx.conf`

里的：

```text
your-domain.example.com
```

替换成你的真实域名。

## 5. HTTPS

推荐配合：

- `certbot`
- `nginx proxy manager`
- 或云厂商负载均衡证书

## 6. 上线前建议

- 修改默认账号密码
- 不要把 `.env.public` 提交到公开仓库
- 只开放 80/443 端口
- 服务器开启防火墙
- 定期备份 `config/ocr_rules.yaml`
- 后续如多人高频使用，建议继续拆分为 API + OCR Worker 架构

## 7. 一键部署命令

Linux 服务器上可以直接运行：

```bash
chmod +x deploy_public.sh
./deploy_public.sh
```
