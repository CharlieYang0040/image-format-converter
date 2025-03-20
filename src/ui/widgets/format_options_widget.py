import tkinter as tk
from tkinter import ttk

from src.services.log_service import LogService

class FormatOptionsWidget(ttk.Frame):
    """이미지 포맷 변환 옵션을 제공하는 위젯"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.logger = LogService()
        
        # 설정 옵션 저장
        self.options = {}
        
        # 옵션 위젯 참조 저장
        self.option_widgets = {}
        
        # 색 관리 옵션 프레임
        self.color_frame = ttk.LabelFrame(self, text="색 관리")
        self.color_frame.pack(fill="x", pady=(0, 5))
        
        # 색 관리 사용 여부
        self.use_color_management = tk.BooleanVar(value=True)
        cm_check = ttk.Checkbutton(self.color_frame, text="색 관리 사용", 
                                  variable=self.use_color_management,
                                  command=self._update_color_options)
        cm_check.pack(anchor="w")
        
        # 색 프로파일 선택 프레임
        self.profile_frame = ttk.Frame(self.color_frame)
        self.profile_frame.pack(fill="x", pady=(5, 0))
        
        # 입력 프로파일
        in_profile_label = ttk.Label(self.profile_frame, text="입력 프로파일:")
        in_profile_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.input_profile_var = tk.StringVar(value="자동 감지")
        self.input_profile_combo = ttk.Combobox(self.profile_frame, 
                                              textvariable=self.input_profile_var,
                                              state="readonly", width=15)
        self.input_profile_combo.grid(row=0, column=1, sticky="ew")
        
        # 출력 프로파일
        out_profile_label = ttk.Label(self.profile_frame, text="출력 프로파일:")
        out_profile_label.grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(5, 0))
        
        self.output_profile_var = tk.StringVar(value="sRGB")
        self.output_profile_combo = ttk.Combobox(self.profile_frame, 
                                               textvariable=self.output_profile_var,
                                               state="readonly", width=15)
        self.output_profile_combo.grid(row=1, column=1, sticky="ew", pady=(5, 0))
        
        # 프로파일 콤보박스 가중치 설정
        self.profile_frame.columnconfigure(1, weight=1)
        
        # HDR 변환 옵션 프레임
        self.hdr_frame = ttk.LabelFrame(self, text="HDR 옵션")
        
        # 노출 설정
        exposure_frame = ttk.Frame(self.hdr_frame)
        exposure_frame.pack(fill="x", pady=(0, 5))
        
        exposure_label = ttk.Label(exposure_frame, text="노출:")
        exposure_label.pack(side="left", padx=(0, 5))
        
        self.exposure_var = tk.DoubleVar(value=1.0)
        exposure_scale = ttk.Scale(exposure_frame, from_=0.1, to=5.0,
                                  variable=self.exposure_var, 
                                  orient="horizontal")
        exposure_scale.pack(side="left", fill="x", expand=True)
        
        exposure_value = ttk.Label(exposure_frame, textvariable=self.exposure_var, width=5)
        exposure_value.pack(side="left", padx=(5, 0))
        
        # 감마 설정
        gamma_frame = ttk.Frame(self.hdr_frame)
        gamma_frame.pack(fill="x", pady=(0, 5))
        
        gamma_label = ttk.Label(gamma_frame, text="감마:")
        gamma_label.pack(side="left", padx=(0, 5))
        
        self.gamma_var = tk.DoubleVar(value=2.2)
        gamma_scale = ttk.Scale(gamma_frame, from_=1.0, to=4.0,
                               variable=self.gamma_var, 
                               orient="horizontal")
        gamma_scale.pack(side="left", fill="x", expand=True)
        
        gamma_value = ttk.Label(gamma_frame, textvariable=self.gamma_var, width=5)
        gamma_value.pack(side="left", padx=(5, 0))
        
        # 톤 매핑 방식
        tone_map_frame = ttk.Frame(self.hdr_frame)
        tone_map_frame.pack(fill="x")
        
        tone_map_label = ttk.Label(tone_map_frame, text="톤 매핑 방식:")
        tone_map_label.pack(side="left", padx=(0, 5))
        
        self.tone_map_var = tk.StringVar(value="Reinhard")
        tone_map_combo = ttk.Combobox(tone_map_frame, 
                                     textvariable=self.tone_map_var,
                                     state="readonly")
        tone_map_combo.pack(side="left", fill="x", expand=True)
        
        # 기본 톤 매핑 방식 설정
        tone_map_combo["values"] = ["Reinhard", "Filmic", "ACES"]
        
        # 기타 옵션 프레임
        self.other_frame = ttk.LabelFrame(self, text="기타 옵션")
        
        # 색상 조정 옵션
        # 밝기 조정
        brightness_frame = ttk.Frame(self.other_frame)
        brightness_frame.pack(fill="x", pady=(0, 5))
        
        brightness_label = ttk.Label(brightness_frame, text="밝기:")
        brightness_label.pack(side="left", padx=(0, 5))
        
        self.brightness_var = tk.DoubleVar(value=0.0)
        brightness_scale = ttk.Scale(brightness_frame, from_=-1.0, to=1.0,
                                    variable=self.brightness_var, 
                                    orient="horizontal")
        brightness_scale.pack(side="left", fill="x", expand=True)
        
        brightness_value = ttk.Label(brightness_frame, textvariable=self.brightness_var, width=5)
        brightness_value.pack(side="left", padx=(5, 0))
        
        # 대비 조정
        contrast_frame = ttk.Frame(self.other_frame)
        contrast_frame.pack(fill="x", pady=(0, 5))
        
        contrast_label = ttk.Label(contrast_frame, text="대비:")
        contrast_label.pack(side="left", padx=(0, 5))
        
        self.contrast_var = tk.DoubleVar(value=0.0)
        contrast_scale = ttk.Scale(contrast_frame, from_=-1.0, to=1.0,
                                  variable=self.contrast_var, 
                                  orient="horizontal")
        contrast_scale.pack(side="left", fill="x", expand=True)
        
        contrast_value = ttk.Label(contrast_frame, textvariable=self.contrast_var, width=5)
        contrast_value.pack(side="left", padx=(5, 0))
        
        # 채도 조정
        saturation_frame = ttk.Frame(self.other_frame)
        saturation_frame.pack(fill="x")
        
        saturation_label = ttk.Label(saturation_frame, text="채도:")
        saturation_label.pack(side="left", padx=(0, 5))
        
        self.saturation_var = tk.DoubleVar(value=0.0)
        saturation_scale = ttk.Scale(saturation_frame, from_=-1.0, to=1.0,
                                    variable=self.saturation_var, 
                                    orient="horizontal")
        saturation_scale.pack(side="left", fill="x", expand=True)
        
        saturation_value = ttk.Label(saturation_frame, textvariable=self.saturation_var, width=5)
        saturation_value.pack(side="left", padx=(5, 0))
        
        # 옵션 위젯 참조 저장
        self.option_widgets = {
            "use_color_management": self.use_color_management,
            "input_profile": self.input_profile_var,
            "output_profile": self.output_profile_var,
            "exposure": self.exposure_var,
            "gamma": self.gamma_var,
            "tone_map_method": self.tone_map_var,
            "brightness": self.brightness_var,
            "contrast": self.contrast_var,
            "saturation": self.saturation_var,
        }
        
        # 기본적으로 HDR 옵션은 표시하지 않음
        self.hdr_frame.pack_forget()
        
        # 기타 옵션은 항상 표시
        self.other_frame.pack(fill="x", pady=(5, 0))
        
        # 초기 색 관리 옵션 상태 업데이트
        self._update_color_options()
            
    def _update_color_options(self):
        """색 관리 사용 여부에 따라 관련 옵션 위젯 상태 업데이트"""
        if self.use_color_management.get():
            # 프로파일 선택 활성화
            self.profile_frame.pack(fill="x", pady=(5, 0))
        else:
            # 프로파일 선택 비활성화
            self.profile_frame.pack_forget()
    
    def update_for_formats(self, input_format: str, output_format: str, saved_options: dict):
        """입출력 포맷에 따라 옵션 업데이트"""
        self.logger.debug(f"변환 옵션 업데이트: {input_format} → {output_format}")
        
        # 이전 저장된 옵션 초기화
        self.options = {}
        
        # HDR 관련 변환 여부 확인
        is_input_hdr = input_format in ["EXR"] if input_format else False
        is_output_hdr = output_format in ["EXR"] if output_format else False
        
        # HDR 변환 관련 옵션 표시 여부 결정
        if is_input_hdr and not is_output_hdr:
            # HDR → LDR 변환인 경우 톤 매핑 옵션 표시
            self.hdr_frame.pack(fill="x", pady=(5, 0), before=self.other_frame)
        else:
            # 그 외 경우 HDR 옵션 숨김
            self.hdr_frame.pack_forget()
        
        # 저장된 옵션 불러오기
        if saved_options:
            for key, widget_var in self.option_widgets.items():
                if key in saved_options:
                    try:
                        widget_var.set(saved_options[key])
                    except Exception as e:
                        self.logger.error(f"옵션 설정 오류 ({key}): {str(e)}")
        
        # 옵션 설정 유지
        self._update_color_options()
        
    def get_options(self) -> dict:
        """현재 설정된 옵션 반환"""
        options = {}
        for key, widget_var in self.option_widgets.items():
            options[key] = widget_var.get()
        return options
        
    def set_enabled(self, enabled: bool):
        """옵션 위젯의 활성화/비활성화 상태를 설정합니다"""
        state = "normal" if enabled else "disabled"
        
        # 색 관리 프레임 내 위젯들
        for child in self.color_frame.winfo_children():
            # Checkbutton의 경우 비활성화해도 상태 값은 변경 가능
            if child.winfo_class() == 'TCheckbutton':
                child.configure(state=state)
                
        # 프로파일 선택 프레임 내 위젯들
        for child in self.profile_frame.winfo_children():
            if hasattr(child, 'configure'):
                child.configure(state=state)
        
        # HDR 프레임 내 위젯들
        for child in self.hdr_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if hasattr(subchild, 'configure'):
                        subchild.configure(state=state)
            elif hasattr(child, 'configure'):
                child.configure(state=state)
        
        # 기타 옵션 프레임 내 위젯들
        for child in self.other_frame.winfo_children():
            if isinstance(child, ttk.Frame):
                for subchild in child.winfo_children():
                    if hasattr(subchild, 'configure'):
                        subchild.configure(state=state)
            elif hasattr(child, 'configure'):
                child.configure(state=state) 