# Optimus

## 环境准备

### 1. 安装代理
```bash
# 克隆clash安装仓库
git clone --branch master --depth 1 https://gh-proxy.com/https://github.com/nelvko/clash-for-linux-install.git
cd clash-for-linux-install

# 执行安装脚本
sudo bash install.sh

# 更多配置请参考：https://github.com/nelvko/clash-for-linux-install
```

### 2. 安装Chrome浏览器
```bash
# 下载Chrome安装包
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

# 安装Chrome及其依赖
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
```

### 3. 安装Python和Poetry
...

## 项目配置

### 1. 安装项目依赖
```bash
# 在项目根目录下运行
poetry install
```

### 2. 运行项目
```bash
# 执行Twitter评论脚本
poetry run python -m distributors.twitter_v2.twitter_comment
```

## 项目结构

```
optimus/
├── crawlers/           # 爬虫模块
│   └── hentai/        # 特定网站爬虫
├── distributors/      # 分发器模块
│   ├── twitter_v1/    # Twitter API v1 相关功能
│   └── twitter_v2/    # Twitter API v2 相关功能
└── optimus_tools/     # 核心工具模块
```

## 依赖说明

主要依赖包括：
- `playwright`: 浏览器自动化工具
- `requests`: HTTP 请求库
- `tweepy`: Twitter API 客户端
- `matplotlib`: 数据可视化
- `tqdm`: 进度条显示

完整依赖列表请查看 `pyproject.toml` 文件。

## 注意事项

- 确保 Python 版本 >= 3.10
- 首次使用 Playwright 时可能需要安装浏览器：`playwright install`
- 某些功能可能需要额外的环境变量配置

## 开发

如果要为项目贡献代码，请：

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -am 'Add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

## 常用操作

### 代理相关

```bash
# 更新订阅
clashupdate https://your-subscription-link

# 启动代理
clashon

# 关闭代理
clashoff

# 查看代理状态
clash status

# 打开Web控制面板
clashui
```

### Chrome相关

```bash
# 查看Chrome版本
google-chrome --version

# 启动Chrome（无界面模式）
google-chrome --headless

# 启动Chrome（开发者模式）
google-chrome --auto-open-devtools-for-tabs

# 启动Chrome（禁用安全策略，用于开发测试）
google-chrome --disable-web-security --user-data-dir="/tmp/chrome-dev"
```

### Playwright相关

```bash
# 安装/更新Playwright浏览器
poetry run playwright install

# 运行Playwright测试
poetry run playwright test

# 调试模式运行测试
poetry run playwright test --debug

# 生成新的测试代码
poetry run playwright codegen

# 查看测试报告
poetry run playwright show-report
```

### 其他实用操作

```bash
# 检查系统资源使用情况
htop

# 查看网络连接状态
netstat -tunlp

# 查看磁盘使用情况
df -h

# 查看内存使用情况
free -h

# 系统日志查看
tail -f /var/log/syslog
```

## 故障排除

如果遇到以下问题，可以尝试相应的解决方案：

1. Chrome启动失败
   ```bash
   # 清理Chrome用户数据
   rm -rf ~/.config/google-chrome
   # 重新创建配置目录
   mkdir -p ~/.config/google-chrome
   ```

2. Playwright无法连接到浏览器
   ```bash
   # 重新安装浏览器
   poetry run playwright install --force
   ```

3. 系统依赖问题
   ```bash
   # 更新系统包
   sudo apt update
   sudo apt upgrade
   # 修复损坏的依赖
   sudo apt --fix-broken install
   ```
