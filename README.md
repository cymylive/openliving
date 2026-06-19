# OpenLiving

轻量级 Windows 桌面生活管理工具。透明悬浮窗 + 系统托盘，集成待办事项与日记灵感。

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Platform](https://img.shields.io/badge/platform-Windows-blue)

---

## 功能一览

- **待办事项** — 透明卡片悬浮显示，点击完成自动隐藏，托盘图标数字计数
- **日记灵感** — 独立编辑面板，支持全文搜索、新建、编辑、浏览历史
- **系统托盘** — 右键菜单完成所有操作：添加待办、日记、位置切换、开机自启
- **透明悬浮** — 窗口背景完全透明，可拖拽，支持四角定位
- **开机自启** — 托盘菜单一键开关，写入注册表

---

## 快速开始

### 下载

从 [Releases](https://github.com/cymylive/openliving/releases) 下载 `OpenLiving-Windows-x64`，双击运行。

### 从源码运行

```bash
pip install pystray pillow
python todo.py
```

### 打包为 exe

```bash
pip install pyinstaller
pyinstaller --onefile -w --name "openliving" todo.py
```

---

## 详细文档

开发文档见 [DEVELOP.md](DEVELOP.md)，涵盖：

- 功能使用说明（待办、日记、窗口控制、开机自启）
- 技术架构（透明窗口、线程安全、数据持久化）
- 代码结构与类方法说明
- 自定义开发（配色、尺寸、字体修改）
- 打包发布与常见问题

---

## 数据文件

| 文件 | 说明 |
|------|------|
| `data.json` | 待办数据（与 exe 同目录，自动生成） |
| `diary.json` | 日记数据（与 exe 同目录，自动生成） |

---

## 协议

MIT © [cymylive](https://github.com/cymylive)
