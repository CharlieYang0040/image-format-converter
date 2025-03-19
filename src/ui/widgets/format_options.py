import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from src.utils.image_utils import ImageFormatUtils
from src.color_management import ColorManager

class FormatOptionsWidget(ttk.LabelFrame):
    """포맷 변환 관련 옵션을 설정하는 위젯"""
    
    def __init__(self, parent, title: str = "변환 옵션", 
                on_option_change: Optional[Callable] = None, **kwargs):
        super().__init__(parent, text=title, padding="10", **kwargs)
        
        self.on_option_change = on_option_change
        self.options = {}  # 현재 설정된 옵션 값
        self.option_widgets = {}  # 옵션 위젯 레퍼런스
        
        # 색 관리 모듈 초기화
        self.color_manager = ColorManager()
        self.input_format = None
        self.output_format = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 요소들을 설정합니다."""
        # 옵션 섹션 컨테이너
        self.options_container = ttk.Frame(self)
        self.options_container.pack(fill="both", expand=True)
        
        # 초기 옵션 생성
        self._create_basic_options()
        
    def _create_basic_options(self):
        """기본 옵션들을 생성합니다."""
        # 색 관리 섹션
        self._add_option_section("color_management", "색 관리")
        
        # 색 프로파일 선택
        color_profiles = self.color_manager.get_available_profiles()
        self._add_combobox_option(
            section="color_management",
            name="input_profile",
            label="입력 색 공간",
            values=[(p, p) for p in color_profiles],
            default=0,
            tooltip="입력 이미지의 색 공간을 선택합니다."
        )
        
        self._add_combobox_option(
            section="color_management",
            name="output_profile",
            label="출력 색 공간",
            values=[(p, p) for p in color_profiles],
            default=0,
            tooltip="출력 이미지의 색 공간을 선택합니다."
        )
        
        # 색상 조정 섹션
        self._add_option_section("color_adjustments", "색상 조정")
        
        # 밝기 조정
        self._add_slider_option(
            section="color_adjustments",
            name="brightness",
            label="밝기 조정",
            min_val=-1.0,
            max_val=1.0,
            default=0.0,
            resolution=0.05,
            tooltip="이미지 밝기를 조정합니다."
        )
        
        # 대비 조정
        self._add_slider_option(
            section="color_adjustments",
            name="contrast",
            label="대비 조정",
            min_val=-1.0,
            max_val=1.0,
            default=0.0,
            resolution=0.05,
            tooltip="이미지 대비를 조정합니다."
        )
        
        # 채도 조정
        self._add_slider_option(
            section="color_adjustments",
            name="saturation",
            label="채도 조정",
            min_val=-1.0,
            max_val=1.0,
            default=0.0,
            resolution=0.05,
            tooltip="이미지 채도를 조정합니다."
        )
        
        # 노출 조정
        self._add_slider_option(
            section="color_adjustments",
            name="exposure_stops",
            label="노출 조정 (EV)",
            min_val=-3.0,
            max_val=3.0,
            default=0.0,
            resolution=0.25,
            tooltip="이미지 노출을 EV(Exposure Value)로 조정합니다."
        )
        
        # HDR → LDR 변환 관련 옵션
        self._add_option_section("hdr_options", "HDR 변환 옵션")
        
        # 톤 매핑 방식
        tone_mapping_methods = self.color_manager.get_available_tone_mapping_methods()
        self._add_combobox_option(
            section="hdr_options",
            name="tone_map_method",
            label="톤 매핑 방식",
            values=[(tm, tm) for tm in tone_mapping_methods],
            default=1,  # Reinhard가 기본
            tooltip="HDR 이미지를 LDR로 변환할 때 사용할 톤 매핑 방식"
        )
        
        # 노출 설정
        self._add_slider_option(
            section="hdr_options",
            name="exposure",
            label="노출 조정",
            min_val=0.1,
            max_val=5.0,
            default=1.0,
            resolution=0.1,
            tooltip="HDR 이미지의 노출값을 조정합니다."
        )
        
        # 감마 설정
        self._add_slider_option(
            section="hdr_options",
            name="gamma",
            label="감마 값",
            min_val=1.0,
            max_val=3.0,
            default=2.2,
            resolution=0.1,
            tooltip="감마 보정값을 조정합니다."
        )
        
        # 알파 채널 관련 옵션
        self._add_option_section("alpha_options", "알파 채널 옵션")
        
        # 배경색 설정
        self._add_combobox_option(
            section="alpha_options",
            name="background_color",
            label="배경색",
            values=[
                ("흰색", (1, 1, 1)),
                ("검정색", (0, 0, 0)),
                ("회색", (0.5, 0.5, 0.5)),
                ("투명색", (0, 0, 0, 0))
            ],
            default=0,
            tooltip="알파 채널 제거 시 사용할 배경색을 선택합니다."
        )
        
        # JPEG 품질 옵션
        self._add_option_section("jpeg_options", "JPEG 옵션")
        
        self._add_slider_option(
            section="jpeg_options",
            name="jpeg_quality",
            label="JPEG 품질",
            min_val=1,
            max_val=100,
            default=90,
            resolution=1,
            tooltip="JPEG 압축 품질을 설정합니다. 높을수록 화질이 좋아지고 파일 크기가 커집니다."
        )
        
        # 초기에는 모든 섹션 숨김
        self._hide_all_option_sections()
        
    def _add_option_section(self, section_name: str, section_title: str):
        """옵션 섹션을 추가합니다."""
        section_frame = ttk.LabelFrame(self.options_container, text=section_title)
        section_frame.pack(fill="x", pady=5)
        
        self.option_widgets[section_name] = {
            "frame": section_frame,
            "options": {}
        }
        
    def _add_slider_option(self, section: str, name: str, label: str, 
                          min_val: float, max_val: float, default: float,
                          resolution: float = 0.1, tooltip: str = ""):
        """슬라이더 기반 옵션을 추가합니다."""
        if section not in self.option_widgets:
            return
            
        section_data = self.option_widgets[section]
        section_frame = section_data["frame"]
        
        # 옵션 프레임
        option_frame = ttk.Frame(section_frame)
        option_frame.pack(fill="x", pady=3)
        
        # 레이블
        label_widget = ttk.Label(option_frame, text=label)
        label_widget.pack(side="left", padx=(0, 5))
        
        if tooltip:
            self._create_tooltip(label_widget, tooltip)
        
        # 슬라이더 및 입력 필드를 담을 하위 프레임
        control_frame = ttk.Frame(option_frame)
        control_frame.pack(side="right", fill="x", expand=True)
        
        # 값 변수 (슬라이더와 입력 필드 공유)
        value_var = tk.DoubleVar(value=default)
        
        # 입력 필드 (Entry)
        entry_width = 6
        entry = ttk.Entry(control_frame, textvariable=value_var, width=entry_width)
        entry.pack(side="right", padx=(5, 0))
        
        # 슬라이더
        slider = ttk.Scale(
            control_frame, 
            from_=min_val, 
            to=max_val, 
            variable=value_var,
            orient="horizontal"
        )
        slider.pack(side="right", fill="x", expand=True)
        
        # 값 변경 시 표시 업데이트 및 범위 검사
        def _validate_and_update(*args):
            try:
                # 현재 값을 가져옴
                value = value_var.get()
                
                # 범위 검사 및 보정
                if value < min_val:
                    value = min_val
                    value_var.set(min_val)
                elif value > max_val:
                    value = max_val
                    value_var.set(max_val)
                
                # 설정된 해상도에 맞게 반올림
                if resolution > 0:
                    value = round(value / resolution) * resolution
                    value_var.set(value)
                
                # 옵션 갱신 및 콜백 호출
                self._notify_option_change(name, value)
                
            except (ValueError, tk.TclError):
                # 입력 값이 유효하지 않을 경우 기본값으로 재설정
                value_var.set(default)
                
        # 입력 필드에서 Enter 키 누를 때 검증
        def _on_enter(event):
            _validate_and_update()
            
        # 입력 필드에서 포커스 잃을 때 검증
        def _on_focus_out(event):
            _validate_and_update()
        
        # 슬라이더 변경 시 값 업데이트
        def _on_scale_change(*args):
            _validate_and_update()
        
        # 이벤트 바인딩
        value_var.trace_add("write", _on_scale_change)
        entry.bind("<Return>", _on_enter)
        entry.bind("<FocusOut>", _on_focus_out)
        
        # 초기값 설정
        _validate_and_update()
        
        # 옵션 저장
        section_data["options"][name] = {
            "frame": option_frame,
            "var": value_var,
            "widget": slider,
            "entry": entry
        }
        
        # 기본값 저장
        self.options[name] = default
        
    def _add_combobox_option(self, section: str, name: str, label: str,
                            values: list, default: int = 0, tooltip: str = ""):
        """콤보박스 기반 옵션을 추가합니다."""
        if section not in self.option_widgets:
            return
            
        section_data = self.option_widgets[section]
        section_frame = section_data["frame"]
        
        # 옵션 프레임
        option_frame = ttk.Frame(section_frame)
        option_frame.pack(fill="x", pady=3)
        
        # 레이블
        label_widget = ttk.Label(option_frame, text=label)
        label_widget.pack(side="left", padx=(0, 5))
        
        if tooltip:
            self._create_tooltip(label_widget, tooltip)
        
        # 콤보박스 값과 표시 텍스트 분리
        display_values = [v[0] for v in values]
        actual_values = [v[1] for v in values]
        
        # 콤보박스
        value_var = tk.StringVar()
        combo = ttk.Combobox(
            option_frame,
            textvariable=value_var,
            values=display_values,
            state="readonly"
        )
        combo.pack(side="right", fill="x", expand=True)
        
        # 인덱스 기반 선택
        if 0 <= default < len(display_values):
            combo.current(default)
            self.options[name] = actual_values[default]
        
        # 값 변경 시 처리
        def _on_select(event):
            idx = combo.current()
            if 0 <= idx < len(actual_values):
                self.options[name] = actual_values[idx]
                self._notify_option_change(name, actual_values[idx])
        
        combo.bind("<<ComboboxSelected>>", _on_select)
        
        # 옵션 저장
        section_data["options"][name] = {
            "frame": option_frame,
            "var": value_var,
            "widget": combo,
            "values": actual_values
        }
    
    def _create_tooltip(self, widget, text):
        """위젯에 툴팁을 추가합니다."""
        def _show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # 툴팁 생성
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1, padding=3)
            label.pack()
            
            self._tooltip = tooltip
            
        def _hide_tooltip(event):
            if hasattr(self, '_tooltip'):
                self._tooltip.destroy()
                del self._tooltip
                
        widget.bind("<Enter>", _show_tooltip)
        widget.bind("<Leave>", _hide_tooltip)
    
    def _notify_option_change(self, name, value):
        """옵션 변경을 알립니다."""
        self.options[name] = value
        if self.on_option_change:
            self.on_option_change(name, value, self.options)
            
    def update_for_formats(self, input_format: str, output_format: str, saved_options: dict = None):
        """입력 및 출력 포맷에 따라 관련 옵션들을 표시합니다."""
        self.input_format = input_format
        self.output_format = output_format
        
        # 옵션 초기화
        self.options = {}
        
        # 포맷 조합에 따라 옵션 추가
        self._add_options_for_formats(input_format, output_format)
        
        # 저장된 옵션 불러오기
        if saved_options:
            self._load_saved_options(saved_options)
        
        # 옵션 UI 업데이트
        self._update_ui()
        
    def _load_saved_options(self, saved_options: dict):
        """저장된 옵션 값을 로드합니다."""
        for key, value in saved_options.items():
            if key in self.options:
                if isinstance(self.options[key], bool):
                    self.options[key] = bool(value)
                elif isinstance(self.options[key], (int, float)):
                    self.options[key] = float(value)
                elif isinstance(self.options[key], str):
                    self.options[key] = str(value)
                else:
                    self.options[key] = value
                    
                # 위젯에도 값 설정
                for section_name, section_data in self.option_widgets.items():
                    if key in section_data["options"]:
                        option_data = section_data["options"][key]
                        if "var" in option_data:
                            if isinstance(option_data["var"], tk.BooleanVar):
                                option_data["var"].set(bool(value))
                            elif isinstance(option_data["var"], tk.DoubleVar):
                                option_data["var"].set(float(value))
                            elif isinstance(option_data["var"], tk.IntVar):
                                option_data["var"].set(int(value))
                            elif isinstance(option_data["var"], tk.StringVar):
                                option_data["var"].set(str(value))
                        
    def _add_options_for_formats(self, input_format: str, output_format: str):
        """입력 및 출력 포맷 조합에 따라 필요한 옵션을 추가합니다."""
        # 항상 추가되는 색 관리 기본 옵션
        self._add_color_management_options()
        
        # HDR → LDR 변환 시 HDR 옵션 추가
        if ImageFormatUtils.is_hdr_format(input_format) and not ImageFormatUtils.is_hdr_format(output_format):
            self._add_hdr_options()
        
        # 알파 채널 처리 필요 시 관련 옵션 추가
        if ImageFormatUtils.has_alpha_support(input_format) and not ImageFormatUtils.has_alpha_support(output_format):
            self._add_alpha_options()
            
        # JPEG 출력 시 품질 설정 추가
        if output_format == "JPEG":
            self._add_jpeg_options()
            
    def _add_color_management_options(self):
        """색 관리 관련 옵션을 추가합니다."""
        if "color_management" not in self.option_widgets:
            return
            
        # 입력 프로파일 옵션
        input_profile_option = self.option_widgets["color_management"]["options"].get("input_profile")
        if input_profile_option:
            # 기본값 선택 (자동 감지)
            self.options["input_profile"] = ""  # 빈 값은 자동 감지를 의미
            
        # 출력 프로파일 옵션
        output_profile_option = self.option_widgets["color_management"]["options"].get("output_profile")
        if output_profile_option:
            # sRGB가 기본값
            idx = 0
            for i, val in enumerate(output_profile_option["values"]):
                if val == "sRGB":
                    idx = i
                    break
            
            output_profile_option["widget"].current(idx)
            self.options["output_profile"] = "sRGB"
            
        # 색상 조정 옵션 초기화
        for option_name in ["brightness", "contrast", "saturation", "exposure_stops"]:
            option_data = self.option_widgets["color_adjustments"]["options"].get(option_name)
            if option_data:
                self.options[option_name] = 0.0
            
    def _add_hdr_options(self):
        """HDR 변환 관련 옵션을 추가합니다."""
        if "hdr_options" not in self.option_widgets:
            return
            
        # 톤 매핑 방식 옵션
        tone_map_option = self.option_widgets["hdr_options"]["options"].get("tone_map_method")
        if tone_map_option:
            # Reinhard가 기본 톤 매핑 방식
            idx = 0
            for i, val in enumerate(tone_map_option["values"]):
                if val == "Reinhard":
                    idx = i
                    break
                    
            tone_map_option["widget"].current(idx)
            self.options["tone_map_method"] = "Reinhard"
            
        # 노출 옵션
        exposure_option = self.option_widgets["hdr_options"]["options"].get("exposure")
        if exposure_option:
            self.options["exposure"] = 1.0  # 기본 노출
            
        # 감마 옵션
        gamma_option = self.option_widgets["hdr_options"]["options"].get("gamma")
        if gamma_option:
            self.options["gamma"] = 2.2  # 기본 감마
    
    def _add_alpha_options(self):
        """알파 채널 관련 옵션을 추가합니다."""
        if "alpha_options" not in self.option_widgets:
            return
            
        # 배경색 옵션
        bg_option = self.option_widgets["alpha_options"]["options"].get("background_color")
        if bg_option:
            # 기본 흰색 배경
            self.options["background_color"] = (1, 1, 1)
    
    def _add_jpeg_options(self):
        """JPEG 관련 옵션을 추가합니다."""
        if "jpeg_options" not in self.option_widgets:
            return
            
        # JPEG 품질 옵션
        quality_option = self.option_widgets["jpeg_options"]["options"].get("jpeg_quality")
        if quality_option:
            self.options["jpeg_quality"] = 90  # 기본 품질
            
    def _update_ui(self):
        """옵션에 따라 UI를 업데이트합니다."""
        # 모든 섹션 숨김
        self._hide_all_option_sections()
        
        # 색 관리 옵션 (항상 표시)
        self._show_option_section("color_management")
        
        # 색상 조정 옵션
        self._show_option_section("color_adjustments")
        
        # HDR → LDR 변환 시 HDR 옵션 표시
        if ImageFormatUtils.is_hdr_format(self.input_format) and not ImageFormatUtils.is_hdr_format(self.output_format):
            self._show_option_section("hdr_options")
        
        # 알파 채널 처리 필요 시 관련 옵션 표시
        if ImageFormatUtils.has_alpha_support(self.input_format) and not ImageFormatUtils.has_alpha_support(self.output_format):
            self._show_option_section("alpha_options")
            
        # JPEG 출력 시 품질 설정 표시
        if self.output_format == "JPEG":
            self._show_option_section("jpeg_options")
    
    def _hide_all_option_sections(self):
        """모든 옵션 섹션을 숨깁니다."""
        for section_name, section_data in self.option_widgets.items():
            section_data["frame"].pack_forget()
            
    def _show_option_section(self, section_name: str):
        """지정한 옵션 섹션을 표시합니다."""
        if section_name in self.option_widgets:
            self.option_widgets[section_name]["frame"].pack(fill="x", pady=5)
    
    def get_options(self) -> Dict[str, Any]:
        """현재 설정된 모든 옵션 값을 반환합니다."""
        # 색 관리 기능 사용 여부 옵션 추가
        self.options["use_color_management"] = True
        return self.options.copy() 