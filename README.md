# arXiv Daily - 自动论文推送系统

自动抓取、翻译并推送 arXiv 论文到飞书群。

## 功能特性

- ✅ 自动抓取指定关键词的 arXiv 论文
- ✅ 自动翻译论文摘要为中文
- ✅ 推送到飞书群机器人
- ✅ 每日定时自动运行
- ✅ 网页查看历史论文
- ✅ 按抓取日期/发表日期筛选
- ✅ 收藏功能

## 项目结构

`
arxiv-daily/
├── data/                      # 数据目录
│   ├── papers.json           # 当天论文数据
│   ├── papers_translated.json # 翻译后的论文
│   └── papers_record.csv     # 历史记录
├── scripts/                   # Python 脚本
│   ├── arxiv_fetcher.py      # arXiv 检索
│   ├── config.yaml           # 配置文件
│   ├── translator.py         # 翻译模块
│   ├── feishu_notifier.py    # 飞书推送
│   ├── excel_manager.py      # CSV 管理
│   └── run_daily.py          # 主运行脚本
├── viewer/                    # 网页查看器
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── build_data.py
├── requirements.txt          # Python 依赖
└── run_task.bat             # Windows 定时任务脚本
`

## 快速开始

### 1. 环境准备

`ash
# 安装依赖
pip install -r requirements.txt
`

### 2. 配置文件

编辑 config.yaml：

`yaml
# arXiv 检索配置
arxiv:
  keywords:
    - "text-to-image"
    - "image-to-image"
    - "portrait generation"
    ...
  max_results: 50
  days_back: 1
  categories:
    - "cs.CV"
    - "cs.AI"
    ...

# 飞书推送配置
feishu:
  webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token"
  web_url: "xxx.xxx.xxx.xxx"  # 本机IP地址
`

### 3. 创建飞书机器人

1. 在飞书群中添加「自定义机器人」
2. 获取 Webhook 地址并配置到 config.yaml

详细教程：[飞书机器人创建指南](https://www.feishu.cn/content/7271149634339422210)

### 4. 手动运行测试

`ash
# 测试运行（跳过 PDF 下载）
python scripts/run_daily.py --skip_download

# 完整运行（PDF下载可能较慢）
python scripts/run_daily.py

# 仅查看论文
python viewer/run_viewer.py
`

### 5. 网页查看器功能说明

- 📅 按抓取日期/发表日期筛选
- 🔍 关键词搜索
- ⭐ 收藏功能
- 🔗 快速跳转到 arXiv 原文
- 📊 显示论文统计信息

## 目录说明

### scripts/

| 文件 | 说明 |
|------|------|
| arxiv_fetcher.py     | 从 arXiv API 检索论文 |
| translator.py        | 翻译摘要（支持 DeepL/DeepSeek） |
| feishu_notifier.py   | 推送消息到飞书 |
| excel_manager.py     | 管理 CSV 历史记录 |
| run_daily.py         | 主运行脚本 |
| pdf_downloader.py    | 下载 PDF（可选） |

### data/

- papers.json - 当天抓取的原始数据
- papers_translated.json - 翻译后的数据
- papers_record.csv - 累积的历史记录

## 常见问题

**Q: 飞书推送失败？**

A: 检查 webhook 地址是否正确，确认机器人未被移出群。

**Q: 网页无法访问？**

A: 确认已运行 python viewer/run_viewer.py，默认端口为 8765。

## 技术栈

- **后端**: Python 3.8+
- **前端**: 纯静态 HTML/CSS/JavaScript
- **数据存储**: JSON + CSV
- **API**: arXiv API, DeepL/DeepSeek, 飞书开放平台

## 许可证

MIT License

## 致谢

- [arXiv](https://arxiv.org/) - 开放论文库
- [DeepL](https://www.deepl.com/) - 翻译服务
- [飞书](https://www.feishu.cn/) - 团队协作平台
- [参考项目](https://github.com/genggng/hermes-arxiv-agent) - 基于 hermes 的 arxiv 抓取项目
