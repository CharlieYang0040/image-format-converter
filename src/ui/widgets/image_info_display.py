import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

class ImageInfoDisplay(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="이미지 정보", padding="10", **kwargs)
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 요소들을 설정합니다."""
        # 그리드 기반 레이아웃 사용
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)
        
        # 이미지 속성 카드들
        self.cards_frame = ttk.Frame(self.main_frame)
        self.cards_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 속성 카드들을 저장할 딕셔너리
        self.info_cards = {}
        
        # 기본 속성 카드 생성
        self._create_info_card("dimensions", "크기", "")
        self._create_info_card("channels", "채널", "")
        self._create_info_card("format", "포맷", "")
        self._create_info_card("file_size", "파일 크기", "")
        
        # 에러 메시지 표시용 레이블
        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(self.main_frame, textvariable=self.error_var, 
                                    foreground="red", wraplength=300, justify="left")
        self.error_label.pack(fill="x", expand=True, padx=5, pady=5)
        self.error_label.pack_forget()  # 초기에는 숨김
        
    def _create_info_card(self, key: str, title: str, value: str):
        """정보 카드를 생성합니다."""
        card = ttk.Frame(self.cards_frame, relief="solid", borderwidth=1)
        card.grid(row=len(self.info_cards) // 2, 
                 column=len(self.info_cards) % 2, 
                 sticky="nsew", padx=3, pady=3)
        
        # 카드 내부 구성
        title_label = ttk.Label(card, text=title, font=("", 9, "bold"))
        title_label.pack(fill="x", padx=5, pady=(5, 0))
        
        value_var = tk.StringVar(value=value)
        value_label = ttk.Label(card, textvariable=value_var)
        value_label.pack(fill="x", padx=5, pady=(0, 5))
        
        # 그리드 가중치 설정
        self.cards_frame.columnconfigure(0, weight=1)
        self.cards_frame.columnconfigure(1, weight=1)
        
        # 카드 정보 저장
        self.info_cards[key] = {
            "frame": card,
            "title_label": title_label,
            "value_var": value_var,
            "value_label": value_label
        }
        
    def update_info(self, info: Dict[str, Any]):
        """이미지 정보를 업데이트합니다."""
        if "error" in info:
            # 에러 발생 시 카드 숨기고 에러 메시지 표시
            self.cards_frame.pack_forget()
            self.error_var.set(f"오류: {info['error']}")
            self.error_label.pack(fill="x", expand=True, padx=5, pady=5)
            return
            
        # 에러가 없으면 카드 표시하고 에러 메시지 숨김
        self.cards_frame.pack(fill="both", expand=True)
        self.error_label.pack_forget()
        
        # 기본 정보 업데이트
        self.info_cards["dimensions"]["value_var"].set(f"{info['width']} × {info['height']} 픽셀")
        self.info_cards["channels"]["value_var"].set(f"{info['channels']}개")
        
        # 포맷 정보에 메타데이터가 있으면 함께 표시
        format_info = f"{info['format']}"
        if "metadata" in info and len(info["metadata"]) > 0:
            format_info += f" (메타데이터 {len(info['metadata'])}개)"
        self.info_cards["format"]["value_var"].set(format_info)
        
        # 파일 크기를 적절한 단위로 표시
        if "file_size_mb" in info:
            self.info_cards["file_size"]["value_var"].set(f"{info['file_size_mb']:.2f} MB")
        elif "file_size_bytes" in info:
            kb_size = info['file_size_bytes'] / 1024
            self.info_cards["file_size"]["value_var"].set(f"{kb_size:.2f} KB")
        else:
            self.info_cards["file_size"]["value_var"].set(f"{info['file_size'] / 1024:.2f} KB")
        
    def clear(self):
        """정보를 초기화합니다."""
        for card_info in self.info_cards.values():
            card_info["value_var"].set("")
        self.error_var.set("")
        self.error_label.pack_forget()
        self.cards_frame.pack(fill="both", expand=True) 