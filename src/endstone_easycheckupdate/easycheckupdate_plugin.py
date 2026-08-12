# python 库
import os, json, shutil, zipfile, time, logging, random, re
from pathlib import Path
from threading import Lock
from datetime import datetime
import urllib.request
import sys

# endstone 库
from endstone.plugin import Plugin
from endstone.command import CommandSenderWrapper

# Easy系列插件的 BStats 遥测模块
from .bstats import BStats, SimplePie

# ============================================================
# TAG: 全局常量
# ============================================================
plugin_name = "EasyCheckUpdate"
plugin_name_smallest = "easycheckupdate"
plugin_description = "一个基于 EndStone 的插件更新检查工具 | A plugin update checker based on EndStone."
plugin_version = "0.2.3"
plugin_author = ["梦涵LOVE"]
plugin_website = "https://www.minebbs.com/resources/easycheckupdate-ecu-endstone.15500/"
plugin_github_link = "https://github.com/MengHanLOVE1027/endstone-easycheckupdate"
plugin_minebbs_link = "https://www.minebbs.com/resources/easycheckupdate-ecu-endstone.15500/"
plugin_license = "AGPL-3.0"
plugin_update_url = "https://raw.githubusercontent.com/MengHanLOVE1027/endstone-easycheckupdate/refs/heads/main/update_versions.json"

success_plugin_version = "v" + plugin_version
plugin_full_name = plugin_name + " " + success_plugin_version

plugin_path = Path(f"./plugins/{plugin_name}")
plugin_config_path = plugin_path / "config" / f"{plugin_name}.json"


# ============================================================
# TAG: 随机颜色系统
# ============================================================
GLOBAL_C1 = None
GLOBAL_C2 = None

def randomVividColor():
    """生成一个鲜艳的随机颜色"""
    rand = random.random() * 260
    if rand < 90:
        h = rand
    elif rand < 200:
        h = rand + 60
    else:
        h = rand + 100
    s = 0.90 + random.random() * 0.10
    l = 0.65 + random.random() * 0.15
    a = s * min(l, 1 - l)
    def f(n):
        k = (n + h / 30) % 12
        return round((l - a * max(-1, min(k - 3, 9 - k, 1))) * 255)
    return [f(0), f(8), f(4)]

def generateColorPair():
    """生成一对颜色"""
    c1 = randomVividColor()
    c2 = c1
    attempts = 0
    while True:
        c2 = randomVividColor()
        diff = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1]) + abs(c1[2] - c2[2])
        if diff > 150 or attempts > 20:
            break
        attempts += 1
    return [c1, c2]

GLOBAL_C1, GLOBAL_C2 = generateColorPair()

def globalLerpColor(t):
    """在全局颜色对之间进行线性插值"""
    return [
        round(GLOBAL_C1[0] + (GLOBAL_C2[0] - GLOBAL_C1[0]) * t),
        round(GLOBAL_C1[1] + (GLOBAL_C2[1] - GLOBAL_C1[1]) * t),
        round(GLOBAL_C1[2] + (GLOBAL_C2[2] - GLOBAL_C1[2]) * t)
    ]

def randomGradientColor(text):
    """生成随机渐变色文本"""
    lenth = len(text)
    out = ''
    for i in range(lenth):
        t = 0 if lenth <= 1 else i / (lenth - 1)
        r, g, b = globalLerpColor(t)
        out += f"\x1b[38;2;{r};{g};{b}m{text[i]}"
    return out + "\x1b[0m"

class RandomColor:
    """随机颜色类，用于生成随机渐变色文本"""
    def __init__(self, text):
        self.text = text
    def __str__(self):
        return randomGradientColor(self.text)


