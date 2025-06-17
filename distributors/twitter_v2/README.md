# Twitter 自动化系统

一个功能完整的Twitter自动化工具，支持推文发布和评论功能，具备断点恢复、实时保存、智能去重等企业级特性。

## 🚀 主要功能

### 📝 推文发布
- **批量发布推文** - 支持文本和图片（最多4张）
- **断点恢复** - 程序中断后可从上次位置继续
- **智能去重** - 基于文本+图片组合避免重复发布
- **实时保存** - 每条推文发布后立即保存进度

### 💬 评论功能
- **批量评论** - 对指定用户的推文进行评论
- **随机评论内容** - 从预设列表中随机选择评论
- **进度追踪** - 避免重复评论同一用户
- **实时保存** - 每次评论后立即保存进度

### 🛡️ 安全特性
- **人类行为模拟** - 随机鼠标移动、页面滚动、打字节奏
- **智能延迟** - 可配置的随机延迟时间
- **2FA支持** - 支持两步验证登录
- **Cookie管理** - 自动保存和加载登录状态
- **错误处理** - 自动截图、HTML保存、调试信息记录

## 📁 项目结构

```
new_twitter/
├── main.py                    # 主入口文件
├── config.py                  # 配置管理
├── twitter_common.py          # 通用功能（登录、行为模拟等）
├── twitter_post.py            # 推文发布功能
├── twitter_comment.py         # 评论功能
├── data/                      # 数据文件目录
│   ├── user_x_info.json      # 用户列表文件
│   ├── comment_text_list.json # 评论内容列表
│   └── tweet_content_list.json # 推文内容列表
├── progress/                  # 进度文件目录（断点恢复）
│   ├── comment_progress.json # 评论进度记录
│   └── tweet_progress.json   # 推文进度记录
├── results/                   # 详细结果保存目录
│   ├── comment_results_*.json # 评论详细结果
│   └── tweet_results_*.json   # 推文详细结果
├── cookies/                   # Cookie文件目录
│   └── {username}_cookies.json # Twitter登录Cookie（按用户名区分）
└── error_html/               # 错误页面保存目录
```

### 目录说明
- **data/** - 存放所有输入数据文件（用户列表、推文内容、评论内容）
- **progress/** - 存放断点恢复用的进度文件，程序中断后可从此恢复
- **results/** - 存放带时间戳的详细执行结果，用于分析和统计
- **cookies/** - 存放登录Cookie文件，按用户名区分，支持多账号切换
- **error_html/** - 存放错误时的页面截图和HTML，便于调试

## ⚙️ 配置说明

### 账号配置
在 `config.py` 中配置您的Twitter账号信息：

```python
TWITTER_CONFIG = {
    "USERNAME": "your_username",
    "EMAIL": "your_email@example.com", 
    "PASSWORD": "your_password",
    "TOTP_SECRET": "your_2fa_secret"  # 可选，2FA密钥
}
```

### 行为参数配置
```python
BEHAVIOR_CONFIG = {
    "MOUSE_MOVE_DELAY": (0.5, 2.0),      # 鼠标移动延迟范围
    "SCROLL_DELAY": (1, 3),              # 页面滚动延迟
    "TYPING_DELAY": (0.1, 0.3),          # 打字间隔
    "COMMENT_DELAY_MIN": 30,             # 评论间最小延迟（秒）
    "COMMENT_DELAY_MAX": 60,             # 评论间最大延迟（秒）
    "TWEET_DELAY_MIN": 30,               # 推文间最小延迟（秒）
    "TWEET_DELAY_MAX": 60,               # 推文间最大延迟（秒）
    "USER_DELAY_MIN": 10,                # 用户间最小延迟（秒）
    "USER_DELAY_MAX": 20                 # 用户间最大延迟（秒）
}
```

## 📋 数据文件格式

### 推文内容文件 (`tweet_content_list.json`)
```json
[
    {
        "text": "这是一条推文内容",
        "images": ["path/to/image1.jpg", "path/to/image2.jpg"]
    },
    {
        "text": "另一条推文",
        "images": []
    }
]
```

### 评论内容文件 (`comment_text_list.json`)
```json
[
    "很棒的分享！",
    "非常有用的信息",
    "感谢分享这个观点"
]
```

### 用户列表文件 (`user_x_info.json`)
```json
[
    {
        "screen_name": "username1",
        "name": "User One"
    },
    {
        "screen_name": "username2", 
        "name": "User Two"
    }
]
```

## 🚀 使用方法

### 1. 安装依赖
```bash
pip install playwright
playwright install chromium
```

### 2. 配置账号信息
编辑 `config.py` 文件，填入您的Twitter账号信息。

### 3. 准备数据文件
- 创建 `data/tweet_content_list.json` - 推文内容
- 创建 `data/comment_text_list.json` - 评论内容  
- 创建 `data/user_x_info.json` - 目标用户列表

### 4. 运行程序
```bash
python main.py
```

### 5. 选择功能
程序启动后会显示菜单：
```
=== Twitter 自动化工具 ===
1. 评论功能
2. 推文发布功能
3. 退出
请选择功能 (1-3):
```

## 📊 结果文件说明

### 进度记录文件（断点恢复用）
- `progress/comment_progress.json` - 已评论用户记录
- `progress/tweet_progress.json` - 已发布推文记录

### 详细结果文件（分析用）
- `results/comment_results_YYYYMMDD_HHMMSS.json` - 评论详细结果
- `results/tweet_results_YYYYMMDD_HHMMSS.json` - 推文详细结果

### 结果文件格式示例
```json
{
    "success": 8,
    "failed": 2,
    "details": [
        {
            "index": 1,
            "text": "推文内容或用户名",
            "success": true,
            "timestamp": "2024-12-01 14:30:22"
        }
    ]
}
```

## 🔧 高级功能

### 断点恢复
- 程序被中断后重新运行会自动跳过已完成的任务
- 基于文本+图片组合进行精确去重
- 支持部分完成任务的继续执行

### 实时保存
- 每完成一个任务立即保存进度
- 避免程序崩溃导致的数据丢失
- 支持实时查看处理进度

### 智能行为模拟
- 贝塞尔曲线鼠标轨迹
- 随机页面滚动和停顿
- 模拟人类打字节奏
- 随机延迟时间

### 错误处理
- 自动截图保存错误页面
- 详细的错误日志记录
- 元素高亮显示便于调试

## 🎯 使用建议

### 安全使用
1. **合理设置延迟时间** - 避免过于频繁的操作
2. **分批处理** - 不要一次性处理过多内容
3. **监控账号状态** - 注意是否有异常提示
4. **备份数据** - 定期备份配置和进度文件

### 性能优化
1. **使用断点恢复** - 大批量任务分多次完成
2. **检查网络状况** - 确保网络稳定
3. **关闭不必要程序** - 减少系统资源占用
4. **定期清理结果文件** - 避免磁盘空间不足

## 🔄 更新日志

### v2.0.0 (当前版本)
- ✅ 模块化重构，职责分离
- ✅ 实时保存机制，避免数据丢失
- ✅ 断点恢复功能，支持任务继续
- ✅ 智能去重，基于文本+图片组合
- ✅ 统一结果保存目录
- ✅ 优化加载性能，避免重复读取
- ✅ 完善错误处理和日志记录

### v1.0.0
- ✅ 基础推文发布功能
- ✅ 基础评论功能
- ✅ 简单的进度保存 