import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from ..converter import ImageConverter
from ..services.log_service import LogService
from ..config.config_manager import ConfigManager
from .widgets.file_path_entry import FilePathEntry
from .widgets.image_info_display import ImageInfoDisplay
from tkinterdnd2 import DND_FILES, TkinterDnD

class AppWindow:
    def __init__(self):
        self.window = None
        self.converter = ImageConverter()
        self.logger = LogService()
        self.config = ConfigManager()
        self.logger.info("UI 초기화")
        
    def create_window(self):
        """메인 윈도우를 생성합니다."""
        self.window = TkinterDnD.Tk()  # TkinterDnD 사용
        self.window.title("이미지 포맷 변환기")
        
        # 저장된 윈도우 크기 불러오기
        window_size = self.config.get("window_size", {"width": 600, "height": 400})
        self.window.geometry(f"{window_size['width']}x{window_size['height']}")
        
        # 윈도우 크기 변경 이벤트 바인딩
        self.window.bind('<Configure>', self._on_window_resize)
        
        self.logger.debug("메인 윈도우 생성 완료")
        
    def _on_window_resize(self, event):
        """윈도우 크기가 변경될 때 호출됩니다."""
        if event.widget == self.window:
            self.config.set("window_size", {
                "width": event.width,
                "height": event.height
            })
        
    def setup_ui(self):
        """UI 요소들을 설정합니다."""
        self.logger.debug("UI 설정 시작")
        
        # 입력 파일 선택
        self.input_entry = FilePathEntry(
            self.window,
            title="입력 파일",
            browse_command=self.select_input_file,
            on_path_change=self._on_input_path_change
        )
        self.input_entry.pack(fill="x", padx=10, pady=5)
        
        # 출력 포맷 선택
        format_frame = ttk.LabelFrame(self.window, text="출력 포맷", padding="10")
        format_frame.pack(fill="x", padx=10, pady=5)
        
        self.format_var = tk.StringVar()
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var)
        format_combo['values'] = self.converter.get_supported_formats()
        
        # 저장된 출력 포맷 불러오기
        last_format = self.config.get("last_output_format")
        if last_format and last_format in format_combo['values']:
            self.format_var.set(last_format)
            
        format_combo.pack(fill="x", expand=True)
        
        # 출력 경로 선택
        self.output_entry = FilePathEntry(
            self.window,
            title="출력 경로",
            browse_command=self.select_output_path,
            on_path_change=self._on_output_path_change
        )
        self.output_entry.pack(fill="x", padx=10, pady=5)
        
        # 이미지 정보 표시
        self.info_display = ImageInfoDisplay(self.window)
        self.info_display.pack(fill="x", padx=10, pady=5)
        
        # 변환 버튼
        convert_button = ttk.Button(self.window, text="변환 시작", command=self.convert_image)
        convert_button.pack(pady=10)
        
        # 상태 표시줄
        self.status_var = tk.StringVar()
        self.status_var.set("준비")
        status_label = ttk.Label(self.window, textvariable=self.status_var)
        status_label.pack(fill="x", padx=10, pady=5)
        
        self.logger.debug("UI 설정 완료")
        
    def _on_input_path_change(self, path: str):
        """입력 경로가 변경되었을 때 호출됩니다."""
        if path and os.path.exists(path):
            self.update_image_info(path)
            
    def _on_output_path_change(self, path: str):
        """출력 경로가 변경되었을 때 호출됩니다."""
        if path:
            self.config.set("last_output_directory", os.path.dirname(path))
        
    def select_input_file(self):
        """입력 파일을 선택합니다."""
        self.logger.debug("입력 파일 선택 다이얼로그 표시")
        
        # 저장된 마지막 디렉토리 불러오기
        last_dir = self.config.get("last_input_directory")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~")
            
        file_path = filedialog.askopenfilename(
            title="입력 이미지 선택",
            initialdir=last_dir,
            filetypes=[("이미지 파일", "*.png *.jpg *.jpeg *.tif *.tiff *.exr *.bmp *.hdr")]
        )
        if file_path:
            self.input_entry.set_path(file_path)
            
            # 입력 디렉토리 저장
            self.config.set("last_input_directory", os.path.dirname(file_path))
            
            # 입력 파일 포맷 저장
            input_ext = os.path.splitext(file_path)[1].upper()
            for format_name, ext in self.converter.supported_formats.items():
                if ext.upper() == input_ext:
                    self.config.set("last_input_format", format_name)
                    break
            
            self.update_image_info(file_path)
            
    def select_output_path(self):
        """출력 경로를 선택합니다."""
        input_path = self.input_entry.get_path()
        if not input_path:
            self.logger.warning("입력 파일이 선택되지 않은 상태에서 출력 경로 선택 시도")
            messagebox.showerror("오류", "먼저 입력 파일을 선택해주세요.")
            return
            
        if not self.format_var.get():
            self.logger.warning("출력 포맷이 선택되지 않은 상태에서 출력 경로 선택 시도")
            messagebox.showerror("오류", "출력 포맷을 선택해주세요.")
            return
            
        self.logger.debug("출력 경로 선택 다이얼로그 표시")
        
        # 저장된 마지막 디렉토리 불러오기
        last_dir = self.config.get("last_output_directory")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.dirname(input_path)
            
        default_name = os.path.splitext(os.path.basename(input_path))[0]
        default_ext = self.converter.supported_formats[self.format_var.get()]
        file_path = filedialog.asksaveasfilename(
            title="저장 위치 선택",
            initialdir=last_dir,
            defaultextension=default_ext,
            initialfile=f"{default_name}{default_ext}"
        )
        if file_path:
            self.output_entry.set_path(file_path)
            
            # 출력 디렉토리와 포맷 저장
            self.config.set("last_output_directory", os.path.dirname(file_path))
            self.config.set("last_output_format", self.format_var.get())
            
    def update_image_info(self, image_path: str):
        """이미지 정보를 업데이트합니다."""
        self.logger.debug(f"이미지 정보 업데이트: {image_path}")
        info = self.converter.get_image_info(image_path)
        self.info_display.update_info(info)
        
    def convert_image(self):
        """이미지 변환을 실행합니다."""
        input_path = self.input_entry.get_path()
        output_path = self.output_entry.get_path()
        
        if not input_path or not output_path:
            self.logger.warning("입력 파일 또는 출력 경로가 선택되지 않은 상태에서 변환 시도")
            messagebox.showerror("오류", "입력 파일과 출력 경로를 모두 선택해주세요.")
            return
            
        self.logger.info(f"이미지 변환 시작: {input_path} -> {output_path}")
        self.status_var.set("변환 중...")
        self.window.update()
        
        success, message = self.converter.convert_image(input_path, output_path)
        
        if success:
            self.logger.info("이미지 변환 성공")
            messagebox.showinfo("성공", message)
        else:
            self.logger.error(f"이미지 변환 실패: {message}")
            messagebox.showerror("오류", message)
            
        self.status_var.set("준비")
        
    def run(self):
        """애플리케이션을 실행합니다."""
        self.logger.info("애플리케이션 실행 시작")
        self.window.mainloop()
        self.logger.info("애플리케이션 종료")