# python 库
import os, json, shutil, zipfile, time, logging, random
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

# TAG: 全局常量
plugin_name = "EasyCheckUpdate"
plugin_name_smallest = "easycheckupdate"
plugin_description = "一个基于 EndStone 的插件更新检查工具 / A plugin update checker based on EndStone."
plugin_version = "0.1.2"
plugin_author = ["梦涵LOVE"]
plugin_website = "https://www.minebbs.com/resources/easycheckupdate-ecu-endstone.15500/"
plugin_github_link = "https://github.com/MengHanLOVE1027/endstone-easycheckupdate"
plugin_minebbs_link = "https://www.minebbs.com/resources/easycheckupdate-ecu-endstone.15500/"
plugin_license = "AGPL-3.0"
plugin_copyright = "务必保留原作者信息！"
plugin_update_url = "https://raw.githubusercontent.com/MengHanLOVE1027/endstone-easycheckupdate/refs/heads/main/update_versions.json"

success_plugin_version = "v" + plugin_version
plugin_full_name = plugin_name + " " + success_plugin_version

plugin_path = Path(f"./plugins/{plugin_name}")
plugin_config_path = plugin_path / "config" / f"{plugin_name}.json"


# --- 随机颜色系统 ---
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
    c2, attempts = 0, 0
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

# TAG: 日志系统设置
# 创建logs目录
log_dir = Path(f"./logs/{plugin_name}")
if not log_dir.exists():
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[{plugin_name}] 创建日志目录失败: {e}")

# 设置日志文件名，按日期分割
log_file = log_dir / f"{plugin_name_smallest}_{datetime.now().strftime('%Y%m%d')}.log"

# 创建插件专用的logger
logger = logging.getLogger(plugin_name)
logger.setLevel(logging.DEBUG)

# 配置日志处理器
try:
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"[{plugin_name}] 配置日志文件处理器失败: {e}")

