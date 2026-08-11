import re
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# 从源码读取版本号（单一来源，避免与 easycheckupdate_plugin.py 重复）
with open("src/endstone_easycheckupdate/easycheckupdate_plugin.py", "r", encoding="utf-8") as f:
    content = f.read()
    match = re.search(r'^plugin_version\s*=\s*"(.+?)"', content, re.M)
    version = match.group(1) if match else "0.0.0"

setuptools.setup(
    name="endstone-easycheckupdate",
    version=version,
    author="MengHanLOVE",
    url='https://github.com/MengHanLOVE1027',
    author_email="2193438288@qq.com",
    description="一个基于 EndStone 的插件更新检查工具 / A plugin update checker based on EndStone.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
)
