<div align="center">

![EndStone-EasyCheckUpdate](https://socialify.git.ci/MengHanLOVE1027/endstone-easycheckupdate/image?custom_language=Python&description=1&font=Inter&forks=1&issues=1&language=1&logo=https://zh.minecraft.wiki/images/BE_icon_recipe_all.png&format=original&name=1&owner=1&pattern=Plus&pulls=1&stargazers=1&theme=Auto)

<h3>EndStone-EasyCheckUpdate</h3>

<p>
  <b>A plugin update checker based on EndStone.</b>

Powered by EndStone.<br>

</p>

[![README](https://img.shields.io/badge/README-中文|Chinese-blue)](README.md) [![README_EN](https://img.shields.io/badge/README-英文|English-blue)](README_EN.md)

</div>
<div align="center">

[![Github Version](https://img.shields.io/github/v/release/MengHanLOVE1027/endstone-easycheckupdate)](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases) [![GitHub License](https://img.shields.io/badge/License-AGPL3.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0) [![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/) [![Platform](https://img.shields.io/badge/Platform-EndStone-9cf.svg)](https://endstone.io) [![Downloads](https://img.shields.io/github/downloads/MengHanLOVE1027/endstone-easycheckupdate/total.svg)](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases)

</div>

---

## 📖 Introduction

EndStone-EasyCheckUpdate is a plugin update checker designed specifically for EndStone servers. It can automatically check for available updates for plugins installed on the server and supports one-click update functionality. The plugin supports obtaining update information through custom JSON files, providing a convenient plugin management experience for server administrators.

---

## ✨ Core Features

| Feature | Description |
| ---------------- | ---------------------------- |
| 🔍**Auto Check Updates** | Periodically check update status of all plugins |
| 📝**Custom Update Source** | Support specifying update information via JSON files |
| 🔄**One-Click Update** | Support automatic download and update of plugins |
| 🕒**Scheduled Check** | Configurable check intervals |
| 💾**Auto Backup** | Automatically backup old plugin versions before updating |
| 📊**Version Comparison** | Intelligently compare version numbers, supporting multiple formats |

---

## 🗂️ Directory Structure

```
Server Root/
├── logs/
│   └── EasyCheckUpdate/                 # Log directory
│       └── easycheckupdate_YYYYMMDD.log  # Main log file
├── plugins/
│   ├── endstone_easycheckupdate-x.x.x-py3-none-any.whl  # Main plugin file
│   └── EasyCheckUpdate/                 # Plugin resource directory
│       └── config/
│           └── easycheckupdate.json     # Configuration file
```

---

## 🚀 Quick Start

### Installation Steps

1. **Download Plugin**
   - Download the latest version from the [Release page](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/releases)

2. **Install Plugin**

   ```bash
   # Copy the main plugin file to the server plugins directory
   cp endstone_easycheckupdate-x.x.x-py3-none-any.whl plugins/
   ```

3. **Configure Plugin**
   - Edit the configuration file at `plugins/EasyCheckUpdate/config/easycheckupdate.json`
   - Customize check intervals and delay times as needed

4. **Start Server**
   - Restart the server or use the `/reload` command
   - The plugin will automatically generate the default configuration file

---

## ⚙️ Configuration Details

Configuration file location: `plugins/EasyCheckUpdate/config/easycheckupdate.json`

### 📋 Main Configuration Items

```json
{
  "check_update_on_load": true,
  "check_interval": 1800,
  "check_delay": 10,
  "last_check_time": 0
}
```

### Configuration Parameter Description

| Parameter | Type | Default | Description |
|------|------|--------|------|
| check_update_on_load | Boolean | true | Whether to automatically check for updates when server starts |
| check_interval | Integer | 1800 | Interval for automatic update checks (seconds), default is 30 minutes |
| check_delay | Integer | 10 | Delay time before checking for updates after server starts (seconds), default is 10 seconds |
| last_check_time | Integer | 0 | Timestamp of last update check, automatically maintained by plugin |

---

## 🎮 Command Manual

### Admin Commands

| Command | Description |
| --------------------------------- | ------------------ |
| `/checkupdate` | Check updates for all plugins |
| `/checkupdate <plugin_name>` | Check updates for a specific plugin |
| `/checkupdate <plugin_name> update` | Check and update a specific plugin |
| `/cu` | Short form of `/checkupdate` |

### Permission Description

| Permission Node | Description |
| -------- | ---- |
| easycheckupdate.command.use | Allow using the check update command (default: OP only) |

---

## 🔧 Developer Guide

### How to Add Update Check Support to Your Plugin

To make your plugin support EasyCheckUpdate's automatic update check, you need to add an `update_url` attribute to your plugin class, which should point to a URL containing update information in a JSON file.

#### 1. Add update_url Attribute

Add the `update_url` attribute to your plugin class:

```python
class YourPlugin(Plugin):
    name = "your_plugin_name"
    version = "1.0.0"
    update_url = "https://example.com/your_plugin_version.json"  # Add this line

    def __init__(self):
        super().__init__()
        # Other initialization code
```

#### 2. Create Update Information JSON File

Create a JSON file containing plugin update information and upload it to an accessible server. Two formats are supported:

**Format 1: Single Version Format (suitable for maintaining only the latest version)**

```json
{
    "version": "1.0.1",
    "download_url": "https://example.com/downloads/your_plugin-1.0.1.whl",
    "update_content": "Fixed some bugs, added new features",
    "author": "Your Name",
    "update_time": "2023-10-01 12:00:00"
}
```

**Format 2: Multi-Version Format (suitable for maintaining multiple historical versions)**

Array Format (recommended):
```json
{
    "latest_version": "1.0.1",
    "versions": [
        {
            "version": "1.0.1",
            "download_url": "https://example.com/downloads/your_plugin-1.0.1.whl",
            "update_content": "Fixed some bugs, added new features",
            "author": "Your Name",
            "update_time": "2023-10-01 12:00:00"
        },
        {
            "version": "1.0.0",
            "download_url": "https://example.com/downloads/your_plugin-1.0.0.whl",
            "update_content": "Initial release",
            "author": "Your Name",
            "update_time": "2023-09-01 10:00:00"
        }
    ]
}
```

Object Format:
```json
{
    "latest_version": "1.0.1",
    "versions": {
        "1.0.1": {
            "download_url": "https://example.com/downloads/your_plugin-1.0.1.whl",
            "update_content": "Fixed some bugs, added new features",
            "author": "Your Name",
            "update_time": "2023-10-01 12:00:00"
        },
        "1.0.0": {
            "download_url": "https://example.com/downloads/your_plugin-1.0.0.whl",
            "update_content": "Initial release",
            "author": "Your Name",
            "update_time": "2023-09-01 10:00:00"
        }
    }
}
```

#### 3. JSON File Field Description

**Single Version Format Fields:**

| Field | Type | Required | Description |
|------|------|------|------|
| version | String | Yes | Latest version number |
| download_url | String | Yes | Download URL for the latest version |
| update_content | String | No | Update content description |
| author | String | No | Plugin author |
| update_time | String | No | Update release time |

**Multi-Version Format Fields:**

| Field | Type | Required | Description |
|------|------|------|------|
| latest_version | String | Yes | Latest version number |
| versions | Array or Object | Yes | Version information list, can be array format or object format |
| versions[].version | String | Yes (array format) | Version number |
| versions[].download_url | String | Yes | Download URL for that version |
| versions[].update_content | String | No | Update content description |
| versions[].author | String | No | Plugin author |
| versions[].update_time | String | No | Update release time |

#### 4. Version Number Format Description

EasyCheckUpdate supports multiple version number formats, including but not limited to:
- Standard version numbers: `1.0.0`, `2.1.3`
- Version numbers with prefix: `v1.0.0`, `V2.1.3`
- Version numbers with suffix: `1.0.0-beta`, `2.1.3-rc1`

Version comparison automatically ignores `v` or `V` prefixes and compares numeric parts segment by segment. If a segment cannot be converted to a number, it is compared as a string.

#### 5. Complete Example

Here is a complete plugin example:

```python
from endstone.plugin import Plugin

class MyAwesomePlugin(Plugin):
    name = "my_awesome_plugin"
    version = "1.0.0"
    update_url = "https://raw.githubusercontent.com/yourusername/my_awesome_plugin/main/version.json"

    def __init__(self):
        super().__init__()
        # Other initialization code

    def on_enable(self):
        self.logger.info("MyAwesomePlugin enabled!")

    def on_disable(self):
        self.logger.info("MyAwesomePlugin disabled!")
```

Corresponding `version.json` file content:

```json
{
    "version": "1.0.1",
    "download_url": "https://github.com/yourusername/my_awesome_plugin/releases/download/v1.0.1/my_awesome_plugin-1.0.1-py3-none-any.whl",
    "update_content": "Fixed bugs when players drop items, optimized performance",
    "author": "Your Name",
    "update_time": "2023-10-01 12:00:00"
}
```

#### 6. Automatic Update Process

When a user executes the `/checkupdate <plugin_name> update` command, EasyCheckUpdate will:
1. Fetch the latest version information from `update_url`
2. Compare the current version with the latest version
3. If a new version is found, automatically download and install it
4. Automatically backup the old plugin file before updating
5. Attempt to reload the server to apply the update

---

## 📝 FAQ

### Q: Can the frequency of plugin update checks be adjusted?
A: Yes, you can adjust the check interval by modifying the `check_interval` parameter in the configuration file (unit: seconds).

### Q: How to disable automatic check when the server starts?
A: Set `check_update_on_load` to `false` in the configuration file.

### Q: What happens when updating a plugin?
A: When updating a plugin, EasyCheckUpdate will automatically backup the old version, download the new version, and attempt to reload the server. If the reload fails, you will be prompted to manually restart the server.

### Q: How to manually trigger an update check?
A: You can use the command `/checkupdate` to check all plugins, or `/checkupdate <plugin_name>` to check a specific plugin.

### Q: How to recover after a failed update?
A: EasyCheckUpdate automatically backs up the old plugin file (.bak suffix) before updating. If the update fails, you can manually restore the backup file.

---

## 📄 License

AGPL-3.0 License

---

## 🤝 Contributing

Issues and Pull Requests are welcome to help improve this plugin!

---

## 📞 Contact

If you have questions or suggestions, please contact us through:
- GitHub Issues
- MineBBS Forum
- QQ Group: 1083195477 (Easy Series Plugin Exchange Group)


### 📊 Log File Description

| Log File | Location | Purpose |
| -------- | --------------------------------------------------- | -------------------------- |
| Main Log | `logs/EasyLuckyPillar/easycheckupdate_YYYYMMDD.log` | Records game runtime logs and error information |

---

## 📄 License

This project is open sourced under the **AGPL-3.0** license.

```
Copyright (c) 2023 MengHanLOVE

This program is free software: you can freely redistribute and modify it,
but must follow the terms of the AGPL-3.0 license.
```

For the full license text, please refer to the [LICENSE](LICENSE) file.

---

## 👥 Contributing Guide

Issues and Pull Requests are welcome!

1. **Fork the project repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Create Pull Request**

---

## 🌟 Support & Feedback

- **GitHub Issues**: [Submit Issue](https://github.com/MengHanLOVE1027/endstone-easycheckupdate/issues)
- **MineBBS**: [Discussion Thread](https://www.minebbs.com/resources/easycheckupdate-ecu-endstone.15500/)
- **Author**: MengHanLOVE

---

<div align="center">

**⭐ If this project helps you, please give us a Star!**

[![Star History Chart](https://api.star-history.com/svg?repos=MengHanLOVE1027/endstone-easycheckupdate&type=Date)](https://star-history.com/#MengHanLOVE1027/endstone-easycheckupdate&Date)

</div>
