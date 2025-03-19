import tkinter as tk
from tkinter import ttk, filedialog
import os
import glob
from typing import Callable, Optional
from tkinterdnd2 import DND_FILES

class FilePathEntry(ttk.Frame):
    """파일/폴더 경로 입력 위젯"""
    
    def __init__(self, parent, title="", browse_command=None, on_path_change=None,
                 allow_directory=True, clear_command=None, show_full_path=False, on_drop=None):
        """
        파일 경로 입력 위젯을 초기화합니다.
        
        Args:
            parent: 부모 위젯
            title: 제목 텍스트
            browse_command: 찾아보기 버튼 클릭 시 실행할 함수
            on_path_change: 경로 변경 시 실행할 함수
            allow_directory: 디렉토리 선택 허용 여부
            clear_command: 초기화 버튼 클릭 시 실행할 함수
            show_full_path: 전체 경로 표시 여부
            on_drop: 파일/폴더 드롭 시 실행할 함수
        """
        super().__init__(parent)
        self.browse_command = browse_command
        self.on_path_change = on_path_change
        self.allow_directory = allow_directory
        self.clear_command = clear_command
        self.show_full_path = show_full_path
        self.on_drop = on_drop  # 드롭 이벤트 콜백
        self.is_drag_over = False
        self.path = ""  # 실제 전체 경로
        self.is_directory = False  # 디렉토리 여부
        self.has_warning = False  # 경고 표시 여부
        
        # 스타일 설정
        style = ttk.Style()
        style.configure("DropFrame.TFrame", borderwidth=1, relief="solid")
        style.configure("WarningFrame.TFrame", borderwidth=2, relief="solid")
        
        # 제목 표시
        if title:
            self.title_label = ttk.Label(self, text=title)
            self.title_label.pack(anchor="w", pady=(0, 5))
        
        # 경로 표시 프레임 (드롭 영역)
        self.drop_frame = ttk.Frame(self, style="DropFrame.TFrame")
        self.drop_frame.pack(fill="x", pady=(0, 5))
        
        # 중앙 정렬을 위한 하위 프레임
        self.drop_content = ttk.Frame(self.drop_frame)
        self.drop_content.place(relx=0.5, rely=0.5, anchor="center")
        
        # 초기 안내 메시지
        self.placeholder_label = ttk.Label(
            self.drop_content, 
            text="파일 또는 폴더를 여기에 끌어다 놓으세요",
            foreground="gray"
        )
        self.placeholder_label.pack(pady=10)
        
        # 경로 정보 표시 영역 - 처음에는 숨김
        self.info_frame = ttk.Frame(self.drop_frame)
        
        # 파일/폴더 이름 레이블
        self.name_var = tk.StringVar()
        name_style = ttk.Style()
        name_style.configure("PathName.TLabel", font=("", 10, "bold"))
        self.name_label = ttk.Label(
            self.info_frame, 
            textvariable=self.name_var,
            style="PathName.TLabel"
        )
        self.name_label.pack(pady=(5, 2))
        
        # 경로 또는 추가 정보 레이블
        self.info_var = tk.StringVar()
        self.info_label = ttk.Label(
            self.info_frame, 
            textvariable=self.info_var,
            foreground="gray"
        )
        self.info_label.pack(pady=(0, 2))
        
        # 경로 표시 레이블 (작은 글씨로 항상 표시)
        self.path_var = tk.StringVar()
        path_style = ttk.Style()
        path_style.configure("SmallPath.TLabel", font=("", 7), foreground="gray")
        self.path_label = ttk.Label(
            self.info_frame, 
            textvariable=self.path_var,
            style="SmallPath.TLabel",
            wraplength=350  # 긴 경로를 여러 줄로 표시
        )
        self.path_label.pack(pady=(0, 5))
        
        # 경고 레이블 (파일이 이미 존재할 때 표시)
        warning_style = ttk.Style()
        warning_style.configure("Warning.TLabel", foreground="#CC3300", font=("", 7, "bold"))
        self.warning_var = tk.StringVar()
        self.warning_label = ttk.Label(
            self.info_frame,
            textvariable=self.warning_var,
            style="Warning.TLabel"
        )
        self.warning_label.pack(pady=(0, 5))
        self.warning_label.pack_forget()  # 초기에는 숨김
        
        # 버튼 프레임
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=(5, 0))
        
        # 찾아보기 버튼
        self.browse_button = ttk.Button(
            button_frame, 
            text="찾아보기", 
            command=self._browse_command
        )
        self.browse_button.pack(side="left", padx=(0, 5))
        
        # 초기화 버튼
        self.clear_button = ttk.Button(
            button_frame, 
            text="초기화", 
            command=self._clear_command
        )
        self.clear_button.pack(side="left")
        
        # 드래그 앤 드롭 설정
        self._setup_drag_drop()
        
        # 최소 높이 설정 (폴더 정보를 표시할 영역 확보)
        self.drop_frame.update_idletasks()  # 실제 크기 업데이트
        self.drop_frame.configure(height=80 if not show_full_path else 100)
        
    def _setup_drag_drop(self):
        """드래그 앤 드롭 기능을 설정합니다."""
        # 드롭 대상으로 설정
        self.drop_frame.drop_target_register(DND_FILES)
        
        # 드래그 관련 이벤트 바인딩
        self.drop_frame.dnd_bind("<<DragEnter>>", self._on_drop_enter)
        self.drop_frame.dnd_bind("<<DragLeave>>", self._on_drop_leave)
        self.drop_frame.dnd_bind("<<Drop>>", self._on_drop)
        
    def _on_drop_enter(self, event):
        """드래그된 항목이 위젯 위에 들어올 때 호출됩니다."""
        self.is_drag_over = True
        self.drop_frame.configure(borderwidth=2)
        
    def _on_drop_leave(self, event):
        """드래그된 항목이 위젯을 벗어날 때 호출됩니다."""
        self.is_drag_over = False
        self.drop_frame.configure(borderwidth=1)
        
    def _on_drop(self, event):
        """항목이 드롭되었을 때 호출됩니다."""
        self.is_drag_over = False
        self.drop_frame.configure(borderwidth=1)
        
        # 드롭된 파일 경로 처리
        file_path = event.data
        
        # Windows에서는 중괄호로 묶인 경로가 올 수 있음
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
            
        # 드롭 콜백이 있으면 콜백 함수 호출
        if self.on_drop:
            self.on_drop(file_path)
        else:
            # 기본 처리: 경로 설정
            self.set_path(file_path)
        
    def _browse_command(self):
        """찾아보기 버튼 클릭 시 호출됩니다."""
        if self.browse_command:
            self.browse_command()
            
    def _clear_command(self):
        """초기화 버튼 클릭 시 호출됩니다."""
        self.clear_path()
        if self.clear_command:
            self.clear_command()
            
    def set_path(self, path: str):
        """경로를 설정하고 UI를 업데이트합니다."""
        if not path:
            self.clear_path()
            return
            
        self.path = path
        self.is_directory = os.path.isdir(path)
        
        # UI 업데이트
        self._update_display()
        
        # 콜백 호출
        if self.on_path_change:
            self.on_path_change(path)
            
    def _update_display(self):
        """경로 정보 표시를 업데이트합니다."""
        if not self.path:
            # 경로가 없는 경우 초기 상태로
            self.info_frame.place_forget()
            self.placeholder_label.pack(pady=10)
            self.has_warning = False
            self.warning_label.pack_forget()
            self.drop_frame.configure(style="DropFrame.TFrame")
            return
            
        # 항상 전체 경로 표시 (작은 글씨로)
        self.path_var.set(self.path)
            
        # 파일 또는 폴더에 따라 표시 내용 결정
        if self.is_directory:
            # 폴더인 경우
            folder_name = os.path.basename(self.path)
            self.name_var.set(folder_name)
            
            # 폴더 내 이미지 파일 수 계산
            image_extensions = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".bmp", ".hdr", ".tga")
            image_files = []
            for ext in image_extensions:
                # 대소문자 구분 없이 검색 (각 확장자의 대소문자 버전을 모두 추가하되, 중복 제거)
                lower_pattern = os.path.join(self.path, f"*{ext}")
                upper_pattern = os.path.join(self.path, f"*{ext.upper()}")
                
                # 중복을 방지하기 위해 set 사용
                files = set(glob.glob(lower_pattern)).union(set(glob.glob(upper_pattern)))
                image_files.extend(files)
            
            num_images = len(image_files)
            
            # 폴더 정보 표시
            self.info_var.set(f"이미지 파일 {num_images}개")
            
            # 폴더는 경고 표시 안함
            self.has_warning = False
            self.warning_label.pack_forget()
            self.drop_frame.configure(style="DropFrame.TFrame")
        else:
            # 파일인 경우
            file_name = os.path.basename(self.path)
            self.name_var.set(file_name)
            
            # 파일 크기 계산
            try:
                file_size = os.path.getsize(self.path)
                size_str = self._format_file_size(file_size)
                
                # 파일 정보 표시
                self.info_var.set(size_str)
            except Exception:
                self.info_var.set("파일 정보를 읽을 수 없습니다")
                
        # 플레이스홀더 숨기고 정보 표시
        self.placeholder_label.pack_forget()
        self.info_frame.place(relx=0.5, rely=0.5, anchor="center")
        
    def _format_file_size(self, size_bytes):
        """파일 크기를 읽기 쉬운 형식으로 변환합니다."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        
    def get_path(self) -> str:
        """현재 설정된 경로를 반환합니다."""
        return self.path
        
    def clear_path(self):
        """경로를 초기화합니다."""
        self.path = ""
        self.is_directory = False
        self._update_display()
        
    def is_directory_path(self) -> bool:
        """현재 설정된 경로가 디렉토리인지 여부를 반환합니다."""
        return self.is_directory

    def set_existing_file_warning(self, show: bool):
        """
        파일이 이미 존재할 때 경고 메시지를 표시/숨깁니다.
        
        Args:
            show: 경고 표시 여부
        """
        self.has_warning = show
        
        if show:
            self.warning_var.set("⚠️ 이 파일은 이미 존재합니다. 변환 시 덮어쓰기됩니다.")
            self.warning_label.pack(pady=(0, 5))
            # 경고 스타일 적용 (빨간색 테두리)
            self.drop_frame.configure(style="WarningFrame.TFrame")
        else:
            self.warning_label.pack_forget()
            # 기본 스타일로 복원
            self.drop_frame.configure(style="DropFrame.TFrame") 