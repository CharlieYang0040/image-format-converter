import json
import os
import shutil
from typing import Dict, Any
from src.services.log_service import LogService

class ConfigManager:
    _instance = None
    DEFAULT_CONFIG = {
        "version": "1.0.0",  # 설정 파일 버전
        "last_input_format": "",
        "last_output_format": "",
        "last_input_directory": "",
        "last_output_directory": "",
        "last_input_file": "",
        "last_output_file": "",
        "window_size": {
            "width": 1024,
            "height": 910
        },
        "converter_options": {}  # 변환 옵션 저장용
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.logger = LogService()
        
        # 이전 설정 파일 위치 (하위 호환성을 위해 유지)
        self.old_config_dir = "config"
        self.old_config_file = os.path.join(self.old_config_dir, "settings.json")
        
        # 새 설정 파일 위치
        self.config_dir = os.path.join(os.path.expanduser("~"), ".image_converter")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.config = self.DEFAULT_CONFIG.copy()
        
        # 설정 로드
        self._load_config()
    
    def _load_config(self):
        """설정 파일을 로드합니다."""
        try:
            # 1. 새 위치에서 로드 시도
            if os.path.exists(self.config_file):
                self.logger.debug(f"새 위치에서 설정 파일 로드 시도: {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 기본 설정과 병합 (중첩 딕셔너리도 처리)
                    self._merge_config(saved_config)
                self.logger.info(f"설정 파일 로드 완료: {self.config_file}")
                return
                
            # 2. 이전 위치에서 로드 시도
            if os.path.exists(self.old_config_file):
                self.logger.debug(f"이전 위치에서 설정 파일 로드 시도: {self.old_config_file}")
                with open(self.old_config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 기본 설정과 병합 (중첩 딕셔너리도 처리)
                    self._merge_config(saved_config)
                self.logger.info(f"이전 설정 파일 로드 완료: {self.old_config_file}")
                
                # 설정 마이그레이션: 이전 파일을 새 위치로 복사
                self.logger.debug(f"설정 파일 마이그레이션: {self.old_config_file} -> {self.config_file}")
                self._save_config()
                return
                
            # 3. 설정 파일이 없는 경우 기본 설정 사용
            self.logger.info("설정 파일이 없어 기본 설정을 사용합니다.")
            self._save_config()
        except Exception as e:
            self.logger.error(f"설정 파일 로드 중 오류 발생: {str(e)}")
            self.logger.info("오류로 인해 기본 설정을 사용합니다.")
            self.config = self.DEFAULT_CONFIG.copy()
            self._save_config()
    
    def _merge_config(self, saved_config):
        """중첩 딕셔너리를 포함한 설정을 병합합니다."""
        for key, value in saved_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                # 중첩 딕셔너리 병합
                self.config[key].update(value)
            else:
                # 일반 값 업데이트
                self.config[key] = value
                
        # 버전 정보 추가
        self.config["version"] = self.DEFAULT_CONFIG["version"]
    
    def _save_config(self):
        """설정을 파일에 저장합니다."""
        try:
            # 설정 디렉토리 생성
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                self.logger.debug(f"설정 디렉토리 생성: {self.config_dir}")
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"설정 파일 저장 완료: {self.config_file}")
        except Exception as e:
            self.logger.error(f"설정 파일 저장 중 오류 발생: {str(e)}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 값을 가져옵니다."""
        # 키가 존재하지 않는 경우 기본값 반환
        if key not in self.config:
            return default
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
    
    def save_format_options(self, input_format: str, output_format: str, options: Dict[str, Any]):
        """특정 포맷 조합에 대한 변환 옵션을 저장합니다."""
        key = f"{input_format}_{output_format}"
        
        if "converter_options" not in self.config:
            self.config["converter_options"] = {}
            
        self.config["converter_options"][key] = options
        self._save_config()
    
    def get_format_options(self, input_format: str, output_format: str) -> Dict[str, Any]:
        """특정 포맷 조합에 대한 변환 옵션을 가져옵니다."""
        if "converter_options" not in self.config:
            return {}
            
        key = f"{input_format}_{output_format}"
        return self.config["converter_options"].get(key, {})