# ============================================================
# TAG: I18N 国际化模块
# ============================================================
I18N_DATA = {
    "zh_CN": {
        # ── Logo / 启动 ──
        "logo.author": "作者：梦涵LOVE          版本：v{0}",
        "logo.thanks": "感谢您使用Easy系列插件！",
        "logo.license": "本插件使用 {0} 许可证协议发布",
        "logo.github": "GitHub 仓库：{0}",
        "logo.minebbs": "插件MineBBS资源帖：{0}",
        "logo.community": "Easy系列插件交流群：1083195477",
        "logo.author_ver": "作者：梦涵LOVE | 版本：v{0}",
        "logo.bstats_status": "BStats状态：{0}",
        "general.enabled": "已启用",
        "general.disabled": "已禁用",

        # ── 插件生命周期 ──
        "plugin.loading": "{0} 正在加载...",
        "plugin.loaded": "{0} 已加载!",
        "plugin.enabling": "{0} 正在启用...",
        "plugin.enabled": "{0} 已启用!",
        "plugin.disabling": "{0} 正在禁用...",
        "plugin.disabled": "{0} 已禁用!",

        # ── 配置 ──
        "config.created": "已创建默认配置文件",
        "config.backed_up": "配置已备份到 {0}",
        "config.backup_failed": "配置备份失败: {0}",
        "config.version_update": "检测到配置版本更新: v{0} → v{1}，开始迁移配置...",
        "config.migrated": "配置已迁移到 v{0}",
        "config.migrate_failed": "配置迁移到 v{0} 失败: {1}",
        "config.missing_added": "已补充缺失配置项: {0}",
        "config.missing_auto_added": "已自动补充缺失配置项: {0}",
        "config.migrate_done": "配置迁移完成!",
        "config.load_failed": "加载配置文件失败: {0}",
        "config.reloaded": "配置文件已重新加载",
        "config.not_exist": "配置文件不存在，使用默认配置",
        "config.reload_success": "重载成功",
        "config.reload_failed": "重载失败: {0}",
        "config.unknown_language": "未知语言 \"{0}\"，将回退到 zh_CN",
        "config.file_path": "配置文件: {0}",

        # ── 更新检查 ──
        "update.auto_check_delay": "将在 {0} 秒后自动检查所有插件的更新...",
        "update.already_checking": "已有检查任务正在运行，跳过本次检查",
        "update.check_too_soon": "距离上次检查不足 {0} 秒（还需 {1} 秒），跳过本次检查",
        "update.checking_all": "正在检查所有插件的更新...",
        "update.checking": "正在检查插件 {0} 的更新...",
        "update.fetching": "正在从 {0} 获取插件 {1} 的更新信息...",
        "update.fetch_error": "从 {0} 获取插件 {1} 的更新信息时出错，状态码: {2}",
        "update.format_error": "插件 {0} 的更新信息格式不正确",
        "update.version_not_found": "插件 {0} 未找到指定版本 v{1}",
        "update.up_to_date": "插件 {0} 已是最新版本: {1}",
        "update.no_download_url": "插件 {0} 的更新信息缺少下载链接",
        "update.no_required_info": "插件 {0} 的更新信息文件缺少必要信息",
        "update.new_version": "插件 {0} 有新版本: v{1} (当前版本: {2})",
        "update.target_version": "插件 {0} 将安装指定版本 v{1} (当前版本: {2})",
        "update.author": "作者: {0}",
        "update.time": "更新时间: {0}",
        "update.type": "类型: {0}",
        "update.content": "更新内容: {0}",
        "update.download_url": "下载地址: {0}",
        "update.newer_than_latest": "插件 {0} 的当前版本 {1} 比最新版本 v{2} 更新",
        "update.parse_error": "解析插件 {0} 的更新信息时出错: {1}",
        "update.check_error": "检查插件 {0} 的更新时出错: {1}",
        "update.no_update_url": "未找到插件 {0} 的 update_url 字段，无法检查更新",
        "update.check_done": "检查完成，共检查了 {0} 个支持更新检查的插件",
        "update.no_plugins": "没有找到支持更新检查的插件",
        "update.version_list": "插件 {0} 的可用版本列表 (第{1}/{2}页, {3}-{4}/{5}):",
        "update.version_list_next": "使用 /ecu info {0} p{1} 查看下一页",
        "update.version_detail": "插件 {0} 版本 v{1} 的详细信息:",
        "update.fetch_failed": "获取插件 {0} 的更新信息失败，状态码: {1}",
        "update.parse_version_error": "解析版本信息时出错: {0}",
        "general.pre_release": "测试版",
        "general.stable": "正式版",
        "general.current_version": " [当前版本]",
        "general.recommended": " ★推荐",
        "general.no_content": "无更新内容",
        "general.unknown_author": "未知作者",
        "general.unknown_time": "未知时间",
        "general.none": "无",

        # ── 下载 / 解压 ──
        "download.clean_dir_error": "清理目录 {0} 时出错: {1}",
        "download.detect_root": "检测到压缩包根目录: {0}",
        "download.scan_error": "扫描解压目录时出错: {0}",
        "download.copy": "  复制: {0}",
        "download.copy_sub": "  复制: {0}/{1}",
        "download.installed": "已安装 {0} 个文件到 {1}",
        "download.copy_error": "复制文件时出错: {0}",
        "download.downloading": "正在下载: {0}",
        "download.write_failed": "写入文件失败: {0}",
        "download.failed": "下载失败: HTTP {0}",
        "download.from_url": "正在从 {0} 下载插件 {1} 版本 {2}...",
        "download.plugin_failed": "下载插件 {0} 失败: {1}",
        "download.extracting": "ZIP 已下载，正在解压...",
        "download.updated_reloading": "插件 {0} 已更新到 v{1}，正在重载插件...",
        "download.reloaded": "插件 {0} 已重载",
        "download.reload_failed": "重载插件失败: {0}",
        "download.reload_manual": "请手动重启服务器以加载新插件",
        "download.update_error": "更新插件 {0} 时出错: {1}",
        "download.url_error": "从URL下载插件 {0} 时出错: {1}",
        "download.backed_up": "已备份旧文件到 {0}",
        "download.backup_failed": "备份文件失败: {0}",
        "download.backup_dir_done": "已备份插件目录到 {0}",
        "download.rollback_done": "安装失败，已恢复原插件文件",
        "download.rollback_failed": "安装失败且无法恢复原插件文件: {0}",
        "download.install_empty": "压缩包中没有可安装的文件",
        "download.invalid_url": "下载地址不安全或格式无效: {0}",
        "download.invalid_plugin_name": "插件名称包含非法路径字符: {0}",
        "download.file_updated": "已更新插件文件: {0}",
        "download.no_file_path": "无法找到插件 {0} 的文件路径",

        # ── 命令 / 帮助 ──
        "command.desc": "检查插件更新",
        "command.no_permission": "你没有权限使用此命令",
        "command.help": "命令帮助:\n/ecu - 显示此帮助信息\n/ecu all - 检查所有插件的更新\n/ecu reload - 重载插件\n/ecu check <插件名称> - 检查指定插件的更新\n/ecu update <插件名称> [版本号] - 更新指定插件\n/ecu info <插件名称> [版本号] - 查看版本列表或指定版本详情",
        "command.update_usage": "用法: /ecu update <插件名称> [版本号]",
        "command.info_usage": "用法: /ecu info <插件名称> [版本号]",
        "command.checking_update": "正在检查并更新插件 {0}，请查看控制台获取详细信息",
        "command.plugin_not_found": "未找到插件: {0}",
        "command.querying_detail": "正在查询插件 {0} 版本 v{1} 的详细信息，请查看控制台",
        "command.querying_list": "正在查询插件 {0} 的版本列表，请查看控制台",
        "command.checking_all": "正在检查所有插件的更新，请查看控制台获取详细信息",
        "command.checking_plugin": "正在检查插件 {0} 的更新，请查看控制台获取详细信息",
        "command.check_usage": "用法: /ecu check <插件名称>",
        "command.unknown_subcommand": "未知命令: /ecu {0}",

        # ── BStats / 其他 ──
        "bstats.init_failed": "BStats初始化失败: {0}",
        "bstats.started": "{0}遥测模块已启动。",
        "bstats.status": "遥测状态: {0}",
        "bstats.disabled_skip": "遥测模块已禁用，跳过上报。",
        "bstats.submitting": "正在提交遥测数据到 bStats 服务器...",
        "bstats.submit_success": "遥测数据上报成功！",
        "bstats.submit_failed": "上报失败，状态码: {0}",
        "bstats.network_error": "网络请求异常: {0}",
        "bstats.submit_error": "提交数据时发生错误: {0}",
        "bstats.module_started": "{0} 遥测模块已启动。",
        "bstats.first_submit_info": "首次数据将在 30 秒后发送，之后每 30 分钟发送一次。",
        "bstats.plugin_info": "插件ID: {0}, 插件版本: {1}",
        "bstats.debug_mode": "调试模式: {0}",
        "bstats.module_stopped": "{0} 遥测模块已关闭。",
    },
    "en_US": {
        # ── Logo / Startup ──
        "logo.author": "Author: MengHanLOVE          Version: v{0}",
        "logo.thanks": "Thank you for using the Easy series plugins!",
        "logo.license": "This plugin is released under the {0} license",
        "logo.github": "GitHub Repository: {0}",
        "logo.minebbs": "MineBBS Resource Post: {0}",
        "logo.community": "Easy Series Plugin Community: 1083195477",
        "logo.author_ver": "Author: MengHanLOVE | Version: v{0}",
        "logo.bstats_status": "BStats Status: {0}",
        "general.enabled": "Enabled",
        "general.disabled": "Disabled",

        # ── Plugin Lifecycle ──
        "plugin.loading": "{0} is loading...",
        "plugin.loaded": "{0} loaded!",
        "plugin.enabling": "{0} is enabling...",
        "plugin.enabled": "{0} enabled!",
        "plugin.disabling": "{0} is disabling...",
        "plugin.disabled": "{0} disabled!",

        # ── Config ──
        "config.created": "Default configuration file created",
        "config.backed_up": "Configuration backed up to {0}",
        "config.backup_failed": "Configuration backup failed: {0}",
        "config.version_update": "Config version update detected: v{0} → v{1}, starting migration...",
        "config.migrated": "Configuration migrated to v{0}",
        "config.migrate_failed": "Configuration migration to v{0} failed: {1}",
        "config.missing_added": "Missing config items added: {0}",
        "config.missing_auto_added": "Automatically added missing config items: {0}",
        "config.migrate_done": "Configuration migration complete!",
        "config.load_failed": "Failed to load configuration file: {0}",
        "config.reloaded": "Configuration file reloaded",
        "config.not_exist": "Configuration file does not exist, using defaults",
        "config.reload_success": "Reload successful",
        "config.reload_failed": "Reload failed: {0}",
        "config.unknown_language": "Unknown language \"{0}\", falling back to zh_CN",
        "config.file_path": "Config file: {0}",

        # ── Update Check ──
        "update.auto_check_delay": "Will auto-check all plugins for updates in {0} seconds...",
        "update.already_checking": "Another check is already running, skipping this check",
        "update.check_too_soon": "Less than {0} seconds since last check ({1} seconds remaining), skipping this check",
        "update.checking_all": "Checking all plugins for updates...",
        "update.checking": "Checking plugin {0} for updates...",
        "update.fetching": "Fetching update info for {1} from {0}...",
        "update.fetch_error": "Error fetching update info for {1} from {0}, status code: {2}",
        "update.format_error": "Update info format for plugin {0} is incorrect",
        "update.version_not_found": "Plugin {0}: specified version v{1} not found",
        "update.up_to_date": "Plugin {0} is up to date: {1}",
        "update.no_download_url": "Update info for {0} is missing download URL",
        "update.no_required_info": "Update info file for {0} is missing required information",
        "update.new_version": "Plugin {0} has a new version: v{1} (current: {2})",
        "update.target_version": "Plugin {0} will install specified version v{1} (current: {2})",
        "update.author": "Author: {0}",
        "update.time": "Update Time: {0}",
        "update.type": "Type: {0}",
        "update.content": "Update Content: {0}",
        "update.download_url": "Download URL: {0}",
        "update.newer_than_latest": "Plugin {0} current version {1} is newer than latest v{2}",
        "update.parse_error": "Error parsing update info for {0}: {1}",
        "update.check_error": "Error checking updates for {0}: {1}",
        "update.no_update_url": "update_url field not found for plugin {0}, unable to check for updates",
        "update.check_done": "Check complete, {0} update-capable plugin(s) checked",
        "update.no_plugins": "No plugins supporting update checks found",
        "update.version_list": "Available versions for plugin {0} (Page {1}/{2}, {3}-{4}/{5}):",
        "update.version_list_next": "Use /ecu info {0} p{1} for next page",
        "update.version_detail": "Details for plugin {0} version v{1}:",
        "update.fetch_failed": "Failed to fetch update info for {0}, status code: {1}",
        "update.parse_version_error": "Error parsing version info: {0}",
        "general.pre_release": "Pre-release",
        "general.stable": "Stable",
        "general.current_version": " [Current]",
        "general.recommended": " ★Recommended",
        "general.no_content": "No update content",
        "general.unknown_author": "Unknown author",
        "general.unknown_time": "Unknown time",
        "general.none": "None",

        # ── Download / Extract ──
        "download.clean_dir_error": "Error cleaning directory {0}: {1}",
        "download.detect_root": "Detected archive root directory: {0}",
        "download.scan_error": "Error scanning extracted directory: {0}",
        "download.copy": "  Copy: {0}",
        "download.copy_sub": "  Copy: {0}/{1}",
        "download.installed": "Installed {0} file(s) to {1}",
        "download.copy_error": "Error copying files: {0}",
        "download.downloading": "Downloading: {0}",
        "download.write_failed": "Failed to write file: {0}",
        "download.failed": "Download failed: HTTP {0}",
        "download.from_url": "Downloading plugin {1} version {2} from {0}...",
        "download.plugin_failed": "Failed to download plugin {0}: {1}",
        "download.extracting": "ZIP downloaded, extracting...",
        "download.updated_reloading": "Plugin {0} updated to v{1}, reloading...",
        "download.reloaded": "Plugin {0} reloaded",
        "download.reload_failed": "Failed to reload plugin: {0}",
        "download.reload_manual": "Please manually restart the server to load the new plugin",
        "download.update_error": "Error updating plugin {0}: {1}",
        "download.url_error": "Error downloading plugin {0} from URL: {1}",
        "download.backed_up": "Old file backed up to {0}",
        "download.backup_failed": "Failed to backup file: {0}",
        "download.backup_dir_done": "Plugin directory backed up to {0}",
        "download.rollback_done": "Installation failed; original plugin files were restored",
        "download.rollback_failed": "Installation failed and original plugin files could not be restored: {0}",
        "download.install_empty": "The archive contains no installable files",
        "download.invalid_url": "Download URL is unsafe or invalid: {0}",
        "download.invalid_plugin_name": "Plugin name contains invalid path characters: {0}",
        "download.file_updated": "Plugin file updated: {0}",
        "download.no_file_path": "Cannot find file path for plugin {0}",

        # ── Command / Help ──
        "command.desc": "Check plugin updates",
        "command.no_permission": "You do not have permission to use this command",
        "command.help": "Command Help:\n/ecu - Show this help\n/ecu all - Check all plugins for updates\n/ecu reload - Reload plugin\n/ecu check <plugin> - Check specified plugin for updates\n/ecu update <plugin> [version] - Update specified plugin\n/ecu info <plugin> [version] - View version list or details",
        "command.update_usage": "Usage: /ecu update <plugin> [version]",
        "command.info_usage": "Usage: /ecu info <plugin> [version]",
        "command.checking_update": "Checking and updating plugin {0}, check console for details",
        "command.plugin_not_found": "Plugin not found: {0}",
        "command.querying_detail": "Querying details for {0} v{1}, check console",
        "command.querying_list": "Querying version list for {0}, check console",
        "command.checking_all": "Checking all plugins for updates, check console for details",
        "command.checking_plugin": "Checking {0} for updates, check console for details",
        "command.check_usage": "Usage: /ecu check <plugin>",
        "command.unknown_subcommand": "Unknown command: /ecu {0}",

        # ── BStats / Misc ──
        "bstats.init_failed": "BStats initialization failed: {0}",
        "bstats.started": "{0} telemetry module started.",
        "bstats.status": "Telemetry Status: {0}",
        "bstats.disabled_skip": "Telemetry module disabled, skipping report.",
        "bstats.submitting": "Submitting telemetry data to bStats server...",
        "bstats.submit_success": "Telemetry data submitted successfully!",
        "bstats.submit_failed": "Submission failed, status code: {0}",
        "bstats.network_error": "Network request error: {0}",
        "bstats.submit_error": "Error while submitting data: {0}",
        "bstats.module_started": "{0} telemetry module started.",
        "bstats.first_submit_info": "First data will be sent in 30 seconds, then every 30 minutes.",
        "bstats.plugin_info": "Plugin ID: {0}, Plugin Version: {1}",
        "bstats.debug_mode": "Debug mode: {0}",
        "bstats.module_stopped": "{0} telemetry module stopped.",
    }
}

