import tkinter as tk
from tkinter import ttk
import time
from typing import Dict, Any, List
import os

class BatchProgressWidget(ttk.LabelFrame):
    """배치 변환 진행 상황을 표시하는 위젯"""
    
    def __init__(self, parent, title="배치 변환 진행 상황"):
        """
        배치 변환 진행 상황 위젯을 초기화합니다.
        
        Args:
            parent: 부모 위젯
            title: 프레임 제목
        """
        super().__init__(parent, text=title, padding=10)
        self.tasks = {}  # 작업 목록
        self.create_widgets()
        
    def create_widgets(self):
        """위젯 구성 요소를 생성합니다."""
        # 전체 진행률 
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.total_progress_var = tk.DoubleVar(value=0)
        self.total_progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.total_progress_var,
            length=100, 
            mode="determinate"
        )
        self.total_progress_bar.pack(fill="x", side="top")
        
        # 현재 진행 상태 표시
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill="x", expand=True, pady=(5, 0))
        
        ttk.Label(status_frame, text="상태:").pack(side="left", padx=(0, 5))
        self.status_var = tk.StringVar(value="준비")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side="left")
        
        ttk.Label(status_frame, text="처리중:").pack(side="left", padx=(10, 5))
        self.processing_var = tk.StringVar(value="0")
        processing_label = ttk.Label(status_frame, textvariable=self.processing_var)
        processing_label.pack(side="left")
        
        ttk.Label(status_frame, text="완료:").pack(side="left", padx=(10, 5))
        self.completed_var = tk.StringVar(value="0/0")
        completed_label = ttk.Label(status_frame, textvariable=self.completed_var)
        completed_label.pack(side="left")
        
        ttk.Label(status_frame, text="실패:").pack(side="left", padx=(10, 5))
        self.failed_var = tk.StringVar(value="0")
        failed_label = ttk.Label(status_frame, textvariable=self.failed_var, foreground="red")
        failed_label.pack(side="left")
        
        # 작업 목록 표시
        files_frame = ttk.LabelFrame(self, text="처리 파일", padding=(5, 5))
        files_frame.pack(fill="both", expand=True)
        
        # 트리뷰로 파일 목록 표시
        columns = ("file", "status", "progress", "time")
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show="headings", height=8)
        
        # 스크롤바 추가
        scrollbar_y = ttk.Scrollbar(files_frame, orient="vertical", command=self.files_tree.yview)
        scrollbar_x = ttk.Scrollbar(files_frame, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 패킹 순서 중요
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.files_tree.pack(side="left", fill="both", expand=True)
        
        # 컬럼 설정
        self.files_tree.heading("file", text="파일")
        self.files_tree.heading("status", text="상태")
        self.files_tree.heading("progress", text="진행")
        self.files_tree.heading("time", text="처리 시간")
        
        self.files_tree.column("file", width=250, stretch=True)
        self.files_tree.column("status", width=80, stretch=False)
        self.files_tree.column("progress", width=60, stretch=False)
        self.files_tree.column("time", width=80, stretch=False)
        
        # 상태별 색상 태그 설정
        self.files_tree.tag_configure("processing", background="#E6F3FF")  # 연한 파란색
        self.files_tree.tag_configure("completed", background="#E6FFE6")   # 연한 녹색
        self.files_tree.tag_configure("failed", background="#FFE6E6")      # 연한 빨간색
        
        # 버튼 프레임
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=(10, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="취소", state="disabled")
        self.cancel_button.pack(side="right")
        
    def update_progress(self, completed: int, total: int, progress_info: Dict[str, Any]):
        """
        진행 상황을 업데이트합니다.
        
        Args:
            completed: 완료된 작업 수
            total: 전체 작업 수
            progress_info: 진행 정보
        """
        # 진행률 계산
        percentage = (completed / total) * 100 if total > 0 else 0
        self.total_progress_var.set(percentage)
        
        # 상태 텍스트 업데이트
        if percentage == 100:
            self.status_var.set("완료")
            self.cancel_button.configure(state="disabled")
        else:
            self.status_var.set(f"변환 중... ({percentage:.1f}%)")
            self.cancel_button.configure(state="normal")
            
        # 처리 상태 업데이트
        self.completed_var.set(f"{completed}/{total}")
        
        # 처리중 파일 수
        processing_count = len(progress_info.get("processing", []))
        self.processing_var.set(str(processing_count))
        
        # 실패 파일 수
        failed_count = len(progress_info.get("failed", []))
        self.failed_var.set(str(failed_count))
        
        # 파일 목록 업데이트
        self._update_file_list(progress_info)
        
    def _update_file_list(self, progress_info: Dict[str, Any]):
        """파일 목록을 업데이트합니다."""
        # 처리 중인 작업 먼저 표시
        processing = progress_info.get("processing", [])
        for task_info in processing:
            file_path = task_info["input_path"]
            progress_pct = task_info.get("progress", 0)
            item_id = self._get_or_create_item(file_path)
            
            # 진행 상태를 백분율로 표시
            progress_str = f"{progress_pct:.0f}%" if progress_pct > 0 else "처리 중"
            
            self.files_tree.item(item_id, values=(
                os.path.basename(file_path),
                "처리 중",
                progress_str,
                f"{task_info['duration']:.1f}초"
            ), tags=("processing",))
            
            # 툴팁으로 전체 경로 표시
            self._set_tooltip(item_id, file_path)
            
        # 최근 완료된 작업 표시
        completed = progress_info.get("completed", [])
        for task_info in completed[-20:]:  # 최근 20개만
            file_path = task_info["input_path"]
            item_id = self._get_or_create_item(file_path)
            self.files_tree.item(item_id, values=(
                os.path.basename(file_path),
                "완료",
                "100%",
                f"{task_info['duration']:.1f}초"
            ), tags=("completed",))
            
            # 툴팁으로 전체 경로 표시
            self._set_tooltip(item_id, file_path)
            
        # 실패한 작업 표시
        failed = progress_info.get("failed", [])
        for task_info in failed:
            file_path = task_info["input_path"]
            error_msg = task_info.get("error", "")
            item_id = self._get_or_create_item(file_path)
            
            status_text = "실패"
            if error_msg:
                # 오류 메시지가 있는 경우 상태에 괄호로 표시
                error_brief = error_msg[:15] + "..." if len(error_msg) > 15 else error_msg
                status_text = f"실패 ({error_brief})"
                
            self.files_tree.item(item_id, values=(
                os.path.basename(file_path),
                status_text,
                "-",
                f"{task_info['duration']:.1f}초"
            ), tags=("failed",))
            
            # 툴팁으로 전체 경로와 오류 메시지 표시
            tooltip_text = f"{file_path}\n오류: {error_msg}" if error_msg else file_path
            self._set_tooltip(item_id, tooltip_text)
            
        # 트리뷰 정렬 (처리 중 → 실패 → 완료 순)
        all_items = self.files_tree.get_children()
        sorted_items = sorted(all_items, key=lambda item: (
            0 if self.files_tree.item(item)["values"][1].startswith("처리 중") else 
            (1 if self.files_tree.item(item)["values"][1].startswith("실패") else 2)
        ))
        
        for i, item in enumerate(sorted_items):
            self.files_tree.move(item, "", i)
            
    def _set_tooltip(self, item_id, tooltip_text):
        """트리뷰 항목에 툴팁 설정 (향후 구현을 위한 준비)"""
        # 현재는 구현하지 않음 - tkinter에서 트리뷰 아이템 툴팁 구현은 복잡함
        pass
            
    def _get_or_create_item(self, file_path: str):
        """파일 경로에 해당하는 트리뷰 아이템을 가져오거나 생성합니다."""
        if file_path in self.tasks:
            return self.tasks[file_path]
            
        # 아이템 생성
        item_id = self.files_tree.insert("", "end", values=(
            os.path.basename(file_path),
            "대기 중",
            "-",
            "0.0초"
        ))
        self.tasks[file_path] = item_id
        
        # 최대 표시 개수 제한
        if len(self.tasks) > 500:  # 최대 500개 항목 유지
            oldest = next(iter(self.tasks))
            self.files_tree.delete(self.tasks[oldest])
            del self.tasks[oldest]
            
        return item_id
        
    def set_cancel_callback(self, callback):
        """취소 버튼 콜백 설정"""
        self.cancel_button.configure(command=callback)
        
    def reset(self):
        """위젯 상태 초기화"""
        self.tasks = {}
        self.total_progress_var.set(0)
        self.status_var.set("준비")
        self.completed_var.set("0/0")
        self.processing_var.set("0")
        self.failed_var.set("0")
        self.cancel_button.configure(state="disabled")
        
        # 트리뷰 항목 모두 삭제
        for item in self.files_tree.get_children():
            self.files_tree.delete(item) 