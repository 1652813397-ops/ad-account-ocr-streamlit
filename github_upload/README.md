# 广告账户 OCR 网页工具

一个基于 `PaddleOCR + Streamlit + Pandas` 的广告后台截图识别项目，支持批量上传截图、OCR 提取账户数据、结果汇总、复制文本和导出 Excel。

这份 README 按 `GitHub -> Streamlit Community Cloud -> 获取 .streamlit.app 地址` 的路径整理，目标是让你没有域名、没有服务器也能上线一个公网网页版本。

## 当前项目结构

```text
.
├─ app.py
├─ requirements.txt
├─ packages.txt
├─ .gitignore
├─ README.md
├─ config/
│  └─ ocr_rules.yaml
├─ .streamlit/
│  ├─ config.toml
│  └─ secrets.example.toml
└─ src/
   ├─ app_config.py
   ├─ auth.py
   ├─ config_loader.py
   ├─ exporter.py
   ├─ extractor.py
   ├─ models.py
   ├─ ocr_engine.py
   ├─ presenter.py
   ├─ text_utils.py
   ├─ ui.py
   └─ web_access.py
```

## 1. 本地运行

建议使用 Python `3.11`。这是为了和 `paddlepaddle==2.6.2` 保持兼容，避免 Streamlit Community Cloud 默认 Python `3.12` 带来的安装问题。

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 2. 为什么我已经帮你补了 `packages.txt`

根据 Streamlit Community Cloud 官方文档，Python 依赖放在 `requirements.txt`，Linux 系统依赖可以放在根目录的 `packages.txt`。  
这个项目使用了 `PaddleOCR + OpenCV + PaddlePaddle`，在 Linux 环境里通常需要额外系统库，所以我已经补了：

- `libgl1`
- `libglib2.0-0`
- `libsm6`
- `libxext6`
- `libxrender1`
- `libgomp1`

这些是为了提高在 Streamlit Community Cloud 上的成功构建概率。

## 3. 上传到 GitHub

### 方法 A：不会 Git，直接网页上传

如果你不想装 Git，直接用浏览器也能上传：

1. 打开 [GitHub](https://github.com/)
2. 登录账号
3. 点击右上角 `New repository`
4. 仓库名建议例如：`meta-ocr-streamlit`
5. 选择 `Public` 或 `Private`
6. 点击 `Create repository`
7. 进入新仓库后，点击 `Add file -> Upload files`
8. 把当前项目文件夹里的内容整体拖进去
9. 点击页面底部 `Commit changes`

注意：

- 不要上传 `.venv` 文件夹
- 不要上传 `.streamlit/secrets.toml`
- 当前项目里的 `.gitignore` 已经按这个目标配置好了

### 方法 B：命令行上传

如果你本机已经装了 Git，可以在项目目录执行：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的GitHub用户名/你的仓库名.git
git push -u origin main
```

如果你还没有仓库，先按上面的“方法 A”前 6 步在 GitHub 上创建一个空仓库，再回来执行 `git remote add origin` 和 `git push`。

如果你本机没有安装 Git：

1. 去 [Git for Windows](https://git-scm.com/download/win) 安装
2. 安装完成后重开终端
3. 再执行上面的命令

## 4. 部署到 Streamlit Community Cloud

官方入口：
[https://share.streamlit.io](https://share.streamlit.io)

部署步骤：

1. 用 GitHub 账号登录 Streamlit Community Cloud
2. 点击右上角 `Create app`
3. 选择你的 GitHub 仓库
4. Branch 选 `main`
5. Main file path 填 `app.py`
6. 点 `Advanced settings`
7. Python version 选择 `3.11`
8. Secrets 里可选填入登录配置
9. 点击 `Deploy`

### 推荐的 Secrets 配置

如果你想保留账号密码登录，可以直接参考项目里的 `.streamlit/secrets.example.toml`，或者把下面内容粘进 Streamlit Cloud 的 `Secrets`：

```toml
APP_AUTH_ENABLED = true
APP_USERNAME = "admin"
APP_ACCESS_CODE = "962464"
APP_TITLE = "广告账户 OCR 工作台"
APP_BADGE = "Community Cloud"
APP_BRAND = "Shared Workspace"
APP_SUPPORT_MESSAGE = "如遇识别误差，请继续补截图样本优化规则。"
```

如果你不填这些 Secrets，程序也能运行，只是不会启用登录门禁。

## 5. 如何拿到免费的 `.streamlit.app` 公网地址

根据 Streamlit 官方部署文档，部署成功后，你会获得一个唯一的 `https://...streamlit.app` 公网地址。  
在创建应用时，你可以直接填写一个你想要的 `App URL`，例如：

```text
meta-ocr-team.streamlit.app
```

如果这个地址没有被占用，部署完成后同事就可以直接打开它使用。

也就是说，流程是：

1. 推代码到 GitHub
2. 在 Streamlit Community Cloud 点 `Create app`
3. 选择仓库和 `app.py`
4. 成功后自动获得 `.streamlit.app` 公网地址

## 6. 这次我为适配 Streamlit Community Cloud 做了什么修改

- 补了 `packages.txt`
- 补了 `.gitignore`
- 把依赖版本固定到更稳的范围
- 把配置读取改成同时兼容环境变量和 `st.secrets`
- 保留了登录能力，但不强制依赖本地环境变量
- 保留了现有 OCR 主逻辑和页面功能

## 7. 当前核心功能

- 批量上传 `jpg/jpeg/png`
- OCR 自动识别：
  - 账户ID
  - 消耗
  - 注册
  - 订阅/购物
  - 展示
  - 点击
- 自动汇总
- 一键复制结果
- 导出 Excel
- 数值空值默认显示 `0`
- 可配置字段规则

## 8. Streamlit Community Cloud 注意事项

- 部署时务必把 Python 版本设成 `3.11`
- 第一次构建会比普通 Streamlit 项目慢，因为 `paddlepaddle` 比较大
- 第一次启动 OCR 时，服务器还可能下载 PaddleOCR 模型，所以首屏等待时间会更长一些
- 如果构建失败，先看右侧构建日志
- 如果登录配置没生效，优先检查 `Secrets` 是否保存成功

## 9. 如果部署失败，优先检查这几项

1. `requirements.txt` 是否在仓库根目录
2. `packages.txt` 是否在仓库根目录
3. 部署时 Python version 是否选成 `3.11`
4. `app.py` 是否是入口文件
5. GitHub 仓库是否已经 push 成功

## 10. 后续你可以继续让我做的事

- 帮你继续精简 Community Cloud 依赖，提升构建成功率
- 加一个更正式的登录页
- 针对更多 Meta 截图样本继续优化识别规则
- 如果 Community Cloud 性能不够，再迁移到 Docker / 云服务器版本