# NOTE: 版本比较函数
def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号
    :param version1: 版本号1
    :param version2: 版本号2
    :return: -1 表示 version1 < version2，0 表示 version1 == version2，1 表示 version1 > version2
    """
    # 移除版本号前的 'v' 或 'V' 前缀
    v1 = version1.lstrip('vV')
    v2 = version2.lstrip('vV')

    # 分割版本号
    v1_parts = v1.split('.')
    v2_parts = v2.split('.')

    # 确保两个版本号的长度相同
    max_length = max(len(v1_parts), len(v2_parts))
    v1_parts.extend(['0'] * (max_length - len(v1_parts)))
    v2_parts.extend(['0'] * (max_length - len(v2_parts)))

    # 逐个比较版本号部分
    for i in range(max_length):
        try:
            v1_num = int(v1_parts[i])
            v2_num = int(v2_parts[i])

            if v1_num < v2_num:
                return -1
            elif v1_num > v2_num:
                return 1
        except ValueError:
            # 如果无法转换为数字，则按字符串比较
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1

    return 0


# NOTE: 自制日志头
def plugin_print(text, level="INFO") -> bool:
    """
    自制 print 日志输出函数
    :param text: 文本内容
    :param level: 日志级别 (DEBUG, INFO, WARNING, ERROR, SUCCESS)
    :return: True
    """
    # 日志级别颜色映射
    level_colors = {
        "DEBUG": "\x1b[36m",    # 青色
        "INFO": "\x1b[37m",     # 白色
        "WARNING": "\x1b[33m",  # 黄色
        "ERROR": "\x1b[31m",    # 红色
        "SUCCESS": "\x1b[32m"   # 绿色
    }
    
    # 获取日志级别颜色
    level_color = level_colors.get(level, "\x1b[37m")
    
    # 自制Logger消息头
    logger_head = f"[\x1b[96m{plugin_name}\x1b[0m] [{level_color}{level}\x1b[0m] "
    
    # 使用锁确保线程安全
    with print_lock:
        print(logger_head + str(RandomColor(text)))
    
    # 记录到日志文件
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "SUCCESS": logging.INFO
    }
    
    # 将SUCCESS级别映射为INFO级别记录到日志
    log_level = log_level_map.get(level, logging.INFO)
    logger.log(log_level, str(text))
    
    return True


# 检查插件文件路径，以防后续出问题
if not plugin_path.exists():
    # print(f"文件夹 '{plugin_path.resolve()}' 不存在。")
    os.makedirs(plugin_path, exist_ok=True)  # 使用 makedirs 可以创建多级目录
# else:
    # print(f"文件夹 '{plugin_path.resolve()}' 存在。")

print_lock = Lock()  # 用于线程安全的日志输出

# TAG: 插件入口点
class EasyCheckUpdatePlugin(Plugin):
    """
    插件入口点
    """

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
        # 检查更新命令
        "checkupdate": {
            "description": "检查插件更新",
            "usages": [
                "/checkupdate",
                "/checkupdate <plugin_name: str>",
                "/checkupdate <plugin_name: str> update"
            ],
            "permissions": ["easycheckupdate.command.use"],
            "aliases": ["cu"],
        },
    }

    # NOTE: 权限组
    permissions = {
        # 只有 OP 玩家才可以执行命令
        "easycheckupdate.command.use": {
            "description": "允许使用检查更新命令",
            "default": "op",
        },
    }

    def __init__(self):
        super().__init__()
        self.check_update_on_load = True  # 启动时检查更新
        self.check_interval = 1800  # 检查间隔（秒），默认为30分钟
        self.check_delay = 10  # 启用后延迟检查更新的时间（秒），默认为5秒
        self.last_check_time = 0  # 上次检查时间
        self.plugin_config = {}  # 配置字典

    def on_load(self):
        """插件加载时调用"""
        plugin_print(f"{plugin_full_name} 正在加载...")

        # 加载或创建配置文件
        self.load_config()
        print(RandomColor("███████╗ █████╗ ███████╗██╗   ██╗██╗     ██╗   ██╗ ██████╗██╗  ██╗██╗   ██╗██████╗ ██╗██╗     ██╗      █████╗ ██████╗ "))
        print(RandomColor("██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝██║     ██║   ██║██╔════╝██║ ██╔╝╚██╗ ██╔╝██╔══██╗██║██║     ██║     ██╔══██╗██╔══██╗"))
        print(RandomColor("█████╗  ███████║███████╗ ╚████╔╝ ██║     ██║   ██║██║     █████╔╝  ╚████╔╝ ██████╔╝██║██║     ██║     ███████║██████╔╝"))
        print(RandomColor("██╔══╝  ██╔══██║╚════██║  ╚██╔╝  ██║     ██║   ██║██║     ██╔═██╗   ╚██╔╝  ██╔═══╝ ██║██║     ██║     ██╔══██║██╔══██╗"))
        print(RandomColor("███████╗██║  ██║███████║   ██║   ███████╗╚██████╔╝╚██████╗██║  ██╗   ██║   ██║     ██║███████╗███████╗██║  ██║██║  ██║"))
        print(RandomColor("╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝"))
        print(RandomColor(f"""                                作者：{plugin_author[0]}               版本：{plugin_version}"""))
        plugin_print(f"="*80, "INFO")
        plugin_print(f"{plugin_name} - {plugin_description}")
        plugin_print(f"感谢您使用Easy系列插件！")
        plugin_print(f"本插件使用 {plugin_license} 许可证协议进行发布")
        plugin_print(f"插件GitHub项目仓库地址：{plugin_github_link}")
        plugin_print(f"插件MineBBS资源帖：{plugin_minebbs_link}")
        plugin_print(f"Easy系列插件交流群：1083195477")
        plugin_print(f"作者：{plugin_author[0]} | 版本：{plugin_version}")
        plugin_print(f"="*80, "INFO")

        plugin_print(f"{plugin_full_name} 已加载!")

    def on_enable(self):
        """插件启用时调用"""
        plugin_print(f"{plugin_full_name} 正在启用...")

        # 启用 bStats
        try:
            metrics = BStats(self, 29349)  # 替换为你的 bStats ID
            metrics.add_custom_chart(SimplePie("check_interval", lambda: str(self.check_interval)))
            metrics.start()
        except Exception as e:
            plugin_print(f"bStats 启用失败: {e}", "ERROR")

        plugin_print(f"{plugin_full_name} 已启用!")

        # 延迟检查更新
        if self.check_update_on_load:
            plugin_print(f"将在 {self.check_delay} 秒后检查更新...")
            self.server.scheduler.run_task(
                self,
                lambda: self.check_all_plugins_update(),
                delay=self.check_delay * 20  # 转换为tick（1秒=20tick）
            )

    def on_disable(self):
        """插件禁用时调用"""
        plugin_print(f"{plugin_full_name} 正在禁用...")
        plugin_print(f"{plugin_full_name} 已禁用!")

    def load_config(self):
        """加载配置文件"""
        try:
            if plugin_config_path.exists():
                # 检查文件大小，如果为空则重新创建配置
                if plugin_config_path.stat().st_size == 0:
                    plugin_print("配置文件为空，将重新创建默认配置", "WARNING")
                    self.create_default_config()
                    return

                with open(plugin_config_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        plugin_print("配置文件内容为空，将重新创建默认配置", "WARNING")
                        self.create_default_config()
                        return

                    self.plugin_config = json.loads(content)

                # 从配置中读取设置
                self.check_update_on_load = self.plugin_config.get("check_update_on_load", True)
                self.check_interval = self.plugin_config.get("check_interval", 1800)
                self.check_delay = self.plugin_config.get("check_delay", 5)
                self.last_check_time = self.plugin_config.get("last_check_time", 0)
            else:
                # 创建默认配置
                self.create_default_config()
        except Exception as e:
            plugin_print(f"加载配置文件失败: {e}", "ERROR")
            self.create_default_config()

    def create_default_config(self):
        """创建默认配置"""
        self.plugin_config = {
            "check_update_on_load": True,
            "check_interval": 1800,
            "check_delay": 10,
            "last_check_time": 0
        }
        self.save_config()

    def save_config(self):
        """保存配置文件"""
        try:
            # 确保配置目录存在
            plugin_config_path.parent.mkdir(parents=True, exist_ok=True)

            # 更新当前设置
            self.plugin_config["check_update_on_load"] = self.check_update_on_load
            self.plugin_config["check_interval"] = self.check_interval
            self.plugin_config["check_delay"] = self.check_delay
            self.plugin_config["last_check_time"] = self.last_check_time

            # 保存配置
            with open(plugin_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            plugin_print(f"保存配置文件失败: {e}", "ERROR")

    def check_all_plugins_update(self):
        """检查所有插件的更新"""
        plugin_print("正在检查所有插件的更新...")

        # 获取当前时间
        current_time = time.time()

        # 检查是否需要更新
        if current_time - self.last_check_time < self.check_interval:
            plugin_print(f"距离上次检查不足 {self.check_interval} 秒，跳过本次检查")
            return

        # 更新检查时间
        self.last_check_time = current_time
        self.save_config()

        # 遍历所有已加载的插件
        for plugin in self.server.plugin_manager.plugins:
            plugin_name = plugin.name
            # 尝试获取版本号，如果失败则使用 "unknown"
            try:
                plugin_version = plugin.version
            except AttributeError:
                plugin_version = "unknown"
            self.check_plugin_update(plugin_name, plugin_version)

    def check_plugin_update(self, plugin_name, current_version, auto_update=False):
        """检查指定插件的更新

        Args:
            plugin_name: 插件名称
            current_version: 当前版本
            auto_update: 是否自动更新插件
        """
        plugin_print(f"正在检查插件 {plugin_name} 的更新...")

        # 检查插件是否有update_url字段
        plugin_obj = None
        for p in self.server.plugin_manager.plugins:
            if p.name == plugin_name:
                plugin_obj = p
                break

        if plugin_obj and hasattr(plugin_obj, 'update_url'):
            try:
                # 从update_url字段获取更新信息
                update_url = plugin_obj.update_url
                plugin_print(f"正在从 {update_url} 获取插件 {plugin_name} 的更新信息...")

                # 下载更新信息
                request = urllib.request.Request(update_url)
                request.add_header("User-Agent", plugin_name)

                with urllib.request.urlopen(request, timeout=10) as response:
                    update_data = json.loads(response.read().decode('utf-8'))

                # 检查是否包含必要的信息
                # 支持两种格式：单版本格式和多版本格式
                if "version" in update_data and "download_url" in update_data:
                    # 单版本格式
                    latest_version = update_data["version"]
                    download_url = update_data["download_url"]
                    update_content = update_data.get("update_content", "无更新内容")
                    author = update_data.get("author", "未知作者")
                    update_time = update_data.get("update_time", "未知时间")
                elif "latest_version" in update_data and "versions" in update_data:
                    # 多版本格式
                    latest_version = update_data["latest_version"]
                    versions = update_data["versions"]

                    # 获取最新版本的详细信息
                    if isinstance(versions, list):
                        # 数组格式
                        version_info = versions[0] if versions else {}
                    elif isinstance(versions, dict):
                        # 对象格式
                        version_info = versions.get(latest_version, {})
                    else:
                        plugin_print(f"插件 {plugin_name} 的更新信息格式不正确", "WARNING")
                        return

                    download_url = version_info.get("download_url", "")
                    update_content = version_info.get("update_content", "无更新内容")
                    author = version_info.get("author", "未知作者")
                    update_time = version_info.get("update_time", "未知时间")

                    if not download_url:
                        plugin_print(f"插件 {plugin_name} 的更新信息缺少下载链接", "WARNING")
                        return
                else:
                    plugin_print(f"插件 {plugin_name} 的更新信息文件缺少必要信息", "WARNING")
                    return

                # 使用版本比较函数比较版本号
                version_comparison = compare_versions(latest_version, current_version)
                if version_comparison > 0:
                    plugin_print(f"="*80, "INFO")
                    plugin_print(f"插件 {plugin_name} 有新版本: {latest_version} (当前版本: {current_version})")
                    plugin_print(f"作者: {author}")
                    plugin_print(f"更新时间: {update_time}")
                    plugin_print(f"更新内容: {update_content}")
                    plugin_print(f"下载地址: {download_url}")
                    plugin_print(f"="*80, "INFO")

                    # 如果启用了自动更新，则下载并更新插件
                    if auto_update:
                        self.download_and_update_plugin_from_url(plugin_name, latest_version, download_url)
                elif version_comparison < 0:
                    plugin_print(f"插件 {plugin_name} 的当前版本 {current_version} 比最新版本 {latest_version} 更新", "INFO")
                else:
                    plugin_print(f"插件 {plugin_name} 已是最新版本: {current_version}")
                return
            except Exception as e:
                plugin_print(f"从 {update_url} 获取插件 {plugin_name} 的更新信息时出错: {e}", "WARNING")

        plugin_print(f"未找到插件 {plugin_name} 的 update_url 字段，无法检查更新", "WARNING")

    def download_and_update_plugin_from_url(self, plugin_name, version, download_url):
        """
        从指定URL下载并更新插件

        Args:
            plugin_name: 插件名称
            version: 要更新的版本号
            download_url: 下载链接
        """
        try:
            plugin_print(f"正在从 {download_url} 下载插件 {plugin_name} 版本 {version}...")

            # 创建临时目录
            temp_dir = Path("./plugins/_temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 从URL中提取文件名
            file_name = download_url.split('/')[-1]
            if not file_name.endswith(('.whl', '.py')):
                file_name = f"{plugin_name}-{version}.whl"

            # 下载文件
            temp_file = temp_dir / file_name
            request = urllib.request.Request(download_url)
            request.add_header("User-Agent", plugin_name)

            with urllib.request.urlopen(request, timeout=30) as response, open(temp_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            plugin_print(f"文件已下载到 {temp_file}")

            # 使用现有的更新逻辑
            self._update_plugin_file(plugin_name, temp_file)

            # 清理临时文件
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    plugin_print(f"已清理临时文件: {temp_file}")
            except Exception as e:
                plugin_print(f"清理临时文件时出错: {e}", "WARNING")

        except Exception as e:
            plugin_print(f"从URL下载插件 {plugin_name} 时出错: {e}", "ERROR")

    def _update_plugin_file(self, plugin_name, temp_file):
        """
        更新插件文件的内部方法

        Args:
            plugin_name: 插件名称
            temp_file: 临时文件路径
        """
        try:
            # 查找插件文件路径
            plugin_file_path = None

            # 尝试通过插件加载器获取插件文件路径
            for p in self.server.plugin_manager.plugins:
                if p.name == plugin_name:
                    # 尝试获取插件文件路径
                    if hasattr(p, 'plugin_loader') and p.plugin_loader:
                        # 尝试从插件加载器获取文件路径
                        plugin_loader = p.plugin_loader
                        if hasattr(plugin_loader, 'get_plugin_file'):
                            plugin_file_path = Path(plugin_loader.get_plugin_file(p))

                    # 如果没有找到，尝试使用__file__属性
                    if not plugin_file_path and hasattr(p, '__file__'):
                        file_path = Path(p.__file__)
                        # 检查是否是.py文件或.whl文件
                        if file_path.suffix in ['.py', '.whl']:
                            plugin_file_path = file_path
                        else:
                            # 如果是目录，查找其中的__init__.py
                            if file_path.is_dir():
                                init_file = file_path / '__init__.py'
                                if init_file.exists():
                                    plugin_file_path = init_file
                    break

            if not plugin_file_path:
                # 尝试在plugins目录中查找匹配的文件
                plugins_dir = Path("./plugins")
                if plugins_dir.exists():
                    # 查找匹配插件名称的.whl或.py文件
                    for file in plugins_dir.glob("*.whl"):
                        if plugin_name in file.name:
                            plugin_file_path = file
                            break

                    if not plugin_file_path:
                        for file in plugins_dir.glob("*.py"):
                            if plugin_name in file.name:
                                plugin_file_path = file
                                break

            if plugin_file_path and plugin_file_path.exists():
                # 备份旧文件
                backup_path = plugin_file_path.with_suffix(f"{plugin_file_path.suffix}.bak")
                shutil.copy2(plugin_file_path, backup_path)
                plugin_print(f"已备份旧文件到 {backup_path}")

                # 替换文件
                # 首先删除旧文件
                if plugin_file_path.exists():
                    plugin_file_path.unlink()

                # 复制新文件到目标位置
                # 使用原始文件名，而不是下载的文件名
                shutil.copy2(temp_file, plugin_file_path)
                plugin_print(f"已更新插件文件: {plugin_file_path.name}")

                # 重新加载服务器以加载新插件
                try:
                    plugin_print(f"正在重新加载服务器以加载新版本的 {plugin_name} 插件...")

                    # 清除所有插件的模块缓存（除了EasyCheckUpdate本身和正在更新的插件）
                    for p in list(self.server.plugin_manager.plugins):
                        # 跳过EasyCheckUpdate插件本身和正在更新的插件
                        if p.name == plugin_name_smallest or p.name == plugin_name:
                            continue

                        module_name = f"endstone_{p.name}"
                        if module_name in sys.modules:
                            del sys.modules[module_name]
                            plugin_print(f"已清除插件 {p.name} 的模块缓存")

                        # 清除可能的子模块
                        modules_to_remove = [key for key in list(sys.modules.keys()) if key.startswith(module_name)]
                        for module in modules_to_remove:
                            del sys.modules[module]

                    # 重新加载服务器
                    self.server.reload()
                    plugin_print(f"服务器已重新加载，插件 {plugin_name} 应该已更新", "SUCCESS")
                except Exception as e:
                    plugin_print(f"重新加载服务器时出错: {e}", "ERROR")
                    # 提示用户需要重启服务器
                    plugin_print(f"插件 {plugin_name} 已更新，但需要重启服务器才能生效", "WARNING")
            else:
                plugin_print(f"无法找到插件 {plugin_name} 的文件路径", "WARNING")
        except Exception as e:
            plugin_print(f"更新插件文件时出错: {e}", "ERROR")
        finally:
            # 清理临时文件
            try:
                if temp_file and temp_file.exists():
                    temp_file.unlink()
                    plugin_print(f"已清理临时文件: {temp_file}")
            except Exception as e:
                plugin_print(f"清理临时文件时出错: {e}", "WARNING")

    def on_command(self, sender: CommandSenderWrapper, command, args: list):
        """处理命令"""
        # 获取命令名称
        if command.name == "checkupdate" or command.name == "cu":
            if not sender.has_permission("easycheckupdate.command.use"):
                sender.send_message("§c你没有权限使用此命令")
                return True

            if len(args) == 0:
                # 检查所有插件的更新
                self.check_all_plugins_update()
                sender.send_message(f"§a正在检查所有插件的更新，请查看控制台获取详细信息")
            elif len(args) == 1:
                # 检查指定插件的更新
                plugin_name = args[0]

                # 查找插件
                plugin_obj = None
                for p in self.server.plugin_manager.plugins:
                    if p.name == plugin_name:
                        plugin_obj = p
                        break

                if plugin_obj:
                    self.check_plugin_update(plugin_name, plugin_obj.version)
                    sender.send_message(f"§a正在检查插件 {plugin_name} 的更新，请查看控制台获取详细信息")
                else:
                    sender.send_message(f"§c未找到插件: {plugin_name}")
            elif len(args) == 2 and args[1].lower() == "update":
                # 检查并更新指定插件
                plugin_name = args[0]

                # 查找插件
                plugin_obj = None
                for p in self.server.plugin_manager.plugins:
                    if p.name == plugin_name:
                        plugin_obj = p
                        break

                if plugin_obj:
                    self.check_plugin_update(plugin_name, plugin_obj.version, auto_update=True)
                    sender.send_message(f"§a正在检查并更新插件 {plugin_name}，请查看控制台获取详细信息")
                else:
                    sender.send_message(f"§c未找到插件: {plugin_name}")
            else:
                sender.send_message("§c用法: /checkupdate [插件名称] [update]")

            return True

        return False