# 全局翻译状态
_i18n_lang = "zh_CN"
_i18n_data = I18N_DATA["zh_CN"]


def t(key, *args):
    """翻译函数，支持 {0} {1} ... 占位符"""
    template = _i18n_data.get(key, key)
    for i, arg in enumerate(args):
        template = template.replace("{" + str(i) + "}", str(arg))
    return template


def apply_configured_language(config_lang="zh_CN"):
    """根据当前配置切换输出语言"""
    global _i18n_lang, _i18n_data
    if config_lang in I18N_DATA:
        _i18n_lang = config_lang
        _i18n_data = I18N_DATA[config_lang]
        return
    _i18n_lang = "zh_CN"
    _i18n_data = I18N_DATA["zh_CN"]


# ============================================================
# TAG: 配置管理系统
# ============================================================
def deep_merge_config(defaults, target):
    """深度合并配置：将 defaults 中缺失的键合并到 target，不覆盖已有值"""
    result = json.loads(json.dumps(target))
    for key in defaults:
        if result.get(key) is None and defaults[key] is not None:
            result[key] = defaults[key]
        elif isinstance(defaults[key], dict) and not isinstance(defaults[key], list) and \
             isinstance(result.get(key), dict) and not isinstance(result.get(key), list):
            result[key] = deep_merge_config(defaults[key], result[key])
    return result


def get_missing_keys(defaults, target):
    """列出 defaults 中 target 缺失的属性名"""
    missing = []
    for key in defaults:
        if key not in target:
            missing.append(key)
    return missing


