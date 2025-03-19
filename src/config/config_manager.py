import json
import os
from typing import Dict, Any
from src.services.log_service import LogService

class ConfigManager:
    _instance = None
    DEFAULT_CONFIG = {
        "last_input_format": "",
        "last_output_format": "",
        "last_input_directory": "",
        "last_output_directory": "",
        "window_size": {
            "width": 600,
            "height": 400
        }
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = LogService()
        self.config_dir = "config"
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.config = self.DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _load_config(self):
        """설정 파일을 로드합니다."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 기본 설정과 병합
                    self.config.update(saved_config)
                self.logger.info("설정 파일 로드 완료")
            else:
                self._save_config()
        except Exception as e:
            self.logger.error(f"설정 파일 로드 중 오류 발생: {str(e)}")
    
    def _save_config(self):
        """설정을 파일에 저장합니다."""
        try:
            # 설정 디렉토리 생성
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info("설정 파일 저장 완료")
        except Exception as e:
            self.logger.error(f"설정 파일 저장 중 오류 발생: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값을 가져옵니다."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """설정 값을 저장합니다."""
        self.config[key] = value
        self._save_config()
    
    def update(self, config_dict: Dict[str, Any]):
        """여러 설정 값을 한 번에 업데이트합니다."""
        self.config.update(config_dict)
        self._save_config()
    
    def reset(self):
        """설정을 기본값으로 초기화합니다."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config() 