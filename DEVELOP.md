# OpenLiving — 开发文档

## 项目简介

OpenLiving 是一款 Windows 桌面生活管理工具，采用 Python + tkinter 构建，以**透明悬浮窗**形式常驻屏幕角落，通过系统托盘交互。

### 设计理念

- **轻量**：单文件 exe，无外部依赖运行时，内存占用低
- **无感**：透明背景悬浮显示，不遮挡工作区域
- **快捷**：所有操作在托盘右键菜单完成，键盘快捷键辅助

---

## 功能说明

### 待办事项

| 操作 | 方式 |
|------|------|
| 添加 | 右键托盘 → 添加待办，弹出输入框，回车或点击添加 |
| 完成 | 点击 ○ 或任务文字，自动隐藏（数据保留，标记 done） |
| 删除 | 点击 × 永久删除 |
| 查看 | 主窗口列表实时显示未完成项 |
| 计数 | 托盘图标显示已完成数量（紫色数字） |
| 清除 | 右键托盘 → 清除已完成，删除所有标记已完成的条目 |

### 日记灵感

| 操作 | 方式 |
|------|------|
| 打开 | 右键托盘 → 日记灵感 |
| 新建 | 点击"新建"按钮，右侧编辑区写内容，点击"保存" |
| 浏览 | 左侧列表按时间倒序显示，点击条目在右侧查看全文 |
| 搜索 | 顶部搜索框输入关键词，自动过滤或点击"搜索"按钮 |
| 编辑 | 选中已有条目，修改内容后保存 |

### 窗口控制

| 操作 | 方式 |
|------|------|
| 移动 | 拖拽窗口顶部空白区域 |
| 隐藏 | 点击关闭按钮、按 `Esc` |
| 显示 | 左键点击托盘图标、右键菜单→显示/隐藏 |
| 定位 | 右键→显示位置，可选 左上/右上/左下/右下 |
| 退出 | 右键→退出，或按 `Ctrl+Q` |

### 开机自启

右键托盘菜单中勾选"开机自启"，写入 Windows 注册表：

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Run\openliving
```

取消勾选自动删除注册表项。

---

## 安装使用

### 下载运行

从 [GitHub Releases](https://github.com/cymylive/openliving/releases) 下载 `OpenLiving-Windows-x64`，直接双击运行。

首次启动自动在同目录下创建 `data.json`（待办数据）和 `diary.json`（日记数据）。

### 源码运行

```bash
pip install pystray pillow -i https://pypi.tuna.tsinghua.edu.cn/simple
python todo.py
```

---

## 技术架构

### 依赖

| 库 | 用途 |
|------|------|
| tkinter | GUI 框架，窗口渲染、事件处理 |
| pystray | 系统托盘图标与右键菜单 |
| Pillow | 托盘图标图片生成（动态计数渲染） |
| PyInstaller | 打包为单文件 exe |
| winreg | Windows 注册表操作（开机自启） |

### 核心机制

#### 透明窗口

```
root.attributes('-transparentcolor', '#0a0a12')
```

- 设定一个颜色键为完全透明
- 窗口背景使用该颜色 → 背景完全不可见
- 卡片、文字使用其他颜色 → 正常显示

#### 窗口叠加

```
root.attributes('-topmost', True)
root.attributes('-alpha', 0.70)
```

- `topmost` 确保窗口始终在顶层
- `alpha` 控制整体透明度（0.70 = 70% 不透明）

#### 线程安全

pystray 运行在独立线程中，与 tkinter 主线程通信通过 `root.after()`：

```python
def show_add_dialog(self, icon=None, item=None):
    self.root.after(0, self._open_add_dialog)
```

所有 GUI 操作（创建窗口、修改界面）都在主线程执行。

#### 数据持久化

JSON 文件存储，结构简单：

```json
// data.json - 待办
[
    {"text": "买牛奶", "done": false, "created": "2026-06-20T14:30:00"},
    {"text": "写周报", "done": true,  "created": "2026-06-20T15:00:00"}
]