# ============================================================
# TAG: 日志系统设置
# ============================================================
log_dir = Path(f"./logs/{plugin_name}")
if not log_dir.exists():
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[{plugin_name}] 创建日志目录失败: {e}")

log_file = log_dir / f"{plugin_name_smallest}_{datetime.now().strftime('%Y%m%d')}.log"

logger = logging.getLogger(plugin_name)
logger.setLevel(logging.DEBUG)

try:
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"[{plugin_name}] 配置日志文件处理器失败: {e}")

print_lock = Lock()


def plugin_print(text, level="INFO"):
    """自制 print 日志输出函数"""
    level_colors = {
        "DEBUG": "\x1b[36m",
        "INFO": "\x1b[37m",
        "WARNING": "\x1b[33m",
        "ERROR": "\x1b[31m",
        "SUCCESS": "\x1b[32m"
    }
    level_color = level_colors.get(level, "\x1b[37m")
    logger_head = f"[\x1b[96m{plugin_name}\x1b[0m] [{level_color}{level}\x1b[0m] "

    with print_lock:
        print(logger_head + str(RandomColor(text)))

    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "SUCCESS": logging.INFO
    }
    log_level = log_level_map.get(level, logging.INFO)
    logger.log(log_level, str(text))


# 确保插件目录存在
if not plugin_path.exists():
    os.makedirs(plugin_path, exist_ok=True)


# ============================================================
# TAG: 版本比较工具 (SemVer)
# ============================================================
def parse_semantic_version(version):
    """解析 SemVer 版本号，返回 {"core": [...], "preRelease": [...]|None}"""
    if version is None:
        return None
    normalized = str(version).strip().lstrip('vV')
    normalized = normalized.split('+')[0]

    core_text = normalized
    pre_release_text = None
    dash_index = normalized.find('-')
    if dash_index >= 0:
        core_text = normalized[:dash_index]
        pre_release_text = normalized[dash_index + 1:]
    else:
        # 兼容 1.0.0rc1 这类未使用连字符的写法
        m = re.match(r'^(\d+(?:\.\d+)*?)([A-Za-z][0-9A-Za-z.-]*)$', normalized)
        if m:
            core_text = m.group(1)
            pre_release_text = m.group(2)

    if not re.match(r'^\d+(?:\.\d+)*$', core_text):
        return None
    if pre_release_text is not None and not re.match(r'^[0-9A-Za-z.-]+$', pre_release_text):
        return None

    return {
        "core": [int(x) for x in core_text.split('.')],
        "preRelease": pre_release_text.split('.') if pre_release_text else None
    }


def compare_versions(version1, version2):
    """
    比较两个 SemVer 版本号
    :return: -1(小于), 0(等于), 1(大于)
    """
    p1 = parse_semantic_version(version1)
    p2 = parse_semantic_version(version2)

    # 对非标准版本号进行字符串比较
    if not p1 or not p2:
        v1 = str(version1 or "").lstrip('vV').lower()
        v2 = str(version2 or "").lstrip('vV').lower()
        if v1 == v2:
            return 0
        # 尝试数字比较
        tokens1 = re.findall(r'\d+|\D+', v1)
        tokens2 = re.findall(r'\d+|\D+', v2)
        for i in range(max(len(tokens1), len(tokens2))):
            if i >= len(tokens1):
                return -1
            if i >= len(tokens2):
                return 1
            t1, t2 = tokens1[i], tokens2[i]
            if t1.isdigit() and t2.isdigit():
                n1, n2 = int(t1), int(t2)
                if n1 != n2:
                    return -1 if n1 < n2 else 1
            elif t1 != t2:
                return -1 if t1 < t2 else 1
        return 0

    # 比较核心版本号
    max_len = max(len(p1["core"]), len(p2["core"]))
    for i in range(max_len):
        a = p1["core"][i] if i < len(p1["core"]) else 0
        b = p2["core"][i] if i < len(p2["core"]) else 0
        if a != b:
            return -1 if a < b else 1

    # SemVer 规则：正式版高于任何预发布版
    if p1["preRelease"] is None and p2["preRelease"] is not None:
        return 1
    if p1["preRelease"] is not None and p2["preRelease"] is None:
        return -1
    if p1["preRelease"] is None and p2["preRelease"] is None:
        return 0

    # 比较预发布标识符
    max_pre = max(len(p1["preRelease"]), len(p2["preRelease"]))
    for i in range(max_pre):
        if i >= len(p1["preRelease"]):
            return -1
        if i >= len(p2["preRelease"]):
            return 1
        a, b = p1["preRelease"][i], p2["preRelease"][i]
        if a == b:
            continue
        if a.isdigit() and b.isdigit():
            return -1 if int(a) < int(b) else 1
        if a.isdigit() != b.isdigit():
            return -1 if a.isdigit() else 1
        return -1 if a < b else 1
    return 0


def is_prerelease(version):
    """检测版本号是否为预发布版本"""
    parsed = parse_semantic_version(version)
    if parsed:
        return parsed["preRelease"] is not None
    return bool(re.search(r'[a-zA-Z]', str(version or "").lstrip('vV')))


def find_version_key(versions, requested_version):
    """在版本字典中查找匹配的 key（兼容 v 前缀）"""
    if requested_version in versions:
        return requested_version
    normalized = str(requested_version).lstrip('vV')
    for key in versions:
        if key.lstrip('vV') == normalized:
            return key
    return None


def normalize_version(ver: str):
    """去掉版本号前可选的 v/V 前缀"""
    if ver and ver.lower().startswith('v'):
        return ver[1:]
    return ver


