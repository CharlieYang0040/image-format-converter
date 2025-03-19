from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
from src.services.log_service import LogService

class BaseConverter(ABC):
    """모든 변환기의 기본 클래스"""
    
    def __init__(self):
        self.logger = LogService()
        
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """지원되는 이미지 포맷 목록을 반환합니다."""
        pass
        
    @abstractmethod
    def convert_image(self, input_path: str, output_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        이미지를 변환합니다.
        
        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로
            
        Returns:
            (성공 여부, 메시지, 추가 정보) 튜플
        """
        pass
        
    @abstractmethod
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        이미지의 기본 정보를 반환합니다.
        
        Args:
            image_path: 이미지 경로
            
        Returns:
            이미지 정보를 담은 딕셔너리
        """
        pass 