<div align="center">

![EndStone-EasyCheckUpdate](https://socialify.git.ci/MengHanLOVE1027/endstone-easycheckupdate/image?custom_language=Python&description=1&font=Inter&forks=1&issues=1&language=1&logo=https://zh.minecraft.wiki/images/BE_icon_recipe_all.png?8a449&format=original&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

<h3>EndStone-EasyCheckUpdate</h3>

<p>
  <b>一个基于 EndStone 的插件更新检查工具 / A plugin update checker based on EndStone.</b>

Powered by EndStone.<br>

</p>

[![README](https://img.shields.io/badge/README-中文|Chinese-blue)](README.md) [![README_EN](https://img.shields.io/badge/README-英文|English-blue)](README_EN.md)

[![Github Version](https://img.shields.io/github/v/release/MengHanLOVE1027/endstone-easycheckupdate)](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases) [![GitHub License](https://img.shields.io/badge/License-AGPL3.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0) [![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-EndStone-9cf.svg)](https://endstone.io) [![Downloads](https://img.shields.io/github/downloads/MengHanLOVE1027/endstone-easycheckupdate/total.svg)](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases)

</div>
<div align="center">

[![Github Version](https://img.shields.io/github/v/release/MengHanLOVE1027/endstone-easycheckupdate)](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases) [![GitHub License](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0) [![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-EndStone-9cf.svg)](https://endstone.io)

</div>

---

## 📖 简介

EndStone-EasyCheckUpdate 是一个专为 EndStone 服务器设计的插件更新检查工具。它可以自动检查服务器上已安装插件是否有可用更新，并支持一键更新功能。插件支持通过自定义的 JSON 文件来获取更新信息，为服务器管理员提供便捷的插件管理体验。

---

## ✨ 核心特性

| 特性             | 描述                         |
| ---------------- | ---------------------------- |
| 🔍**自动检查更新** | 定期检查所有插件的更新状态   |
| 📝**自定义更新源** | 支持通过 JSON 文件指定更新信息 |
| 🔄**一键更新**   | 支持自动下载并更新插件       |
| 🕒**定时检查**   | 可配置的检查间隔             |
| 💾**自动备份**   | 更新前自动备份旧版本插件     |
| 📊**版本比较**   | 智能比较版本号，支持多种格式 |

---

## 🗂️ 目录结构

```
服务器根目录/
├── logs/
│   └── EasyCheckUpdate/                 # 日志目录
│       └── easycheckupdate_YYYYMMDD.log  # 主日志文件
├── plugins/
│   ├── endstone_easycheckupdate-x.x.x-py3-none-any.whl  # 插件主文件
│   └── EasyCheckUpdate/                 # 插件资源目录
│       └── config/
│           └── easycheckupdate.json     # 配置文件
```

---

## 🚀 快速开始

### 安装步骤

1. **下载插件**
   - 从 [Release页面](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases) 下载最新版本

2. **安装插件**

   ```bash
   # 将插件主文件复制到服务器 plugins 目录
   cp endstone_easycheckupdate-x.x.x-py3-none-any.whl plugins/
   ```

3. **配置插件**
   - 编辑 `plugins/EasyCheckUpdate/config/easycheckupdate.json` 配置文件
   - 根据需要自定义检查间隔和延迟时间

4. **启动服务器**
   - 重启服务器或使用 `/reload` 命令
   - 插件会自动生成默认配置文件

---

## ⚙️ 配置详解

配置文件位于：`plugins/EasyCheckUpdate/config/easycheckupdate.json`

### 📋 主要配置项

```json
{
  "check_update_on_load": true,
  "check_interval": 1800,
  "check_delay": 10,
  "last_check_time": 0
}
```

### 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| check_update_on_load | 布尔值 | true | 服务器启动时是否自动检查更新 |
| check_interval | 整数 | 1800 | 自动检查更新的间隔时间（秒），默认为30分钟 |
| check_delay | 整数 | 10 | 服务器启动后延迟检查更新的时间（秒），默认为10秒 |
| last_check_time | 整数 | 0 | 上次检查更新的时间戳，插件自动维护 |

---

## 🎮 命令手册

### 管理员命令

| 命令                              | 描述               |
| --------------------------------- | ------------------ |
| `/checkupdate` | 检查所有插件的更新 |
| `/checkupdate <插件名称>` | 检查指定插件的更新 |
| `/checkupdate <插件名称> update` | 检查并更新指定插件 |
| `/cu` | `/checkupdate` 的简写形式 |

### 权限说明

| 权限节点 | 描述 |
| -------- | ---- |
| easycheckupdate.command.use | 允许使用检查更新命令（默认仅OP可用） |

---

## 🔧 开发者指南

### 如何为插件添加更新检查支持

要让您的插件支持 EasyCheckUpdate 的自动更新检查，您需要在插件类中添加 `update_url` 属性，该属性应指向一个包含更新信息的 JSON 文件 URL。

#### 1. 添加 update_url 属性

在您的插件类中添加 `update_url` 属性：

```python
class YourPlugin(Plugin):
    name = "your_plugin_name"
    version = "1.0.0"
    update_url = "https://example.com/your_plugin_version.json"  # 添加此行
    
    def __init__(self):
        super().__init__()
        # 其他初始化代码
```

#### 2. 创建更新信息 JSON 文件

创建一个包含插件更新信息的 JSON 文件，并将其上传到可访问的服务器上。JSON 文件应包含以下字段：

```json
{
    "version": "1.0.1",
    "download_url": "https://example.com/downloads/your_plugin-1.0.1.whl",
    "update_content": "修复了一些bug，添加了新功能",
    "author": "您的名字",
    "update_time": "2023-10-01 12:00:00"
}
```

#### 3. JSON 文件字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| version | 字符串 | 是 | 最新版本号 |
| download_url | 字符串 | 是 | 最新版本的下载链接 |
| update_content | 字符串 | 否 | 更新内容说明 |
| author | 字符串 | 否 | 插件作者 |
| update_time | 字符串 | 否 | 更新发布时间 |

#### 4. 版本号格式说明

EasyCheckUpdate 支持多种版本号格式，包括但不限于：
- 标准版本号：`1.0.0`, `2.1.3`
- 带前缀的版本号：`v1.0.0`, `V2.1.3`
- 带后缀的版本号：`1.0.0-beta`, `2.1.3-rc1`

版本比较会自动忽略 `v` 或 `V` 前缀，并逐段比较数字部分。如果某一段无法转换为数字，则按字符串比较。

#### 5. 完整示例

以下是一个完整的插件示例：

```python
from endstone.plugin import Plugin

class MyAwesomePlugin(Plugin):
    name = "my_awesome_plugin"
    version = "1.0.0"
    update_url = "https://raw.githubusercontent.com/yourusername/my_awesome_plugin/main/version.json"
    
    def __init__(self):
        super().__init__()
        # 其他初始化代码
        
    def on_enable(self):
        self.logger.info("MyAwesomePlugin 已启用!")
        
    def on_disable(self):
        self.logger.info("MyAwesomePlugin 已禁用!")
```

对应的 `version.json` 文件内容：

```json
{
    "version": "1.0.1",
    "download_url": "https://github.com/yourusername/my_awesome_plugin/releases/download/v1.0.1/my_awesome_plugin-1.0.1-py3-none-any.whl",
    "update_content": "修复了玩家掉落物品时的bug，优化了性能",
    "author": "您的名字",
    "update_time": "2023-10-01 12:00:00"
}
```

#### 6. 自动更新流程

当用户执行 `/checkupdate <插件名称> update` 命令时，EasyCheckUpdate 会：
1. 从 `update_url` 获取最新的版本信息
2. 比较当前版本与最新版本
3. 如果发现新版本，自动下载并安装
4. 更新前会自动备份旧版本插件文件
5. 尝试重新加载服务器以应用更新

---

## 📝 常见问题

### Q: 插件检查更新的频率可以调整吗？
A: 可以，通过修改配置文件中的 `check_interval` 参数来调整检查间隔（单位为秒）。

### Q: 如何禁用服务器启动时的自动检查？
A: 将配置文件中的 `check_update_on_load` 设置为 `false` 即可。

### Q: 更新插件时会发生什么？
A: 更新插件时，EasyCheckUpdate 会自动备份旧版本，下载新版本，并尝试重新加载服务器。如果重新加载失败，会提示您需要手动重启服务器。

### Q: 如何手动触发更新检查？
A: 可以使用命令 `/checkupdate` 检查所有插件，或 `/checkupdate <插件名称>` 检查特定插件。

### Q: 更新失败后如何恢复？
A: EasyCheckUpdate 在更新前会自动备份旧版本插件文件（.bak 后缀）。如果更新失败，可以手动将备份文件恢复。

---

## 📄 许可证

AGPL-3.0 License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个插件！

---

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- MineBBS 论坛
- QQ群：1083195477（Easy系列插件交流群）


### 📊 日志文件说明

| 日志文件 | 位置                                                | 用途                       |
| -------- | --------------------------------------------------- | -------------------------- |
| 主日志   | `logs/EasyLuckyPillar/easycheckupdate_YYYYMMDD.log` | 记录游戏运行日志和错误信息 |

---

## 📄 许可证

本项目采用 **AGPL-3.0** 许可证开源。

```
版权所有 (c) 2023 梦涵LOVE

本程序是自由软件：您可以自由地重新发布和修改它，
但必须遵循AGPL-3.0许可证的条款。
```

完整许可证文本请参阅 [LICENSE](LICENSE) 文件。

---

## 👥 贡献指南

欢迎提交 Issue 和 Pull Request！

1. **Fork 项目仓库**
2. **创建功能分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **提交更改**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **推送分支**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **创建 Pull Request**

---

## 🌟 支持与反馈

- **GitHub Issues**: [提交问题](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/issues)
- **MineBBS**: [讨论帖](https://www.minebbs.com/resources/easycheckupdate-elp-endstone.15496/)
- **作者**: 梦涵LOVE

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**

[![Star History Chart](https://api.star-history.com/svg?repos=MengHanLOVE1027/endstone-easycheckupdate&type=Date)](https://star-history.com/#MengHanLOVE1027/endstone-easycheckupdate&Date)

</div>
