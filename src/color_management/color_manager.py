"""
색 관리 핵심 모듈

이미지 변환 및 처리 시 색 관리 기능을 총괄하는 클래스를 제공합니다.
"""

import os
import numpy as np
import OpenImageIO as oiio
from typing import Dict, List, Tuple, Optional, Union, Any
from src.services.log_service import LogService
from .color_profiles import ColorProfile, ColorProfileManager
from .color_transforms import ColorTransform, ToneMapMethod

class ColorManager:
    """색 관리 핵심 클래스
    
    이미지 파일 및 데이터의 색 공간을 처리하고, 각종 색상 조정 기능을 제공합니다.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ColorManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """초기화 메서드"""
        self.logger = LogService()
        self.profile_manager = ColorProfileManager()
        self.transform = ColorTransform()
        
        # 기본 설정
        self.default_input_profile = "sRGB"
        self.default_output_profile = "sRGB"
        
        self.logger.debug("색 관리 모듈 초기화 완료")
    
    def get_available_profiles(self) -> List[str]:
        """사용 가능한 색 프로파일 목록을 반환합니다."""
        profiles = self.profile_manager.get_all_profiles()
        return [p.name for p in profiles]
    
    def get_available_tone_mapping_methods(self) -> List[str]:
        """사용 가능한 톤 매핑 방식 목록을 반환합니다."""
        return [method.value for method in ToneMapMethod]
    
    def detect_image_profile(self, image_path: str) -> Optional[ColorProfile]:
        """이미지 파일에서 색 프로파일을 감지합니다."""
        return self.profile_manager.detect_profile_from_image(image_path)
    
    def get_profile(self, profile_name: str) -> Optional[ColorProfile]:
        """프로파일 이름으로 프로파일 객체를 가져옵니다."""
        return self.profile_manager.get_profile(profile_name)
    
    def get_default_input_profile(self) -> ColorProfile:
        """기본 입력 프로파일을 가져옵니다."""
        profile = self.profile_manager.get_profile(self.default_input_profile)
        if not profile:
            profile = self.profile_manager.get_default_profile()
        return profile
    
    def get_default_output_profile(self) -> ColorProfile:
        """기본 출력 프로파일을 가져옵니다."""
        profile = self.profile_manager.get_profile(self.default_output_profile)
        if not profile:
            profile = self.profile_manager.get_default_profile()
        return profile
    
    def read_image_with_colorspace(self, input_path: str, 
                              target_profile_name: Optional[str] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """이미지를 로드하고 지정된 색 공간으로 변환합니다."""
        self.logger.debug(f"이미지 로드 및 색 공간 변환: {input_path}")
        
        try:
            # 이미지 열기
            input_file = oiio.ImageInput.open(input_path)
            if not input_file:
                self.logger.error(f"이미지 열기 실패: {input_path}")
                return None, {"error": "이미지 열기 실패"}
            
            try:
                # 이미지 스펙 확인
                spec = input_file.spec()
                
                # 입력 색 프로파일 감지
                source_profile = self.detect_image_profile(input_path)
                if not source_profile:
                    source_profile = self.get_default_input_profile()
                
                # 타겟 색 프로파일 설정
                if target_profile_name:
                    target_profile = self.get_profile(target_profile_name)
                    if not target_profile:
                        self.logger.warning(f"지정된 프로파일을 찾을 수 없음: {target_profile_name}, 기본값 사용")
                        target_profile = self.get_default_output_profile()
                else:
                    target_profile = source_profile
                
                # 이미지 데이터 로드
                pixels = input_file.read_image()
                if pixels is None:
                    self.logger.error(f"이미지 데이터 읽기 실패: {input_path}")
                    return None, {"error": "이미지 데이터 읽기 실패"}
                
                # 색 공간 변환
                if source_profile.name != target_profile.name:
                    self.logger.debug(f"색 공간 변환: {source_profile.name} → {target_profile.name}")
                    pixels = self.transform.convert_colorspace(pixels, source_profile, target_profile)
                
                # 메타데이터 반환
                metadata = {
                    "width": spec.width,
                    "height": spec.height,
                    "channels": spec.nchannels,
                    "source_profile": source_profile.name,
                    "target_profile": target_profile.name,
                    "format": str(spec.format)
                }
                
                return pixels, metadata
                
            finally:
                input_file.close()
                
        except Exception as e:
            self.logger.error(f"이미지 로드 중 오류: {str(e)}")
            return None, {"error": f"이미지 로드 중 오류: {str(e)}"}
    
    def write_image_with_colorspace(self, output_path: str, pixels: np.ndarray,
                              metadata: Dict, output_profile_name: Optional[str] = None) -> bool:
        """이미지 데이터를 지정된 색 공간으로 변환하여 저장합니다."""
        self.logger.debug(f"이미지 저장 및 색 공간 변환: {output_path}")
        
        try:
            # 현재 색 공간 확인
            current_profile_name = metadata.get("target_profile", self.default_input_profile)
            current_profile = self.get_profile(current_profile_name)
            if not current_profile:
                current_profile = self.get_default_input_profile()
            
            # 출력 색 프로파일 설정
            if output_profile_name:
                output_profile = self.get_profile(output_profile_name)
                if not output_profile:
                    self.logger.warning(f"지정된 출력 프로파일을 찾을 수 없음: {output_profile_name}, 기본값 사용")
                    output_profile = self.get_default_output_profile()
            else:
                output_profile = self.get_default_output_profile()
            
            # 출력 이미지 픽셀 데이터
            output_pixels = pixels
            
            # 색 공간 변환 필요 시 수행
            if current_profile.name != output_profile.name:
                self.logger.debug(f"색 공간 변환 (출력용): {current_profile.name} → {output_profile.name}")
                output_pixels = self.transform.convert_colorspace(pixels, current_profile, output_profile)
            
            # 출력 형식 설정
            spec = oiio.ImageSpec()
            spec.width = metadata["width"]
            spec.height = metadata["height"]
            spec.nchannels = metadata["channels"]
            
            # 색 공간 정보 추가
            spec.attribute("oiio:ColorSpace", output_profile.name)
            
            # 출력 이미지 생성
            output_ext = os.path.splitext(output_path)[1].lower()
            output_file = oiio.ImageOutput.create(output_path)
            if not output_file:
                self.logger.error(f"출력 이미지 생성 실패: {output_path}")
                return False
            
            try:
                # 이미지 쓰기
                success = output_file.open(output_path, spec)
                if not success:
                    self.logger.error(f"출력 파일 열기 실패: {output_path}")
                    return False
                
                success = output_file.write_image(output_pixels)
                if not success:
                    self.logger.error(f"이미지 데이터 쓰기 실패: {output_path}")
                    return False
                
                return True
                
            finally:
                output_file.close()
                
        except Exception as e:
            self.logger.error(f"이미지 저장 중 오류: {str(e)}")
            return False
    
    def process_hdr_to_ldr(self, hdr_data: np.ndarray, 
                          method: Union[str, ToneMapMethod] = ToneMapMethod.REINHARD,
                          exposure: float = 1.0, 
                          gamma: float = 2.2) -> np.ndarray:
        """HDR 이미지 데이터를 LDR로 변환합니다."""
        # 메서드가 문자열로 주어진 경우 Enum으로 변환
        if isinstance(method, str):
            method_enum = None
            for tm in ToneMapMethod:
                if tm.value == method:
                    method_enum = tm
                    break
            
            if method_enum is None:
                self.logger.warning(f"알 수 없는 톤 매핑 방식: {method}, 기본값 사용")
                method_enum = ToneMapMethod.REINHARD
        else:
            method_enum = method
        
        # 톤 매핑 적용
        return self.transform.tone_map(hdr_data, method_enum, exposure, gamma)
    
    def apply_color_adjustments(self, data: np.ndarray, 
                             brightness: float = 0.0,
                             contrast: float = 0.0,
                             saturation: float = 0.0,
                             exposure_stops: float = 0.0) -> np.ndarray:
        """이미지 데이터에 여러 색상 조정을 적용합니다."""
        result = data.copy()
        
        # 노출 조정 (가장 먼저 적용)
        if exposure_stops != 0.0:
            result = self.transform.adjust_exposure(result, exposure_stops)
        
        # 밝기 및 대비 조정
        if brightness != 0.0 or contrast != 0.0:
            result = self.transform.adjust_brightness_contrast(result, brightness, contrast)
        
        # 채도 조정
        if saturation != 0.0:
            result = self.transform.adjust_saturation(result, saturation)
        
        return result 