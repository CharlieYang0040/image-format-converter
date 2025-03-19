import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Dict, Any
from ..converter import ImageConverter
from ..services.log_service import LogService
from ..config.config_manager import ConfigManager
from .widgets.file_path_entry import FilePathEntry
from .widgets.image_info_display import ImageInfoDisplay
from .widgets.format_options import FormatOptionsWidget
from .widgets.batch_progress import BatchProgressWidget
from src.converters.batch_service import BatchService
from tkinterdnd2 import DND_FILES, TkinterDnD
from src.color_management import ColorManager
from .widgets.conversion_progress import ConversionProgressWidget

class AppWindow:
    def __init__(self):
        self.window = None
        self.converter = ImageConverter()
        self.logger = LogService()
        self.config = ConfigManager()
        self.batch_service = BatchService()
        self.logger.info("UI 초기화")
        
    def create_window(self):
        """메인 윈도우를 생성합니다."""
        self.logger.debug("메인 윈도우 생성 시작")
        
        # 메인 윈도우 설정
        self.window = TkinterDnD.Tk()
        self.window.title("이미지 포맷 변환기")
        self.window.geometry("1024x768")
        self.window.minsize(800, 600)
        
        # 파일 드래그 앤 드롭 초기화
        self.logger.debug("드래그 앤 드롭 초기화")
        
        # 윈도우 아이콘 설정
        try:
            if os.path.exists("assets/icon.ico"):
                self.window.iconbitmap("assets/icon.ico")
                self.logger.debug("윈도우 아이콘 설정 완료")
            else:
                self.logger.warning("아이콘 파일을 찾을 수 없습니다.")
        except Exception as e:
            self.logger.error(f"아이콘 설정 중 오류 발생: {str(e)}")
        
        # 스타일 설정
        self._setup_styles()
        
        self.logger.debug("메인 윈도우 생성 완료")
        
    def _setup_styles(self):
        """애플리케이션 스타일을 설정합니다."""
        # 기본 테마 설정
        style = ttk.Style()
        
        # 프레임과 레이블 프레임 스타일 설정
        style.configure('TLabelframe', borderwidth=2)
        style.configure('TFrame', borderwidth=0)
        
        # 버튼 스타일 설정
        style.configure('Primary.TButton', font=('', 10, 'bold'))
        
        # 프로그레스바 스타일 설정
        style.configure('TProgressbar', thickness=10)
        
    def _setup_ui(self):
        """UI 요소들을 설정합니다."""
        # 메인 프레임
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 좌우 분할 (왼쪽: 변환 옵션, 오른쪽: 이미지 정보)
        main_paned = ttk.PanedWindow(main_frame, orient="horizontal")
        main_paned.pack(fill="both", expand=True)
        
        # 왼쪽 패널 (변환 옵션)
        left_panel = ttk.Frame(main_paned)
        main_paned.add(left_panel, weight=1)
        
        # 입력 경로 선택
        input_frame = ttk.LabelFrame(left_panel, text="입력", padding=10)
        input_frame.pack(fill="x", pady=(0, 5))
        self.input_entry = FilePathEntry(input_frame, on_path_change=self._on_input_path_change, 
                                         clear_command=self._on_clear_input_path)
        self.input_entry.pack(fill="x")
        
        # 입력 타입 선택 (파일/폴더)
        input_type_frame = ttk.Frame(input_frame)
        input_type_frame.pack(fill="x", pady=(5, 0))
        
        # 출력 형식 선택
        format_frame = ttk.LabelFrame(left_panel, text="출력 형식", padding=10)
        format_frame.pack(fill="x", pady=5)
        
        self.format_var = tk.StringVar()
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, state="readonly")
        format_combo.pack(fill="x")
        
        # 출력 파일 포맷 설정
        supported_formats = self.converter.get_supported_formats()
        format_combo["values"] = supported_formats
        
        if supported_formats:
            format_combo.current(0)
        
        # 포맷 변경 이벤트 핸들러
        def _on_format_change(*args):
            # 출력 경로 확장자 업데이트
            output_path = self.output_entry.get_path()
            
            if output_path and not os.path.isdir(output_path):
                # 현재 선택된 형식
                selected_format = self.format_var.get()
                
                if selected_format in self.converter.supported_formats:
                    # 새 확장자 가져오기
                    new_ext = self.converter.supported_formats[selected_format]
                    
                    # 기존 파일명에서 확장자 제외한 부분
                    base_path = os.path.splitext(output_path)[0]
                    
                    # 새 경로 설정
                    new_path = f"{base_path}{new_ext}"
                    self.output_entry.set_path(new_path)
            
            # 포맷에 따른 옵션 업데이트
            self._update_format_options(self.input_entry.get_path())
        
        self.format_var.trace_add("write", _on_format_change)
        
        # 출력 경로 선택
        output_frame = ttk.LabelFrame(left_panel, text="출력", padding=10)
        output_frame.pack(fill="x", pady=(0, 5))
        self.output_entry = FilePathEntry(output_frame, on_path_change=self._on_output_path_change, 
                                          clear_command=self._on_clear_output_path, 
                                          on_drop=self._on_output_path_drop)
        self.output_entry.pack(fill="x")
        
        # 변환 옵션 프레임
        self.format_options = FormatOptionsWidget(left_panel)
        self.format_options.pack(fill="x", pady=(5, 0))
        
        # 변환 작업 모드 관리 (단일 파일/배치)
        self.work_mode_var = tk.StringVar(value="single")  # 'single' 또는 'batch'
        
        # 진행 상태 프레임 (단일 파일용)
        self.single_progress_container = ttk.Frame(left_panel)
        self.single_progress_container.pack(fill="x", pady=(10, 0))
        
        # 상세 변환 진행 상태 위젯
        self.conversion_progress = ConversionProgressWidget(self.single_progress_container)
        self.conversion_progress.pack(fill="x", expand=True)
        
        # 작업 버튼 프레임
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 변환 버튼
        self.convert_button = ttk.Button(button_frame, text="변환 시작", command=self.convert_image)
        self.convert_button.pack(side="right", padx=(5, 0))
        
        # 배치 처리 진행 상태 위젯 (초기에는 숨김)
        self.batch_progress = BatchProgressWidget(left_panel)
        self.batch_progress.pack(fill="x", expand=True, pady=(10, 0))
        self.batch_progress.pack_forget()
        self.batch_progress.set_cancel_callback(self._cancel_batch_conversion)
        
        # 오른쪽 패널 (이미지 정보)
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=1)
        
        # 이미지 미리보기 및 정보
        preview_frame = ttk.LabelFrame(right_panel, text="이미지 정보", padding=10)
        preview_frame.pack(fill="both", expand=True)
        
        # 이미지 정보 표시
        self.info_display = ImageInfoDisplay(preview_frame)
        self.info_display.pack(fill="both", expand=True)
        
        # 초기 UI 상태 업데이트
        self._update_ui_state()
        
    def _switch_to_mode(self, mode: str):
        """작업 모드를 전환합니다 (단일 파일 또는 배치)"""
        if mode == "single":
            # 단일 파일 모드
            self.work_mode_var.set("single")
            self.batch_progress.pack_forget()
            self.single_progress_container.pack(fill="x", pady=(10, 0))
        else:
            # 배치 모드
            self.work_mode_var.set("batch")
            self.single_progress_container.pack_forget()
            self.batch_progress.pack(fill="x", expand=True, pady=(10, 0))
            
    def _update_ui_state(self):
        """입력 경로 변경에 따라 UI 상태를 업데이트합니다."""
        input_path = self.input_entry.get_path()
        
        if not input_path:
            # 입력 경로가 없음
            self.convert_button.configure(state="disabled")
        else:
            # 입력 경로 유효성 확인
            if os.path.exists(input_path):
                self.convert_button.configure(state="normal")
                
                # 경로 유형에 따른 UI 모드 전환
                is_dir = os.path.isdir(input_path)
                if is_dir:
                    self._switch_to_mode("batch")
                else:
                    self._switch_to_mode("single")
            else:
                self.convert_button.configure(state="disabled")
        
    def _on_input_path_change(self, path: str):
        """입력 경로가 변경되었을 때 호출됩니다."""
        if not path:
            return
            
        if os.path.exists(path):
            # 경로 유형에 따라 UI 상태 변경
            if os.path.isdir(path):
                # 디렉토리인 경우
                self._switch_to_mode("batch")
                self.config.set("last_input_directory", path)
            else:
                # 파일인 경우
                self._switch_to_mode("single")
                self.config.set("last_input_file", path)
                self.config.set("last_input_directory", os.path.dirname(path))
                
                # 이미지 정보 업데이트 및 포맷 옵션 설정
                self.update_image_info(path)
                self._update_format_options(path)
                
            # 입력 경로가 변경되면 출력 경로의 덮어쓰기 경고 상태도 확인
            self._check_output_path_exists()
            
    def _check_output_path_exists(self):
        """출력 경로의 파일 존재 여부를 확인하고 경고를 표시합니다."""
        output_path = self.output_entry.get_path()
        if output_path and os.path.exists(output_path) and not os.path.isdir(output_path):
            self.output_entry.set_existing_file_warning(True)
        else:
            self.output_entry.set_existing_file_warning(False)
        
    def _on_output_path_change(self, path: str):
        """출력 경로가 변경되었을 때 호출됩니다."""
        if not path:
            return
            
        # 경로 유형에 따라 설정 저장
        if os.path.isdir(path):
            self.config.set("last_output_directory", path)
        else:
            # 파일이 이미 존재하는지 확인
            if os.path.exists(path) and not os.path.isdir(path):
                self.logger.debug(f"출력 파일이 이미 존재함: {path}")
                self.output_entry.set_existing_file_warning(True)
            else:
                self.output_entry.set_existing_file_warning(False)
            
            self.config.set("last_output_file", path)
            self.config.set("last_output_directory", os.path.dirname(path))
            
    def _on_clear_input_path(self):
        """입력 경로 초기화 시 호출됩니다."""
        self.info_display.clear()
        
    def _on_clear_output_path(self):
        """출력 경로 초기화 시 호출됩니다."""
        pass
        
    def select_input_path(self):
        """입력 경로를 선택합니다."""
        self.logger.debug("입력 경로 선택 다이얼로그 표시")
        
        # 저장된 마지막 디렉토리 불러오기
        last_dir = self.config.get("last_input_directory")
        if not last_dir or not os.path.exists(last_dir):
            last_dir = os.path.expanduser("~")
            
        # 파일 또는 폴더 선택을 묻는 대화상자
        choice = messagebox.askyesnocancel(
            "입력 선택", 
            "이미지 파일을 선택하시겠습니까?\n'예' - 파일 선택\n'아니오' - 폴더 선택\n'취소' - 취소",
            icon="question"
        )
        
        # 취소 버튼 클릭 시
        if choice is None:
            return
        
        if choice:
            # 파일 선택 다이얼로그
            file_path = filedialog.askopenfilename(
                title="입력 이미지 선택",
                initialdir=last_dir,
                filetypes=[("이미지 파일", "*.png *.jpg *.jpeg *.tif *.tiff *.exr *.bmp *.hdr *.tga")]
            )
            if file_path:
                self.input_entry.set_path(file_path)
        else:
            # 폴더 선택 다이얼로그
            folder_path = filedialog.askdirectory(
                title="입력 폴더 선택",
                initialdir=last_dir
            )
            if folder_path:
                self.input_entry.set_path(folder_path)
            
    def select_output_path(self):
        """출력 경로를 선택합니다."""
        input_path = self.input_entry.get_path()
        
        if not input_path:
            self.logger.warning("입력 경로가 선택되지 않은 상태에서 출력 경로 선택 시도")
            messagebox.showerror("오류", "먼저 입력 경로를 선택해주세요.")
            return
            
        if not self.format_var.get() and not self.input_entry.is_directory_path():
            self.logger.warning("출력 포맷이 선택되지 않은 상태에서 출력 경로 선택 시도")
            messagebox.showerror("오류", "출력 포맷을 선택해주세요.")
            return
            
        self.logger.debug("출력 경로 선택 다이얼로그 표시")
        
        # 저장된 마지막 디렉토리 불러오기
        last_dir = self.config.get("last_output_directory")
        if not last_dir or not os.path.exists(last_dir):
            if os.path.isdir(input_path):
                last_dir = input_path
            else:
                last_dir = os.path.dirname(input_path)
                
        if self.input_entry.is_directory_path():
            # 입력이 폴더인 경우 - 폴더 선택 다이얼로그
            folder_path = filedialog.askdirectory(
                title="출력 폴더 선택",
                initialdir=last_dir
            )
            if folder_path:
                self.output_entry.set_path(folder_path)
                
                # 폴더인 경우 덮어쓰기 경고 표시 안함
                self.output_entry.set_existing_file_warning(False)
        else:
            # 입력이 파일인 경우 - 폴더 선택 다이얼로그 (파일 저장 대화상자 대신)
            folder_path = filedialog.askdirectory(
                title="출력 폴더 선택",
                initialdir=last_dir
            )
            if folder_path:
                # 입력 파일명(확장자 제외) 추출
                input_filename = os.path.splitext(os.path.basename(input_path))[0]
                
                # 출력 파일 확장자
                output_ext = self.converter.supported_formats[self.format_var.get()]
                
                # 최종 출력 경로: 선택한 폴더 + 입력 파일명 + 확장자
                output_path = os.path.join(folder_path, f"{input_filename}{output_ext}")
                self.output_entry.set_path(output_path)
                
                # 파일 존재 여부 확인하여 경고 표시
                if os.path.exists(output_path) and not os.path.isdir(output_path):
                    self.output_entry.set_existing_file_warning(True)
                    self.logger.debug(f"출력 파일이 이미 존재함: {output_path}")
                else:
                    self.output_entry.set_existing_file_warning(False)
                
                # 출력 포맷 저장
                self.config.set("last_output_format", self.format_var.get())
            
    def update_image_info(self, image_path: str):
        """이미지 정보를 업데이트합니다."""
        self.logger.debug(f"이미지 정보 업데이트: {image_path}")
        info = self.converter.get_image_info(image_path)
        self.info_display.update_info(info)
        
    def _update_format_options(self, input_path: str):
        """포맷 옵션을 업데이트합니다."""
        if not input_path or not os.path.exists(input_path) or os.path.isdir(input_path):
            return
            
        # 입력 포맷 결정
        input_ext = os.path.splitext(input_path)[1].lower()
        input_format = None
        for format_name, ext in self.converter.supported_formats.items():
            if ext.lower() == input_ext:
                input_format = format_name
                break
                
        # 출력 포맷
        output_format = self.format_var.get()
        
        if input_format and output_format:
            # 저장된 옵션 불러오기
            saved_options = self.config.get_format_options(input_format, output_format)
            
            # 포맷 옵션 위젯 업데이트
            self.format_options.update_for_formats(input_format, output_format, saved_options)
            
            # 옵션이 있으면 표시, 없으면 숨김
            if self.format_options.options:
                self.format_options.pack(fill="x", pady=(5, 0))
            else:
                self.format_options.pack_forget()
        
    def convert_image(self):
        """이미지 변환을 실행합니다."""
        input_path = self.input_entry.get_path()
        output_path = self.output_entry.get_path()
        
        if not input_path or not output_path:
            self.logger.warning("입력 경로 또는 출력 경로가 선택되지 않은 상태에서 변환 시도")
            messagebox.showerror("오류", "입력 경로와 출력 경로를 모두 선택해주세요.")
            return
            
        # 파일 덮어쓰기 확인
        if not self.input_entry.is_directory_path() and os.path.exists(output_path) and not os.path.isdir(output_path):
            if not messagebox.askyesno("확인", f"출력 파일이 이미 존재합니다:\n{output_path}\n\n덮어쓰시겠습니까?", 
                                     icon="warning"):
                self.logger.info("사용자가 덮어쓰기를 취소함")
                return
            
        # 변환 옵션 수집
        conversion_options = {}
        if hasattr(self, 'format_options'):
            conversion_options = self.format_options.get_options()
            
            # 입력/출력 포맷이 모두 있는 경우 옵션 저장
            if not self.input_entry.is_directory_path():
                input_path = self.input_entry.get_path()
                input_ext = os.path.splitext(input_path)[1].lower()
                input_format = None
                for format_name, ext in self.converter.supported_formats.items():
                    if ext.lower() == input_ext:
                        input_format = format_name
                        break
                        
                output_format = self.format_var.get()
                
                if input_format and output_format:
                    self.config.save_format_options(input_format, output_format, conversion_options)
                    self.logger.debug(f"변환 옵션 저장: {input_format} -> {output_format}")
            
        # 입력이 폴더인지 파일인지에 따라 변환 방식 결정
        if self.input_entry.is_directory_path():
            # 배치 변환 전 폴더 내 파일 덮어쓰기 확인
            if os.path.exists(output_path) and os.path.isdir(output_path):
                # 출력 폴더가 이미 있는 경우
                output_files = [f for f in os.listdir(output_path) if os.path.isfile(os.path.join(output_path, f))]
                if output_files:
                    if not messagebox.askyesno("확인", 
                                            f"출력 폴더({output_path})에 {len(output_files)}개의 파일이 있습니다. "
                                            f"기존 파일이 덮어쓰기될 수 있습니다.\n계속하시겠습니까?", 
                                            icon="warning"):
                        self.logger.info("사용자가 배치 변환을 취소함")
                        return
                        
            self._convert_batch(input_path, output_path, conversion_options)
        else:
            self._convert_single(input_path, output_path, conversion_options)
            
    def _convert_single(self, input_path: str, output_path: str, options: Dict):
        """단일 파일 변환을 실행합니다."""
        self.logger.info(f"단일 이미지 변환 시작: {input_path} -> {output_path}")
        
        # 배치 진행 상태 숨김, 단일 파일 진행 상태 표시
        self._switch_to_mode("single")
        
        # 파일명 추출
        input_filename = os.path.basename(input_path)
        output_filename = os.path.basename(output_path)
        
        # 변환 시작 전 UI 초기화
        self.conversion_progress.reset()
        self.conversion_progress.start()
        
        # 상태 메시지 설정
        self.conversion_progress.set_status(f"변환 중... {input_filename}")
        
        try:
            # 변환기의 진행 상황 콜백 설정
            self.converter.converter.set_progress_callback(self._on_conversion_progress)
            
            # 실제 변환 실행
            success, message, debug_info = self.converter.converter.convert_image(input_path, output_path, options)
            
            # 변환 결과 처리
            if success:
                self.logger.info("이미지 변환 성공")
                self.conversion_progress.complete()
                self.conversion_progress.set_status(f"변환 완료: {input_filename} → {output_filename}")
                messagebox.showinfo("성공", message)
            else:
                error_details = ""
                if debug_info:
                    if 'oiio_error' in debug_info and debug_info['oiio_error']:
                        error_details = f"\n\n세부 오류: {debug_info['oiio_error']}"
                    elif 'error_info' in debug_info:
                        error_details = f"\n\n세부 오류: {debug_info['error_info']['message']}"
                        
                self.logger.error(f"이미지 변환 실패: {message}")
                self.conversion_progress.set_error(message)
                messagebox.showerror("오류", f"{message}{error_details}")
                
        except Exception as e:
            import traceback
            error_msg = f"예상치 못한 오류: {str(e)}"
            error_trace = traceback.format_exc()
            self.logger.error(f"{error_msg}\n{error_trace}")
            self.conversion_progress.set_error(error_msg)
            messagebox.showerror("예상치 못한 오류", f"{error_msg}\n\n자세한 내용은 로그를 확인해주세요.")
    
    def _on_conversion_progress(self, stage: int, progress: float, info: Dict):
        """변환기에서 보고하는 진행 상황을 UI에 반영합니다."""
        # 현재 단계 진행 상황 업데이트
        self.conversion_progress.update_stage(stage, progress, 
                                         info.get("message", ""), 
                                         progress >= 1.0)
        
        # 경과 시간 업데이트
        if "elapsed_time" in info:
            self.conversion_progress.set_time(info["elapsed_time"])
        
        # 오류 메시지 표시
        if "error" in info:
            self.conversion_progress.set_error(info["error"])
        
        # 전체 상태 메시지 업데이트
        if "message" in info:
            stage_name = info.get("stage_name", "")
            self.conversion_progress.set_status(f"{stage_name}: {info['message']}")
        
        # 윈도우 강제 업데이트 (UI 응답성 유지)
        self.window.update()
        
    def _convert_batch(self, input_folder: str, output_folder: str, options: Dict):
        """배치 변환을 실행합니다."""
        self.logger.info(f"배치 이미지 변환 시작: {input_folder} -> {output_folder}")
        
        # 단일 파일 진행 상태 숨김, 배치 진행 상태 표시
        self._switch_to_mode("batch")
        
        # 배치 서비스 초기화
        self.batch_service.reset()
        
        # 출력 포맷
        output_format = self.format_var.get() if self.format_var.get() else None
        
        # 작업 추가
        added_count = self.batch_service.add_folder_task(
            input_folder, output_folder, 
            output_format=output_format,
            recursive=True,
            options=options
        )
        
        if added_count == 0:
            self.logger.warning("변환할 이미지가 없습니다.")
            messagebox.showinfo("알림", "변환할 이미지가 없습니다.")
            return
            
        # 배치 위젯 초기화
        self.batch_progress.reset()
        
        # 배치 변환 시작
        success = self.batch_service.start(self._update_batch_progress)
        
        if not success:
            self.logger.warning("배치 변환 시작 실패")
            messagebox.showerror("오류", "배치 변환을 시작할 수 없습니다.")
        
    def _update_batch_progress(self, completed: int, total: int, progress_info: Dict):
        """배치 변환 진행 상황을 업데이트합니다."""
        # 배치 진행 위젯 업데이트
        self.batch_progress.update_progress(completed, total, progress_info)
        
        # 윈도우 업데이트 (UI 응답성 유지)
        self.window.update()
        
    def _cancel_batch_conversion(self):
        """배치 변환을 취소합니다."""
        if self.batch_service.is_running():
            if messagebox.askyesno("확인", "변환 작업을 취소하시겠습니까?"):
                self.batch_service.cancel()
                self.logger.info("배치 변환 작업 취소 요청")
        
    def _on_output_path_drop(self, path: str):
        """출력 경로에 파일/폴더가 드롭되었을 때 호출됩니다."""
        input_path = self.input_entry.get_path()
        
        if not input_path:
            # 입력 경로가 없으면 단순히 출력 경로만 설정
            self.output_entry.set_path(path)
            return
        
        # 입력이 파일인 경우 처리
        if not self.input_entry.is_directory_path():
            # 입력 파일명(확장자 제외) 추출
            input_filename = os.path.splitext(os.path.basename(input_path))[0]
            
            # 출력 파일 확장자 결정
            output_ext = ""
            if self.format_var.get():
                output_ext = self.converter.supported_formats[self.format_var.get()]
            
            # 드롭된 것이 파일인지 폴더인지 확인
            if os.path.isdir(path):
                # 폴더인 경우: 폴더 경로 + 입력 파일명 + 확장자
                output_path = os.path.join(path, f"{input_filename}{output_ext}")
            else:
                # 파일인 경우: 해당 파일이 위치한 폴더 경로 + 입력 파일명 + 확장자
                folder_path = os.path.dirname(path)
                output_path = os.path.join(folder_path, f"{input_filename}{output_ext}")
            
            # 출력 경로 설정
            self.output_entry.set_path(output_path)
            
            # 경로 설정 후 파일 존재 여부 확인
            self._check_output_path_exists()
        else:
            # 입력이 폴더인 경우 드롭된 경로를 그대로 사용
            self.output_entry.set_path(path)
            
            # 폴더인 경우 기존 파일 존재 여부 확인 필요 없음
            self.output_entry.set_existing_file_warning(False)
        
    def run(self):
        """애플리케이션을 실행합니다."""
        self.logger.info("애플리케이션 실행 시작")
        self.window.mainloop()
        self.logger.info("애플리케이션 종료")