// diary.json - 日记
[
    {
        "id": 1,
        "text": "今天...",
        "created": "2026-06-20T14:30:00",
        "updated": "2026-06-20T14:30:00"
    }
]
```

---

## 代码结构

```
openliving/
├── todo.py          # 主程序（TodoApp + DiaryApp）
├── openliving.exe   # 打包后的可执行文件
├── data.json        # 待办数据（自动生成）
├── diary.json       # 日记数据（自动生成）
├── README.md        # 快速使用说明
└── .gitignore       # Git 忽略规则
```

### 类说明

#### `TodoApp`（主窗口）

| 方法 | 功能 |
|------|------|
| `__init__` | 初始化窗口属性、加载数据、构建 UI、启动托盘 |
| `build_ui` | 构建拖拽条、Canvas 列表容器、注册快捷键 |
| `setup_tray` | 创建托盘图标、构建右键菜单 |
| `update_tray_icon` | 绘制/更新托盘图标（完成计数） |
| `refresh_list` | 刷新待办列表，仅显示未完成项 |
| `draw_row` | 绘制单个待办卡片（○ + 文字 + ×） |
| `toggle_done` | 标记完成（done=true，不移除数据） |
| `delete_todo` | 删除待办条目 |
| `clear_done` | 清除所有已完成条目 |
| `_open_add_dialog` | 弹出添加待办输入框 |
| `_open_diary` | 打开/切换日记面板 |
| `toggle_window` | 显示/隐藏主窗口 |
| `_apply_position` | 应用窗口位置设置 |
| `_is_autostart` | 检查是否已注册开机自启 |
| `_toggle_autostart` | 切换开机自启状态 |

#### `DiaryApp`（日记面板）

| 方法 | 功能 |
|------|------|
| `__init__` | 初始化窗口、加载数据、构建 UI |
| `build_ui` | 构建搜索栏、分栏布局（列表+编辑区） |
| `new_entry` | 清空编辑区准备写新内容 |
| `save_entry` | 保存当前内容（新建或更新） |
| `on_select` | 点击列表条目，加载到编辑区 |
| `do_search` | 按关键词过滤条目 |
| `refresh_list` | 刷新左侧列表显示 |
| `load` | 从 diary.json 加载数据 |
| `save` | 保存数据到 diary.json |

---

## 自定义开发

### 修改配色

在文件顶部找到颜色常量，修改后重新运行：

```python
BG = '#0a0a12'      # 窗口透明背景色
CARD = '#16162b'     # 卡片背景色
FG = '#e8e8f0'       # 文字颜色
ACCENT = '#7c6cf0'   # 强调色（按钮、图标数字）
DIM = '#3a3a55'      # 次要文字/装饰色
```

### 修改窗口尺寸

```python
self.w = 290   # 窗口宽度
self.h = 380   # 窗口高度
```

### 修改字体

全局搜索 `SimHei` 替换为其他中文字体（如 `Microsoft YaHei UI`、`DengXian`、`PingFang SC`）。

---

## 打包发布

### 构建 exe

```bash
pip install pyinstaller
pyinstaller --onefile -w --name "openliving" todo.py
```

参数说明：

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包为单文件 |
| `-w` | 无控制台窗口（GUI 应用必需） |
| `--name` | 输出文件名 |
| `--distpath` | 指定输出目录 |
| `--workpath` | 指定工作目录 |
| `--specpath` | 指定 spec 文件目录 |

### 发布 Release

```bash
gh release create v1.0.0 "openliving.exe#OpenLiving-Windows-x64" --title "v1.0.0" --notes "更新说明"
```

---

## 常见问题

### Q: exe 报毒？

单文件 exe 打包方式可能被部分杀软误报。可自行从源码构建，或使用 `python todo.py` 直接运行。

### Q: 数据存在哪里？

exe 或 .py 所在目录下的 `data.json`（待办）和 `diary.json`（日记）。直接编辑 JSON 文件可批量修改。

### Q: 托盘图标不显示？

部分精简版 Windows 系统可能禁用了系统托盘图标。检查系统托盘设置，确保 OpenLiving 未被隐藏。

### Q: 如何完全卸载？

1. 右键托盘 → 退出
2. 取消勾选"开机自启"（或手动删除注册表 `HKCU\...\Run\openliving`）
3. 删除 `openliving.exe` 及同目录下的 `data.json`、`diary.json`

---

## 开源协议

MIT License. 详见 GitHub 仓库 [cymylive/openliving](https://github.com/cymylive/openliving)。
