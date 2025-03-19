import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

class ImageInfoDisplay(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="이미지 정보", padding="10", **kwargs)
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 요소들을 설정합니다."""
        self.info_text = tk.Text(self, height=5, wrap="word")
        self.info_text.pack(fill="x", expand=True)
        
    def update_info(self, info: Dict[str, Any]):
        """이미지 정보를 업데이트합니다."""
        if "error" in info:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"오류: {info['error']}")
            return
            
        info_text = f"크기: {info['width']}x{info['height']}\n"
        info_text += f"채널: {info['channels']}\n"
        info_text += f"포맷: {info['format']}\n"
        info_text += f"파일 크기: {info['file_size'] / 1024:.2f} KB"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
        
    def clear(self):
        """정보를 초기화합니다."""
        self.info_text.delete(1.0, tk.END) 