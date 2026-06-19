import tkinter as tk
from tkinter import ttk
import json
import os
import sys
import threading
import winreg
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import pystray

def _base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(_base_dir(), "data.json")
DIARY_FILE = os.path.join(_base_dir(), "diary.json")
BG = '#0a0a12'
CARD = '#16162b'
FG = '#e8e8f0'
ACCENT = '#7c6cf0'
DIM = '#3a3a55'

class DiaryApp:
    def __init__(self):
        self.win = tk.Toplevel()
        self.win.title("日记灵感")
        self.win.configure(bg='#1a1a2e')
        self.win.attributes('-topmost', True)

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        w, h = 700, 500
        self.win.geometry(f"{w}x{h}+{sw//2 - w//2}+{sh//2 - h//2}")
        self.win.minsize(500, 350)

        self.entries = self.load()
        self.filtered = list(self.entries)
        self.search_var = tk.StringVar()

        self.build_ui()
        self.search_var.trace('w', lambda *a: self.do_search())
        self.refresh_list()

        self.win.protocol("WM_DELETE_WINDOW", self.win.destroy)

    def build_ui(self):
        self.win.columnconfigure(0, weight=1)
        self.win.rowconfigure(1, weight=1)

        top = tk.Frame(self.win, bg='#1a1a2e')
        top.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 4))
        top.columnconfigure(0, weight=1)

        tk.Label(top, text='日记灵感', bg='#1a1a2e', fg='#a0a0c0',
                 font=('SimHei', 13)).pack(side='left', padx=(0, 10))

        search_entry = tk.Entry(top, textvariable=self.search_var, bg='#16213e', fg=FG,
                                insertbackground=FG, font=('SimHei', 10), relief='flat', bd=4)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 4), ipady=3)
        search_entry.insert(0, '搜索...')
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, 'end') if search_entry.get() == '搜索...' else None)
        search_entry.bind('<FocusOut>', lambda e: search_entry.insert(0, '搜索...') if not search_entry.get() else None)

        tk.Button(top, text='搜索', bg='#16213e', fg=FG, bd=0,
                  font=('SimHei', 10), padx=10, pady=2, cursor='hand2',
                  activebackground='#0f3460', activeforeground='#fff',
                  command=self.do_search).pack(side='left', padx=(0, 6))

        tk.Button(top, text='新建', bg=ACCENT, fg='#fff', bd=0,
                  font=('SimHei', 10), padx=14, pady=2, cursor='hand2',
                  activebackground='#6a5cd8', activeforeground='#fff',
                  command=self.new_entry).pack(side='right')

        paned = tk.PanedWindow(self.win, bg='#1a1a2e', sashwidth=4, sashrelief='flat')
        paned.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))

        left_frame = tk.Frame(paned, bg='#14142a')
        self.listbox = tk.Listbox(left_frame, bg='#14142a', fg=FG,
                                  font=('SimHei', 10), bd=0, highlightthickness=0,
                                  selectbackground=ACCENT, selectforeground='#fff',
                                  activestyle='none')
        scroll_l = tk.Scrollbar(left_frame, orient='vertical', command=self.listbox.yview,
                                width=6, troughcolor='#14142a', bg=DIM, activebackground=ACCENT)
        self.listbox.configure(yscrollcommand=scroll_l.set)
        self.listbox.pack(side='left', fill='both', expand=True)
        scroll_l.pack(side='right', fill='y')
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        paned.add(left_frame, width=200)

        right_frame = tk.Frame(paned, bg='#0d0d1a')
        paned.add(right_frame, width=480)

        self.text_area = tk.Text(right_frame, bg='#0d0d1a', fg=FG,
                                 font=('SimHei', 11), bd=0, highlightthickness=0,
                                 insertbackground=FG, wrap='word', padx=10, pady=10)
        scroll_r = tk.Scrollbar(right_frame, orient='vertical', command=self.text_area.yview,
                                width=6, troughcolor='#0d0d1a', bg=DIM, activebackground=ACCENT)
        self.text_area.configure(yscrollcommand=scroll_r.set)
        self.text_area.pack(side='left', fill='both', expand=True)
        scroll_r.pack(side='right', fill='y')
        self.text_area.insert('1.0', '选择左侧条目查看，或点击"新建"写新内容')

        bottom = tk.Frame(self.win, bg='#1a1a2e')
        bottom.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 8))

        self.save_btn = tk.Button(bottom, text='保存', bg=ACCENT, fg='#fff', bd=0,
                                  font=('SimHei', 10), padx=20, pady=3, cursor='hand2',
                                  activebackground='#6a5cd8', activeforeground='#fff',
                                  command=self.save_entry)
        self.save_btn.pack(side='right')
        self.current_id = None

    def new_entry(self):
        self.current_id = None
        self.text_area.delete('1.0', 'end')
        self.text_area.insert('1.0', '')
        self.text_area.focus_force()
        self.listbox.selection_clear(0, 'end')

    def save_entry(self):
        text = self.text_area.get('1.0', 'end-1c').strip()
        if not text:
            return
        now = datetime.now().isoformat()
        if self.current_id is not None:
            for e in self.entries:
                if e.get('id') == self.current_id:
                    e['text'] = text
                    e['updated'] = now
                    break
        else:
            new_id = max([e.get('id', 0) for e in self.entries], default=0) + 1
            self.entries.insert(0, {'id': new_id, 'text': text, 'created': now, 'updated': now})
        self.save()
        self.do_search()
        for i, e in enumerate(self.filtered):
            if e.get('id') == self.current_id or (self.current_id is None and i == 0):
                self.listbox.selection_set(i)
                self.listbox.see(i)
                break

    def on_select(self, e):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.filtered):
            entry = self.filtered[idx]
            self.current_id = entry.get('id')
            self.text_area.delete('1.0', 'end')
            self.text_area.insert('1.0', entry['text'])
            self.save_btn.configure(text='保存')

    def do_search(self):
        q = self.search_var.get().strip().lower()
        if q == '搜索...' or not q:
            self.filtered = list(self.entries)
        else:
            self.filtered = [e for e in self.entries if q in e['text'].lower()]
        self.refresh_list()

    def refresh_list(self):
        self.listbox.delete(0, 'end')
        for e in self.filtered:
            try:
                dt = datetime.fromisoformat(e['created'])
                date_str = dt.strftime('%m-%d %H:%M')
            except:
                date_str = ''
            first_line = e['text'].split('\n')[0][:30]
            display = f"{date_str}  {first_line}" if date_str else first_line
            self.listbox.insert('end', display)

    def load(self):
        if os.path.exists(DIARY_FILE):
            try:
                with open(DIARY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save(self):
        os.makedirs(os.path.dirname(DIARY_FILE) or '.', exist_ok=True)
        with open(DIARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenLiving")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', BG)
        self.root.attributes('-alpha', 0.70)
        self.root.configure(bg=BG)

        self.w = 290
        self.h = 380
        sw = root.winfo_screenwidth()
        self.root.geometry(f"{self.w}x{self.h}+{sw - self.w - 18}+70")

        self.position = 'top-right'
        self.todos = self.load_todos()
        self.drag_x = 0
        self.drag_y = 0
        self.build_ui()
        self.setup_tray()

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        drag_bar = tk.Frame(self.root, bg=BG, height=24, cursor='fleur')
        drag_bar.grid(row=0, column=0, sticky='ew')
        drag_bar.bind('<Button-1>', self.start_drag)
        drag_bar.bind('<B1-Motion>', self.do_drag)
        drag_bar.grid_propagate(False)

        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky='nsew', padx=8, pady=(0, 8))

        self.list_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas.create_window((0, 0), window=self.list_frame, anchor='nw', tags='inner')
        self.list_frame.bind('<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))

        self.refresh_list()

        self.root.bind('<Escape>', lambda e: self.hide_window())
        self.root.bind('<Control-q>', lambda e: self.quit_app())
        self.root.bind('<Control-Q>', lambda e: self.quit_app())

    def setup_tray(self):
        self.update_tray_icon()
        self.tray_icon = pystray.Icon("openliving", self._tray_img, "OpenLiving",
            menu=pystray.Menu(
                pystray.MenuItem("添加待办", self.show_add_dialog),
                pystray.MenuItem("日记灵感", self.open_diary),
                pystray.MenuItem("显示位置",
                    pystray.Menu(
                        pystray.MenuItem("左上角", self.set_pos_tl),
                        pystray.MenuItem("右上角", self.set_pos_tr, checked=lambda item: self.position=='top-right'),
                        pystray.MenuItem("左下角", self.set_pos_bl),
                        pystray.MenuItem("右下角", self.set_pos_br),
                    )),
                pystray.MenuItem("清除已完成", self.clear_done),
                pystray.MenuItem("开机自启", self.toggle_autostart, checked=lambda item: self._is_autostart()),
                pystray.MenuItem("显示/隐藏", self.toggle_window, default=True),
                pystray.MenuItem("退出", self.quit_app)
            ))
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def open_diary(self, icon=None, item=None):
        self.root.after(0, self._open_diary)

    def _open_diary(self):
        if hasattr(self, '_diary_win') and self._diary_win is not None:
            try:
                self._diary_win.win.lift()
                self._diary_win.win.focus_force()
                return
            except:
                pass
        self._diary_win = DiaryApp()

    def update_tray_icon(self):
        done = sum(1 for t in self.todos if t['done'])
        s = 32
        img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([2, 2, s-2, s-2], radius=6, fill='#14141e')
        if done > 0:
            try:
                font = ImageFont.truetype("simhei.ttf", 16)
            except:
                font = ImageFont.load_default()
            text = str(done) if done < 100 else '99+'
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
            draw.text(((s-tw)//2, (s-th)//2-1), text, fill=ACCENT, font=font)
        else:
            draw.rectangle([8, 9, 24, 11], fill=ACCENT)
            draw.rectangle([8, 15, 20, 17], fill='#555')
            draw.rectangle([8, 21, 22, 23], fill='#555')
        self._tray_img = img
        try:
            self.tray_icon.icon = img
        except:
            pass

    def clear_done(self, icon=None, item=None):
        self.root.after(0, self._clear_done)

    def _clear_done(self):
        self.todos = [t for t in self.todos if not t['done']]
        self.save_todos()
        self.refresh_list()

    def show_add_dialog(self, icon=None, item=None):
        self.root.after(0, self._open_add_dialog)

    def _open_add_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("添加待办")
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.configure(bg='#1a1a2e')

        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        dw, dh = 340, 130
        win.geometry(f"{dw}x{dh}+{sw//2 - dw//2}+{sh//2 - dh//2}")

        win.columnconfigure(0, weight=1)

        tk.Label(win, text='新建待办事项', bg='#1a1a2e', fg='#a0a0c0',
                 font=('SimHei', 11)).grid(row=0, column=0, pady=(14, 0))

        var = tk.StringVar()
        entry = tk.Entry(win, textvariable=var, bg='#16213e', fg=FG, bd=0,
                         insertbackground=FG, font=('SimHei', 13),
                         relief='flat', highlightthickness=0)
        entry.grid(row=1, column=0, sticky='ew', padx=20, pady=(10, 6), ipady=6)
        entry.focus_force()

        btn_frame = tk.Frame(win, bg='#1a1a2e')
        btn_frame.grid(row=2, column=0, pady=(0, 12))

        def submit():
            text = var.get().strip()
            if text:
                self.todos.append({'text': text, 'done': False, 'created': datetime.now().isoformat()})
                self.save_todos()
                self.refresh_list()
                self.root.deiconify()
                self.root.lift()
            win.destroy()

        def on_key(e):
            if e.keysym == 'Return':
                submit()
            elif e.keysym == 'Escape':
                win.destroy()

        entry.bind('<KeyRelease>', on_key)

        tk.Button(btn_frame, text='取消', bg='#16213e', fg='#888', bd=0,
                  font=('SimHei', 10), padx=18, pady=4, cursor='hand2',
                  activebackground='#0f3460', activeforeground='#fff',
                  command=win.destroy).pack(side='left', padx=6)

        tk.Button(btn_frame, text='添加', bg=ACCENT, fg='#fff', bd=0,
                  font=('SimHei', 10), padx=22, pady=4, cursor='hand2',
                  activebackground='#6a5cd8', activeforeground='#fff',
                  command=submit).pack(side='left', padx=6)

    def toggle_window(self, icon=None, item=None):
        self.root.after(0, self._toggle_window)

    def _toggle_window(self):
        if self.root.state() == 'withdrawn' or not self.root.winfo_viewable():
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        else:
            self.root.withdraw()

    def hide_window(self):
        self.root.withdraw()

    def quit_app(self):
        self.tray_icon.stop()
        self.root.destroy()

    def _app_path(self):
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(__file__)

    def _is_autostart(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, "openliving")
            winreg.CloseKey(key)
            return os.path.exists(val)
        except:
            return False

    def toggle_autostart(self, icon=None, item=None):
        self.root.after(0, self._toggle_autostart)

    def _toggle_autostart(self):
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if self._is_autostart():
            winreg.DeleteValue(key, "openliving")
        else:
            winreg.SetValueEx(key, "openliving", 0, winreg.REG_SZ, self._app_path())
        winreg.CloseKey(key)

    def set_position(self, pos):
        self.position = pos
        self.root.after(0, self._apply_position)

    def set_pos_tl(self, icon, item):
        self.set_position('top-left')
    def set_pos_tr(self, icon, item):
        self.set_position('top-right')
    def set_pos_bl(self, icon, item):
        self.set_position('bottom-left')
    def set_pos_br(self, icon, item):
        self.set_position('bottom-right')

    def _apply_position(self):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin = 18
        if self.position == 'top-left':
            x, y = margin, 70
        elif self.position == 'top-right':
            x, y = sw - self.w - margin, 70
        elif self.position == 'bottom-left':
            x, y = margin, sh - self.h - 60
        elif self.position == 'bottom-right':
            x, y = sw - self.w - margin, sh - self.h - 60
        self.root.geometry(f"+{x}+{y}")

    def start_drag(self, e):
        self.drag_x = e.x_root - self.root.winfo_x()
        self.drag_y = e.y_root - self.root.winfo_y()

    def do_drag(self, e):
        self.root.geometry(f"+{e.x_root - self.drag_x}+{e.y_root - self.drag_y}")

    def toggle_done(self, idx):
        self.todos[idx]['done'] = True
        self.save_todos()
        self.refresh_list()

    def delete_todo(self, idx):
        self.todos.pop(idx)
        self.save_todos()
        self.refresh_list()

    def refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        active = [t for t in self.todos if not t['done']]
        if not active:
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            self.update_tray_icon()
            return

        for vis_idx, actual_idx in enumerate([i for i, t in enumerate(self.todos) if not t['done']]):
            self.draw_row(vis_idx, actual_idx)

        self.list_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.root.update_idletasks()
        self.update_tray_icon()

    def draw_row(self, vis_idx, real_idx):
        todo = self.todos[real_idx]
        card = tk.Frame(self.list_frame, bg=CARD)
        card.pack(fill='x', pady=5)

        row = tk.Frame(card, bg=CARD)
        row.pack(fill='x', padx=6, pady=6)

        cb = tk.Label(row, text=' ○ ', bg=CARD, fg=DIM,
                      font=('Arial', 20), cursor='hand2')
        cb.pack(side='left')
        cb.bind('<Button-1>', lambda e, idx=real_idx: self.toggle_done(idx))

        lbl = tk.Label(row, text=todo['text'], bg=CARD, fg=FG, cursor='hand2',
                       font=('SimHei', 13), anchor='w')
        lbl.pack(side='left', fill='x', expand=True, padx=4, ipady=2)
        lbl.bind('<Button-1>', lambda e, idx=real_idx: self.toggle_done(idx))

        dl = tk.Label(row, text=' × ', bg=CARD, fg=DIM,
                      font=('Arial', 15), cursor='hand2')
        dl.pack(side='right')
        dl.bind('<Button-1>', lambda e, idx=real_idx: self.delete_todo(idx))
        dl.bind('<Enter>', lambda e: dl.configure(fg='#ff6b6b'))
        dl.bind('<Leave>', lambda e: dl.configure(fg=DIM))

    def load_todos(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_todos(self):
        os.makedirs(os.path.dirname(DATA_FILE) or '.', exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.todos, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    root = tk.Tk()
    app = TodoApp(root)
    root.protocol("WM_DELETE_WINDOW", root.withdraw)
    root.mainloop()