def print_version_list(plugin_name_str, versions, current_version, recommended_ver, page=1, per_page=10):
    """打印插件的版本列表（支持分页）"""
    sorted_vers = sorted(versions.keys(), key=lambda v: compare_versions(v, "0.0.0"), reverse=True)
    total = len(sorted_vers)
    total_pages = max(1, (total + per_page - 1) // per_page)

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = min(start + per_page, total)

    plugin_print(t("update.version_list", plugin_name_str, page, total_pages, start + 1, end, total))
    for i in range(start, end):
        ver = sorted_vers[i]
        tag = t("general.pre_release" if is_prerelease(ver) else "general.stable")
        marker = t("general.current_version") if compare_versions(ver, current_version) == 0 else ""
        latest = t("general.recommended") if ver == recommended_ver else ""
        plugin_print(f"  {i + 1}. v{ver} ({tag}){latest}{marker}")

    if page < total_pages:
        plugin_print(t("update.version_list_next", plugin_name_str, page + 1))


# ============================================================
# TAG: 插件入口点
# ============================================================
class EasyCheckUpdatePlugin(Plugin):
    """EasyCheckUpdate 插件入口点"""

    api_version = "0.5"
    name = plugin_name_smallest
    full_name = plugin_full_name
    description = plugin_description
    version = plugin_version
    authors = plugin_author
    website = plugin_website
    update_url = plugin_update_url

    # NOTE: 注册命令
    commands = {
        "easycheckupdate": {
            "description": t("command.desc"),
            "usages": [
                "/easycheckupdate",
                "/easycheckupdate all",
                "/easycheckupdate reload",
                "/easycheckupdate check <plugin_name: str>",
                "/easycheckupdate info <plugin_name: str> [version: str]",
                "/easycheckupdate update <plugin_name: str> [version: str]",
            ],
            "permissions": ["easycheckupdate.command.use"],
            "aliases": ["ecu"],
        },
    }

    # NOTE: 权限组
    permissions = {
        "easycheckupdate.command.use": {
            "description": "允许使用 /ecu 命令",
            "default": "op",
        },
    }

    def __init__(self):
        super().__init__()
        self.check_update_on_load = True
        self.check_interval = 1800
        self.check_delay = 10
        self.last_check_time = 0
        self.plugin_config = {}
        self.config_backup_path = plugin_path / "config" / ".config_backup.json"
        self._checking = False  # 防重入锁
        self._periodic_scheduled = False  # 防重复调度

    # ── 配置方法 ──

    def get_config_defaults(self):
        """返回完整默认配置"""
        return {
            "Version": plugin_version,
            "language": "zh_CN",
            "Bstats": {
                "EnableModule": True,
                "logSentData": False
            },
            "check_update_on_load": True,
            "check_interval": 1800,
            "check_delay": 10,
            "last_check_time": 0
        }

    def backup_config(self, saved_ver):
        """备份当前配置到 .config_backup.json"""
        try:
            backup = {
                "version": saved_ver or "unknown",
                "timestamp": datetime.now().isoformat(),
                "config": json.loads(json.dumps(self.plugin_config))
            }
            self.config_backup_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup, f, indent=4, ensure_ascii=False)
            plugin_print(t("config.backed_up", str(self.config_backup_path)), "INFO")
        except Exception as e:
            plugin_print(t("config.backup_failed", str(e)), "WARNING")

    def migrate_config(self, old_version):
        """增量迁移配置"""

        def _migrate():
            migrations = []
            # 未来配置迁移示例：
            # migrations.append({
            #     "version": "0.3.0",
            #     "handler": lambda: self.plugin_config.update({"notifyChannel": "console"})
            # })

            for migration in migrations:
                if compare_versions(old_version, migration["version"]) < 0:
                    try:
                        self.backup_config(old_version)
                        migration["handler"]()
                        plugin_print(t("config.migrated", migration["version"]), "SUCCESS")
                    except Exception as e:
                        plugin_print(t("config.migrate_failed", migration["version"], str(e)), "ERROR")

        _migrate()

    def load_config(self):
        """加载配置文件（含版本管理和迁移）"""
        try:
            config_dir = plugin_config_path.parent
            config_dir.mkdir(parents=True, exist_ok=True)

            if plugin_config_path.exists():
                if plugin_config_path.stat().st_size == 0:
                    plugin_print(t("config.not_exist"), "WARNING")
                    self.plugin_config = json.loads(json.dumps(self.get_config_defaults()))
                    self.save_config()
                    return

                with open(plugin_config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        plugin_print(t("config.not_exist"), "WARNING")
                        self.plugin_config = json.loads(json.dumps(self.get_config_defaults()))
                        self.save_config()
                        return
                    self.plugin_config = json.loads(content)
            else:
                plugin_print(t("config.not_exist"), "INFO")
                self.plugin_config = json.loads(json.dumps(self.get_config_defaults()))
                self.save_config()
                plugin_print(t("config.created"), "INFO")
                return

            saved_version = self.plugin_config.get("Version", "0.0.0")

            if compare_versions(saved_version, plugin_version) < 0:
                plugin_print(t("config.version_update", saved_version, plugin_version))
                self.backup_config(saved_version)
                self.migrate_config(saved_version)
                # 补全所有当前版本必需的配置项
                defaults = self.get_config_defaults()
                missing = get_missing_keys(defaults, self.plugin_config)
                self.plugin_config = deep_merge_config(defaults, self.plugin_config)
                self.plugin_config["Version"] = plugin_version
                self.save_config()
                if missing:
                    plugin_print(t("config.missing_added", ", ".join(missing)), "INFO")
                plugin_print(t("config.migrate_done"), "SUCCESS")
            else:
                # 版本一致，补全缺失项（防止用户手误删除）
                defaults = self.get_config_defaults()
                missing = get_missing_keys(defaults, self.plugin_config)
                if missing:
                    self.plugin_config = deep_merge_config(defaults, self.plugin_config)
                    self.save_config()
                    plugin_print(t("config.missing_auto_added", ", ".join(missing)), "INFO")
        except Exception as e:
            self.plugin_config = json.loads(json.dumps(self.get_config_defaults()))
            plugin_print(t("config.load_failed", str(e)), "ERROR")

        # 从配置读取设置
        self.check_update_on_load = self.plugin_config.get("check_update_on_load", True)
        self.check_interval = self.plugin_config.get("check_interval", 1800)
        self.check_delay = self.plugin_config.get("check_delay", 10)
        self.last_check_time = self.plugin_config.get("last_check_time", 0)

    def save_config(self):
        """保存配置文件"""
        try:
            plugin_config_path.parent.mkdir(parents=True, exist_ok=True)
            self.plugin_config["check_update_on_load"] = self.check_update_on_load
            self.plugin_config["check_interval"] = self.check_interval
            self.plugin_config["check_delay"] = self.check_delay
            self.plugin_config["last_check_time"] = self.last_check_time
            with open(plugin_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            plugin_print(t("config.load_failed", str(e)), "ERROR")

    # ── 生命周期 ──

    def on_load(self):
        """插件加载时调用"""
        plugin_print(t("plugin.loading", plugin_full_name))

        # 加载配置
        self.load_config()

        # 初始化 i18n 语言
        lang = self.plugin_config.get("language", "zh_CN")
        apply_configured_language(lang)
        if lang not in I18N_DATA:
            plugin_print(t("config.unknown_language", lang), "WARNING")

        # Logo
        print(RandomColor("███████╗ █████╗ ███████╗██╗   ██╗██╗   ██╗██████╗ ██████╗  █████╗ ████████╗███████╗"))
        print(RandomColor("██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██║   ██║██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔════╝"))
        print(RandomColor("█████╗  ███████║███████╗ ╚████╔╝ ██║   ██║██████╔╝██║  ██║███████║   ██║   █████╗  "))
        print(RandomColor("██╔══╝  ██╔══██║╚════██║  ╚██╔╝  ██║   ██║██╔═══╝ ██║  ██║██╔══██║   ██║   ██╔══╝  "))
        print(RandomColor("███████╗██║  ██║███████║   ██║   ╚██████╔╝██║     ██████╔╝██║  ██║   ██║   ███████╗"))
        print(RandomColor("╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝     ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝"))
        plugin_print(t("logo.author", plugin_version))
        plugin_print("=" * 80, "INFO")
        plugin_print(f"{plugin_name} - {plugin_description}")
        plugin_print(t("logo.thanks"))
        plugin_print(t("logo.license", plugin_license))
        plugin_print(t("logo.github", plugin_github_link))
        plugin_print(t("logo.minebbs", plugin_minebbs_link))
        plugin_print(t("logo.community"))
        plugin_print(t("logo.author_ver", plugin_version))
        bstats_enabled = self.plugin_config.get("Bstats", {}).get("EnableModule", True)
        plugin_print(t("logo.bstats_status", t("general.enabled") if bstats_enabled else t("general.disabled")))
        plugin_print("=" * 80, "INFO")

        plugin_print(t("plugin.loaded", plugin_full_name))

    def on_enable(self):
        """插件启用时调用"""
        plugin_print(t("plugin.enabling", plugin_full_name))

        # 启用 bStats
        try:
            metrics = BStats(self, 29349, translate=t)
            metrics.add_custom_chart(SimplePie("check_interval", lambda: str(self.check_interval)))
            metrics.start()
        except Exception as e:
            plugin_print(t("bstats.init_failed", str(e)), "ERROR")

        plugin_print(t("plugin.enabled", plugin_full_name))

        # 定时检查更新
        self.schedule_update_checks()

    def on_disable(self):
        """插件禁用时调用"""
        plugin_print(t("plugin.disabling", plugin_full_name))
        plugin_print(t("plugin.disabled", plugin_full_name))

    # ── 定时调度 ──

    def schedule_update_checks(self):
        """安排定时更新检查"""
        if self.check_update_on_load:
            plugin_print(t("update.auto_check_delay", str(self.check_delay)))

            def _delayed_check():
                self.check_all_plugins_update()
                # 安排下一次周期性检查
                self._schedule_next_periodic_check()

            self.server.scheduler.run_task(self, _delayed_check, delay=self.check_delay * 20)
        else:
            # 即使首次不检查，也安排后续周期
            self._schedule_next_periodic_check()

    def _schedule_next_periodic_check(self):
        """安排下一次周期性检查"""
        if self._periodic_scheduled:
            return
        self._periodic_scheduled = True

        def _periodic_check():
            self._periodic_scheduled = False
            self.check_all_plugins_update()
            self._schedule_next_periodic_check()

        self.server.scheduler.run_task(self, _periodic_check, delay=self.check_interval * 20)

    # ── 更新检查 ──

    def get_plugin_update_info(self, plugin_name_str):
        """获取插件的更新信息"""
        for p in self.server.plugin_manager.plugins:
            if p.name == plugin_name_str:
                if hasattr(p, 'update_url') and p.update_url:
                    return p
        return None

    def check_all_plugins_update(self, force=False):
        """检查所有插件的更新。force=True 时忽略间隔限制"""
        if self._checking:
            plugin_print(t("update.already_checking"))
            return
        self._checking = True

        try:
            plugin_print(t("update.checking_all"))

            current_time = time.time()
            if not force and current_time - self.last_check_time < self.check_interval:
                remaining = int(self.check_interval - (current_time - self.last_check_time))
                plugin_print(t("update.check_too_soon", str(self.check_interval), str(remaining)))
                return

            self.last_check_time = current_time
            self.save_config()

            checked_count = 0
            for plugin in self.server.plugin_manager.plugins:
                pname = plugin.name
                try:
                    pversion = plugin.version
                except AttributeError:
                    pversion = "0.0.0"
                if pversion is None:
                    pversion = "0.0.0"
                if self.check_plugin_update(pname, pversion):
                    checked_count += 1

            if checked_count > 0:
                plugin_print(t("update.check_done", str(checked_count)))
            else:
                plugin_print(t("update.no_plugins"))
        finally:
            self._checking = False

    def check_plugin_update(self, plugin_name_str, current_version, auto_update=False, target_version=None):
        """检查指定插件的更新

        Args:
            plugin_name_str: 插件名称
            current_version: 当前版本
            auto_update: 是否自动更新
            target_version: 指定目标版本号，为 None 时智能选择最佳版本

        Returns:
            bool: 是否成功获取到更新信息（用于计数）
        """
        plugin_print(t("update.checking", plugin_name_str))

        # 兼容 version 为 None 或空字符串的插件
        if not current_version:
            current_version = "0.0.0"

        plugin_obj = self.get_plugin_update_info(plugin_name_str)
        if not plugin_obj:
            plugin_print(t("update.no_update_url", plugin_name_str), "WARNING")
            return False

        try:
            update_url = plugin_obj.update_url
            plugin_print(t("update.fetching", update_url, plugin_name_str))

            request = urllib.request.Request(update_url)
            request.add_header("User-Agent", plugin_name_str)

            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status != 200:
                    plugin_print(t("update.fetch_failed", plugin_name_str, response.status), "WARNING")
                    return False
                update_data = json.loads(response.read().decode('utf-8'))

            latest_version = None
            download_url = None
            update_content = t("general.no_content")
            author = t("general.unknown_author")
            update_time = t("general.unknown_time")
            explicit_target = False

            # 单版本格式
            if "version" in update_data and "download_url" in update_data:
                latest_version = update_data["version"]
                download_url = update_data["download_url"]
                update_content = update_data.get("update_content", t("general.no_content"))
                author = update_data.get("author", t("general.unknown_author"))
                update_time = update_data.get("update_time", t("general.unknown_time"))

                if target_version:
                    if compare_versions(target_version, latest_version) != 0:
                        plugin_print(t("update.version_not_found", plugin_name_str, target_version), "WARNING")
                        return True
                    explicit_target = True

            # 多版本格式
            elif "latest_version" in update_data and "versions" in update_data:
                versions = update_data["versions"]

                if not isinstance(versions, dict) or not versions:
                    plugin_print(t("update.format_error", plugin_name_str), "WARNING")
                    return True

                if target_version:
                    # 指定目标版本（强制安装，跳过版本比较）
                    target_key = find_version_key(versions, target_version)
                    if not target_key:
                        plugin_print(t("update.version_not_found", plugin_name_str, target_version), "WARNING")
                        return True
                    target_info = versions[target_key]
                    if not isinstance(target_info, dict):
                        plugin_print(t("update.format_error", plugin_name_str), "WARNING")
                        return True
                    latest_version = target_key
                    explicit_target = True
                    download_url = target_info.get("download_url", "")
                    update_content = target_info.get("update_content", t("general.no_content"))
                    author = target_info.get("author", t("general.unknown_author"))
                    update_time = target_info.get("update_time", t("general.unknown_time"))
                else:
                    # 智能选择最佳版本
                    user_is_prerelease_flag = is_prerelease(current_version)
                    candidate_ver = None
                    sorted_vers = sorted(versions.keys(), key=lambda v: compare_versions(v, "0.0.0"), reverse=True)

                    if user_is_prerelease_flag:
                        # 测试版用户：1) 最新正式版 > 2) 最新测试版
                        for ver in sorted_vers:
                            if not is_prerelease(ver) and compare_versions(ver, current_version) > 0:
                                candidate_ver = ver
                                break
                        if not candidate_ver:
                            for ver in sorted_vers:
                                if is_prerelease(ver) and compare_versions(ver, current_version) > 0:
                                    candidate_ver = ver
                                    break
                    else:
                        # 正式版用户：最新正式版
                        for ver in sorted_vers:
                            if not is_prerelease(ver) and compare_versions(ver, current_version) > 0:
                                candidate_ver = ver
                                break

                    if not candidate_ver:
                        plugin_print(t("update.up_to_date", plugin_name_str, current_version))
                        return True

                    version_info = versions[candidate_ver]
                    if not isinstance(version_info, dict):
                        plugin_print(t("update.format_error", plugin_name_str), "WARNING")
                        return True
                    latest_version = candidate_ver
                    download_url = version_info.get("download_url", "")
                    update_content = version_info.get("update_content", t("general.no_content"))
                    author = version_info.get("author", t("general.unknown_author"))
                    update_time = version_info.get("update_time", t("general.unknown_time"))

            else:
                plugin_print(t("update.no_required_info", plugin_name_str), "WARNING")
                return True

            if not download_url:
                plugin_print(t("update.no_download_url", plugin_name_str), "WARNING")
                return True

            # 版本比较
            version_comparison = compare_versions(latest_version, current_version)

            if version_comparison > 0 or explicit_target:
                plugin_print("=" * 80, "INFO")
                if explicit_target:
                    plugin_print(t("update.target_version", plugin_name_str, latest_version, current_version))
                else:
                    plugin_print(t("update.new_version", plugin_name_str, latest_version, current_version))
                plugin_print(t("update.author", author))
                plugin_print(t("update.time", update_time))
                plugin_print(t("update.content", update_content))
                plugin_print(t("update.download_url", download_url))
                plugin_print("=" * 80, "INFO")

                if auto_update:
                    self.download_and_update_plugin_from_url(plugin_name_str, latest_version, download_url)
            elif version_comparison < 0:
                plugin_print(t("update.newer_than_latest", plugin_name_str, current_version, latest_version), "INFO")
            else:
                plugin_print(t("update.up_to_date", plugin_name_str, current_version))

            return True

        except Exception as e:
            plugin_print(t("update.check_error", plugin_name_str, str(e)), "ERROR")
            return False

    def _print_version_list_with_recommend(self, plugin_name_str, versions, pversion, update_data, page=1):
        """计算推荐版本并打印分页版本列表"""
        user_is_prerelease_flag = is_prerelease(pversion)
        sorted_vers = sorted(versions.keys(), key=lambda v: compare_versions(v, "0.0.0"), reverse=True)
        recommended_ver = ""
        if user_is_prerelease_flag:
            # 测试版用户: 1)最新正式版 2)最新测试版
            for ver in sorted_vers:
                if not is_prerelease(ver):
                    recommended_ver = ver
                    break
            if not recommended_ver:
                for ver in sorted_vers:
                    if is_prerelease(ver):
                        recommended_ver = ver
                        break
        else:
            # 正式版用户：最新正式版
            for ver in sorted_vers:
                if not is_prerelease(ver):
                    recommended_ver = ver
                    break
        if not recommended_ver:
            recommended_ver = update_data.get("latest_version", "")
        print_version_list(plugin_name_str, versions, pversion, recommended_ver, page)

    def print_version_detail(self, plugin_name_str, version_str, versions):
        """打印单个版本的详细信息"""
        plugin_print(t("update.version_detail", plugin_name_str, version_str))
        key = find_version_key(versions, version_str)
        if not key:
            plugin_print(t("update.version_not_found", plugin_name_str, version_str), "WARNING")
            return
        info = versions[key]
        if isinstance(info, dict):
            tag = t("general.pre_release" if is_prerelease(key) else "general.stable")
            plugin_print(f"  v{key} ({tag})")
            plugin_print("  " + t("update.author", info.get("author", t("general.unknown_author"))))
            plugin_print("  " + t("update.time", info.get("update_time", t("general.unknown_time"))))
            plugin_print("  " + t("update.content", info.get("update_content", t("general.no_content"))))
            download_url = info.get("download_url", "")
            if download_url:
                plugin_print("  " + t("update.download_url", download_url))

    # ── 下载 / 安装 ──

    def download_and_update_plugin_from_url(self, plugin_name_str, version_str, download_url):
        """从指定URL下载并更新插件（支持 ZIP 和 .whl/.py 单文件）"""
        try:
            plugin_print(t("download.from_url", download_url, plugin_name_str, version_str))

            # 安全检查
            if not download_url or not download_url.startswith(("http://", "https://")):
                plugin_print(t("download.invalid_url", download_url), "ERROR")
                return

            # 创建临时目录
            temp_dir = Path("./plugins/_temp_update")
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    plugin_print(t("download.clean_dir_error", str(temp_dir), str(e)), "WARNING")

            temp_dir.mkdir(parents=True, exist_ok=True)

            # 下载文件
            file_name = download_url.split('/')[-1].split('?')[0]
            if not file_name or not file_name.endswith(('.whl', '.py', '.zip')):
                # 尝试从 Content-Disposition 获取文件名
                file_name = f"{plugin_name_str}-{version_str}.zip"

            temp_file = temp_dir / file_name
            plugin_print(t("download.downloading", file_name))

            req = urllib.request.Request(download_url)
            req.add_header("User-Agent", plugin_name_str)

            with urllib.request.urlopen(req, timeout=60) as response, open(temp_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            # 根据文件类型处理
            if file_name.endswith('.zip'):
                self._install_from_archive(plugin_name_str, version_str, temp_file, temp_dir)
            else:
                # .whl 或 .py 单文件
                self._install_single_file(plugin_name_str, temp_file, version_str)

            # 清理临时目录
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception:
                pass

        except Exception as e:
            plugin_print(t("download.plugin_failed", plugin_name_str, str(e)), "ERROR")

    def _find_plugin_file_path(self, plugin_name_str):
        """查找插件的文件路径"""
        for p in self.server.plugin_manager.plugins:
            if p.name == plugin_name_str:
                if hasattr(p, 'plugin_loader') and p.plugin_loader:
                    loader = p.plugin_loader
                    if hasattr(loader, 'get_plugin_file'):
                        return Path(loader.get_plugin_file(p))
                if hasattr(p, '__file__'):
                    file_path = Path(p.__file__)
                    if file_path.suffix in ['.py', '.whl']:
                        return file_path
                    if file_path.is_dir():
                        init_file = file_path / '__init__.py'
                        if init_file.exists():
                            return init_file
                break

        # 在 plugins 目录中查找
        plugins_dir = Path("./plugins")
        if plugins_dir.exists():
            for ext in ['*.whl', '*.py']:
                for f in plugins_dir.glob(ext):
                    if plugin_name_str in f.name:
                        return f
        return None

    def _install_single_file(self, plugin_name_str, new_file, version_str=""):
        """安装单个文件（.whl 或 .py）"""
        plugin_file_path = self._find_plugin_file_path(plugin_name_str)
        dest = Path("./plugins") / new_file.name

        # 删除旧文件
        if plugin_file_path and plugin_file_path.exists():
            try:
                plugin_file_path.unlink()
            except Exception as e:
                plugin_print(t("download.copy_error", str(e)), "ERROR")
                return

        # 放入新文件（保留原始文件名）
        shutil.copy2(new_file, dest)
        plugin_print(t("download.file_updated", str(dest.name)))

        # 重载
        self._reload_after_update(plugin_name_str, version_str)

    def _install_from_archive(self, plugin_name_str, version_str, archive_file, temp_dir):
        """从 ZIP 压缩包安装插件"""
        plugin_print(t("download.extracting"))

        extract_dir = temp_dir / "_extracted"
        extract_dir.mkdir(exist_ok=True)

        try:
            with zipfile.ZipFile(archive_file, 'r') as zf:
                zf.extractall(extract_dir)
        except Exception as e:
            plugin_print(t("download.plugin_failed", plugin_name_str, str(e)), "ERROR")
            return

        # 检测根目录
        root_dir = extract_dir
        try:
            entries = list(extract_dir.iterdir())
        except Exception as e:
            plugin_print(t("download.scan_error", str(e)), "ERROR")
            return

        if len(entries) == 1 and entries[0].is_dir():
            root_dir = entries[0]
            plugin_print(t("download.detect_root", str(root_dir.name)))

        # 收集所有 .whl/.py 文件
        install_files = []
        for f in root_dir.rglob("*"):
            if f.is_file() and f.suffix in ['.whl', '.py']:
                install_files.append(f)

        if not install_files:
            plugin_print(t("download.install_empty"), "WARNING")
            return

        # 查找原插件路径并备份
        plugin_file_path = self._find_plugin_file_path(plugin_name_str)
        backup_path = None

        if plugin_file_path and plugin_file_path.exists():
            backup_dir = temp_dir / "_backup"
            backup_dir.mkdir(exist_ok=True)
            try:
                if plugin_file_path.is_file():
                    backup_path = backup_dir / plugin_file_path.name
                    shutil.copy2(plugin_file_path, backup_path)
                    plugin_print(t("download.backed_up", str(backup_path)))
                elif plugin_file_path.parent.is_dir():
                    backup_path = backup_dir / plugin_file_path.parent.name
                    shutil.copytree(plugin_file_path.parent, backup_path)
                    plugin_print(t("download.backup_dir_done", str(backup_path)))
            except Exception as e:
                plugin_print(t("download.backup_failed", str(e)), "WARNING")

        # 复制文件
        installed_count = 0
        try:
            for f in install_files:
                rel = f.relative_to(root_dir)
                if len(rel.parts) > 1:
                    dest = Path("./plugins") / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dest)
                    plugin_print(t("download.copy_sub", rel.parts[0], "/".join(rel.parts[1:])))
                else:
                    dest = Path("./plugins") / rel.name
                    shutil.copy2(f, dest)
                    plugin_print(t("download.copy", rel.name))
                installed_count += 1
        except Exception as e:
            plugin_print(t("download.copy_error", str(e)), "ERROR")
            # 回滚
            if backup_path and backup_path.exists():
                try:
                    if backup_path.is_file():
                        shutil.copy2(backup_path, plugin_file_path)
                    else:
                        if plugin_file_path.parent.exists():
                            shutil.rmtree(plugin_file_path.parent)
                        shutil.copytree(backup_path, plugin_file_path.parent)
                    plugin_print(t("download.rollback_done"))
                except Exception as e2:
                    plugin_print(t("download.rollback_failed", str(e2)), "ERROR")
            return

        plugin_print(t("download.installed", str(installed_count), "./plugins/"))

        # 重载
        self._reload_after_update(plugin_name_str, version_str)

    def _reload_after_update(self, plugin_name_str, version_str):
        """更新后重载"""
        if version_str:
            plugin_print(t("download.updated_reloading", plugin_name_str, version_str))
        else:
            plugin_print(t("download.updated_reloading", plugin_name_str, "?"))

        try:
            # 清除模块缓存
            for p in list(self.server.plugin_manager.plugins):
                if p.name == plugin_name_smallest or p.name == plugin_name_str:
                    continue
                module_name = f"endstone_{p.name}"
                if module_name in sys.modules:
                    del sys.modules[module_name]
                modules_to_remove = [key for key in list(sys.modules.keys()) if key.startswith(module_name)]
                for module in modules_to_remove:
                    del sys.modules[module]

            self.server.reload()
            plugin_print(t("download.reloaded", plugin_name_str), "SUCCESS")
        except Exception as e:
            plugin_print(t("download.reload_failed", str(e)), "ERROR")
            plugin_print(t("download.reload_manual"), "WARNING")

    # ── 命令处理 ──

    def on_command(self, sender: CommandSenderWrapper, command, args: list):
        """处理命令"""
        if command.name in ("easycheckupdate", "ecu"):
            if not sender.has_permission("easycheckupdate.command.use"):
                sender.send_message(f"§c{t('command.no_permission')}")
                return True

            if len(args) == 0:
                # /ecu → 显示帮助
                for line in t("command.help").split('\n'):
                    sender.send_message(f"§e{line}")
                return True

            sub = args[0].lower()

            if sub == "all":
                # /ecu all → 检查全部
                self.check_all_plugins_update(force=True)
                sender.send_message(f"§a{t('command.checking_all')}")
                return True

            if sub == "reload":
                # /ecu reload → 重载配置
                try:
                    self.load_config()
                    lang = self.plugin_config.get("language", "zh_CN")
                    apply_configured_language(lang)
                    sender.send_message(f"§a{t('config.reload_success')}")
                    plugin_print(t("config.reloaded"), "SUCCESS")
                except Exception as e:
                    sender.send_message(f"§c{t('config.reload_failed', str(e))}")
                    plugin_print(t("config.reload_failed", str(e)), "ERROR")
                return True

            if sub == "update":
                # /ecu update <plugin> [version]
                if len(args) < 2:
                    sender.send_message(f"§c{t('command.update_usage')}")
                    return True
                # 兼容 EndStone 两种解析行为：版本号可能在 args[2] 也可能合并在 args[1] 中
                if len(args) > 2:
                    plugin_name_str = args[1]
                    target_ver = normalize_version(args[2])
                else:
                    parts = args[1].split(' ', 1)
                    plugin_name_str = parts[0]
                    target_ver = normalize_version(parts[1]) if len(parts) > 1 else None

                plugin_obj = None
                for p in self.server.plugin_manager.plugins:
                    if p.name == plugin_name_str:
                        plugin_obj = p
                        break
                if plugin_obj:
                    self.check_plugin_update(plugin_name_str, plugin_obj.version,
                                             auto_update=True, target_version=target_ver)
                    sender.send_message(f"§a{t('command.checking_update', plugin_name_str)}")
                else:
                    sender.send_message(f"§c{t('command.plugin_not_found', plugin_name_str)}")
                return True

            if sub == "info":
                # /ecu info <plugin> [version]
                if len(args) < 2:
                    sender.send_message(f"§c{t('command.info_usage')}")
                    return True
                # 兼容 EndStone 两种解析行为：版本号可能在 args[2] 也可能合并在 args[1] 中
                if len(args) > 2:
                    plugin_name_str = args[1]
                    target_ver = normalize_version(args[2])
                else:
                    parts = args[1].split(' ', 1)
                    plugin_name_str = parts[0]
                    target_ver = normalize_version(parts[1]) if len(parts) > 1 else None

                plugin_obj = self.get_plugin_update_info(plugin_name_str)
                if not plugin_obj:
                    sender.send_message(f"§c{t('command.plugin_not_found', plugin_name_str)}")
                    return True

                try:
                    request = urllib.request.Request(plugin_obj.update_url)
                    request.add_header("User-Agent", plugin_name_str)
                    with urllib.request.urlopen(request, timeout=10) as response:
                        update_data = json.loads(response.read().decode('utf-8'))
                except Exception as e:
                    plugin_print(t("update.fetch_failed", plugin_name_str, str(e)), "ERROR")
                    return True

                versions = update_data.get("versions")
                if not versions or not isinstance(versions, dict):
                    sender.send_message(f"§c{t('update.format_error', plugin_name_str)}")
                    return True

                try:
                    pversion = plugin_obj.version
                except AttributeError:
                    pversion = "unknown"

                if target_ver:
                    # p+数字 → 查看指定页码的版本列表
                    if re.match(r'^p\d+$', target_ver, re.IGNORECASE):
                        page = int(target_ver[1:])
                        sender.send_message(f"§a{t('command.querying_list', plugin_name_str)}")
                        self._print_version_list_with_recommend(plugin_name_str, versions, pversion, update_data, page=page)
                    else:
                        # 查看指定版本详情
                        sender.send_message(f"§a{t('command.querying_detail', plugin_name_str, target_ver)}")
                        self.print_version_detail(plugin_name_str, target_ver, versions)
                else:
                    # 查看版本列表（第1页）
                    sender.send_message(f"§a{t('command.querying_list', plugin_name_str)}")
                    self._print_version_list_with_recommend(plugin_name_str, versions, pversion, update_data)
                return True

            if sub == "check":
                # /ecu check <plugin>
                if len(args) < 2:
                    sender.send_message(f"§c{t('command.check_usage')}")
                    return True
                plugin_name_str = args[1]
                plugin_obj = None
                for p in self.server.plugin_manager.plugins:
                    if p.name == plugin_name_str:
                        plugin_obj = p
                        break
                if plugin_obj:
                    self.check_plugin_update(plugin_name_str, plugin_obj.version)
                    sender.send_message(f"§a{t('command.checking_plugin', plugin_name_str)}")
                else:
                    sender.send_message(f"§c{t('command.plugin_not_found', plugin_name_str)}")
                return True

            # 未知子命令
            sender.send_message(f"§c{t('command.unknown_subcommand', sub)}")

        return False