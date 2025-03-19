import tkinter as tk
from tkinter import ttk
import os
from typing import Callable, Optional
from tkinterdnd2 import DND_FILES

class FilePathEntry(ttk.Frame):
    def __init__(self, parent, title: str, browse_command: Callable, 
                 on_path_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.title = title
        self.browse_command = browse_command
        self.on_path_change = on_path_change
        
        self._setup_ui()
        self._setup_drag_drop()
        
    def _setup_ui(self):
        """UI 요소들을 설정합니다."""
        # 제목 프레임
        title_frame = ttk.LabelFrame(self, text=self.title, padding="10")
        title_frame.pack(fill="x", expand=True)
        
        # 경로 입력 프레임
        path_frame = ttk.Frame(title_frame)
        path_frame.pack(fill="x", expand=True)
        
        # 경로 입력 필드
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 경로 변경 이벤트 바인딩
        self.path_var.trace_add("write", self._on_path_change)
        
        # 찾아보기 버튼
        browse_button = ttk.Button(path_frame, text="찾아보기", command=self.browse_command)
        browse_button.pack(side="right")
        
    def _setup_drag_drop(self):
        """드래그 앤 드롭 기능을 설정합니다."""
        self.path_entry.drop_target_register(DND_FILES)
        self.path_entry.dnd_bind('<<Drop>>', self._on_drop)
        
    def _on_drop(self, event):
        """파일이 드래그되었을 때 호출됩니다."""
        file_path = event.data
        # 드래그 앤 드롭으로 받은 경로에서 따옴표 제거
        file_path = file_path.strip('{}')
        self.set_path(file_path)
        
    def _on_path_change(self, *args):
        """경로가 변경되었을 때 호출됩니다."""
        if self.on_path_change:
            self.on_path_change(self.get_path())
            
    def get_path(self) -> str:
        """현재 입력된 경로를 반환합니다."""
        return self.path_var.get()
        
    def set_path(self, path: str):
        """경로를 설정합니다."""
        self.path_var.set(path)
        
    def clear(self):
        """경로를 초기화합니다."""
        self.path_var.set("") 