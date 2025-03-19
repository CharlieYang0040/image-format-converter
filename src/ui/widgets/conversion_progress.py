"""
변환 진행 상태를 표시하는 위젯 모듈
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any, Optional, Callable, Tuple
import os

class ConversionProgressWidget(ttk.Frame):
    """단일 파일 또는 배치 변환 작업의 진행 상태를 표시하는 위젯"""
    
    # 변환 단계 정의
    STAGES = [
        "준비", 
        "파일 로드",
        "이미지 분석",
        "색 공간 변환",
        "이미지 처리",
        "파일 저장",
        "완료"
    ]
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.current_stage = 0
        self.status_message = ""
        self.error_message = ""
        self.is_error = False
        self.is_complete = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 구성 요소 초기화"""
        # 상단 상태 프레임
        status_frame = ttk.Frame(self)
        status_frame.pack(fill="x", pady=(0, 5))
        
        # 상태 메시지 (고정 너비 설정)
        self.status_var = tk.StringVar(value="준비됨")
        status_label = ttk.Label(status_frame, textvariable=self.status_var,
                              font=("", 10), anchor="w", width=40, wraplength=350)
        status_label.pack(side="left")
        
        # 진행 시간 
        self.time_var = tk.StringVar(value="")
        time_label = ttk.Label(status_frame, textvariable=self.time_var,
                           font=("", 9), anchor="e", width=10)
        time_label.pack(side="right")
        
        # 전체 진행률 표시
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, orient="horizontal", length=100,
            mode="determinate", variable=self.progress_var
        )
        self.progress_bar.pack(fill="x")
        
        # 단계별 진행 프레임
        stages_frame = ttk.LabelFrame(self, text="진행 단계", padding=(10, 5))
        stages_frame.pack(fill="x")
        
        # 단계별 상태 항목 생성
        self.stage_indicators = []
        
        for i, stage_name in enumerate(self.STAGES):
            stage_frame = ttk.Frame(stages_frame)
            stage_frame.pack(fill="x", pady=2)
            
            # 체크박스 (완료 여부 표시)
            check_var = tk.BooleanVar(value=False)
            check = ttk.Checkbutton(
                stage_frame, variable=check_var, state="disabled",
                takefocus=False, text=""
            )
            check.pack(side="left")
            
            # 단계 레이블
            label = ttk.Label(stage_frame, text=stage_name, width=12, anchor="w")
            label.pack(side="left", padx=(0, 5))
            
            # 단계별 진행률
            stage_progress_var = tk.DoubleVar(value=0)
            stage_progress_bar = ttk.Progressbar(
                stage_frame, orient="horizontal",
                mode="determinate", variable=stage_progress_var,
                length=100
            )
            stage_progress_bar.pack(side="left", fill="x", expand=True)
            
            # 단계별 상태 메시지
            stage_status_var = tk.StringVar(value="")
            stage_status = ttk.Label(
                stage_frame, textvariable=stage_status_var,
                width=12, anchor="e", font=("", 9)
            )
            stage_status.pack(side="right")
            
            # 단계 정보 저장
            self.stage_indicators.append({
                "check_var": check_var,
                "progress_var": stage_progress_var,
                "status_var": stage_status_var,
                "label": label,
                "progress_bar": stage_progress_bar,
                "status": stage_status
            })
        
        # 에러 메시지 프레임
        self.error_frame = ttk.Frame(self)
        
        self.error_var = tk.StringVar(value="")
        error_label = ttk.Label(
            self.error_frame, textvariable=self.error_var,
            foreground="red", wraplength=400, justify="left"
        )
        error_label.pack(fill="x", pady=5)
        
        # 초기화
        self.reset()
        
    def update_stage(self, stage_index: int, progress: float = 0, 
                   message: str = "", is_complete: bool = False):
        """특정 단계의 진행 상태를 업데이트합니다."""
        if 0 <= stage_index < len(self.STAGES):
            # 단계 인디케이터 업데이트
            indicator = self.stage_indicators[stage_index]
            
            # 완료 여부
            indicator["check_var"].set(is_complete)
            
            # 진행률
            indicator["progress_var"].set(progress * 100)
            
            # 상태 메시지
            if message:
                indicator["status_var"].set(message)
            elif is_complete:
                indicator["status_var"].set("완료")
            else:
                indicator["status_var"].set(f"{int(progress * 100)}%")
                
            # 현재 단계 하이라이트
            for i, ind in enumerate(self.stage_indicators):
                if i == stage_index:
                    ind["label"].configure(font=("", 10, "bold"))
                else:
                    ind["label"].configure(font=("", 10))
                    
            # 전체 진행률 업데이트 (각 단계의 가중치는 균등하게 설정)
            total_progress = 0
            for i, ind in enumerate(self.stage_indicators):
                if i < stage_index:
                    # 이전 단계는 100%
                    stage_contribution = 1.0
                elif i == stage_index:
                    # 현재 단계는 현재 진행률
                    stage_contribution = progress
                else:
                    # 다음 단계는 0%
                    stage_contribution = 0.0
                    
                # 각 단계별 가중치 적용 (단순화를 위해 모든 단계의 가중치는 동일)
                total_progress += stage_contribution / len(self.STAGES)
                
            self.progress_var.set(total_progress * 100)
            
            # 현재 단계 업데이트
            self.current_stage = stage_index
    
    def set_status(self, message: str):
        """전체 상태 메시지를 설정합니다."""
        self.status_message = message
        
        # 상태 메시지가 너무 긴 경우 축약
        max_length = 50  # 최대 표시 길이
        if len(message) > max_length:
            # 파일 경로 형태인 경우 (파일명:파일명 패턴)
            if " → " in message:
                parts = message.split(" → ")
                if len(parts) == 2:
                    # 앞부분과 뒷부분 각각 처리
                    prefix = parts[0]
                    suffix = parts[1]
                    
                    # 앞부분이 너무 길면 축약
                    if len(prefix) > max_length // 2:
                        prefix_parts = prefix.split(": ", 1)
                        if len(prefix_parts) > 1:
                            # "변환 중..." 같은 접두사가 있으면 유지
                            short_prefix = f"{prefix_parts[0]}: {os.path.basename(prefix_parts[1])}"
                        else:
                            # 파일명만 추출
                            short_prefix = os.path.basename(prefix)
                        prefix = short_prefix
                    
                    # 뒷부분이 너무 길면 축약
                    if len(suffix) > max_length // 2:
                        suffix = os.path.basename(suffix)
                        
                    # 축약된 메시지 조합
                    message = f"{prefix} → {suffix}"
            else:
                # 일반 텍스트인 경우
                message = message[:max_length-3] + "..."
        
        self.status_var.set(message)
    
    def set_time(self, elapsed_seconds: float):
        """경과 시간을 설정합니다."""
        if elapsed_seconds < 60:
            time_str = f"{elapsed_seconds:.1f}초"
        else:
            minutes = int(elapsed_seconds // 60)
            seconds = int(elapsed_seconds % 60)
            time_str = f"{minutes}분 {seconds}초"
            
        self.time_var.set(time_str)
    
    def set_error(self, error_message: str):
        """오류 메시지를 설정합니다."""
        if error_message:
            self.is_error = True
            self.error_message = error_message
            self.error_var.set(f"오류: {error_message}")
            self.error_frame.pack(fill="x")
        else:
            self.is_error = False
            self.error_message = ""
            self.error_var.set("")
            self.error_frame.pack_forget()
    
    def complete(self):
        """변환 완료 상태로 설정합니다."""
        self.is_complete = True
        
        # 모든 단계 완료로 표시
        for indicator in self.stage_indicators:
            indicator["check_var"].set(True)
            indicator["progress_var"].set(100)
            indicator["status_var"].set("완료")
            
        # 전체 진행률 100%
        self.progress_var.set(100)
        
        # 상태 메시지 업데이트
        self.set_status("변환 완료")
    
    def reset(self):
        """위젯을 초기 상태로 재설정합니다."""
        self.current_stage = 0
        self.is_error = False
        self.is_complete = False
        
        # 상태 초기화
        self.set_status("준비됨")
        self.set_time(0)
        self.set_error("")
        
        # 전체 진행률 초기화
        self.progress_var.set(0)
        
        # 모든 단계 초기화
        for indicator in self.stage_indicators:
            indicator["check_var"].set(False)
            indicator["progress_var"].set(0)
            indicator["status_var"].set("")
            indicator["label"].configure(font=("", 10))  # 기본 폰트로 복원
            
        # 첫 번째 단계 하이라이트
        if self.stage_indicators:
            self.stage_indicators[0]["label"].configure(font=("", 10, "bold"))
    
    def start(self):
        """변환 시작 상태로 설정합니다."""
        self.reset()
        self.set_status("변환 중...")
        self.update_stage(0, 0.5, "진행 중") 