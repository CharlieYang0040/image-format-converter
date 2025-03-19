from typing import Optional
from src.converters.base_converter import BaseConverter
from src.converters.oiio_converter import OIIOConverter
from src.converters.enhanced_converter import EnhancedConverter
from src.services.log_service import LogService

class ConverterFactory:
    """이미지 변환기 팩토리 클래스"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConverterFactory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = LogService()
        self.converters = {
            "oiio": OIIOConverter,
            "enhanced": EnhancedConverter
        }
        self.default_converter = "enhanced"
        
    def get_converter(self, converter_type: Optional[str] = None) -> BaseConverter:
        """
        지정된 타입의 변환기를 반환합니다.
        
        Args:
            converter_type: 변환기 타입 이름. 기본값은 None이며, 이 경우 기본 변환기를 반환
            
        Returns:
            BaseConverter 인스턴스
        """
        if converter_type is None:
            converter_type = self.default_converter
            
        if converter_type not in self.converters:
            self.logger.warning(f"요청된 변환기 타입 '{converter_type}'이 지원되지 않습니다. 기본 변환기를 사용합니다.")
            converter_type = self.default_converter
            
        converter_class = self.converters[converter_type]
        return converter_class()
        
    def get_available_converters(self):
        """사용 가능한 모든 변환기 목록을 반환합니다."""
        return list(self.converters.keys()) 