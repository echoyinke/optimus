# Optimus

Your ML project - 一个包含爬虫工具和分发器的机器学习项目。

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

## 环境配置

### 1. 安装 Python 包管理器 pip

```bash
sudo apt update && sudo apt install python3-pip
```

### 2. 安装 Poetry

使用 pip 安装 Poetry（Python 依赖管理工具）：

```bash
pip install poetry
```

### 3. 配置 PATH 环境变量

Poetry 安装后会被放在 `~/.local/bin` 目录中，需要将此目录添加到 PATH：

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 4. 验证安装

验证 Poetry 是否安装成功：

```bash
poetry --version
```

应该显示类似：`Poetry (version 2.1.3)`

### 5. 安装项目依赖

在项目根目录下运行：

```bash
poetry install
```

这将会：
- 创建虚拟环境
- 安装所有项目依赖
- 安装当前项目为可编辑模式

## 使用方法

### 激活虚拟环境

```bash
poetry shell
```

### 运行项目

```bash
# 在虚拟环境中运行 Python 脚本
poetry run python your_script.py
```

### 添加新依赖

```bash
# 添加运行时依赖
poetry add package_name

# 添加开发依赖
poetry add --group dev package_name
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
