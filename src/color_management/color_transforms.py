"""
색 변환 알고리즘 모듈

이미지 데이터의 색 공간 변환과 색상 보정을 위한 알고리즘을 제공합니다.
- 색 공간 변환 행렬
- 감마 변환
- 톤 매핑
- 색상 조정 (밝기, 대비, 채도 등)
"""

import numpy as np
from enum import Enum
from typing import Dict, List, Tuple, Optional, Union, Callable
import OpenImageIO as oiio
from src.services.log_service import LogService
from .color_profiles import ColorProfile

class ToneMapMethod(Enum):
    """톤 매핑 방식"""
    SIMPLE = "단순 매핑"  # 선형 스케일링
    REINHARD = "Reinhard"  # Reinhard 톤 매핑
    FILMIC = "Filmic"  # Filmic 톤 매핑
    ACES = "ACES"  # Academy Color Encoding System


class ColorTransform:
    """색 변환 알고리즘 클래스"""
    
    def __init__(self):
        self.logger = LogService()
    
    def apply_gamma(self, data: np.ndarray, gamma: float) -> np.ndarray:
        """감마 변환을 적용합니다."""
        if gamma == 1.0:
            return data
        
        # 양수 값에만 감마 적용
        result = data.copy()
        mask = result > 0
        result[mask] = np.power(result[mask], 1.0 / gamma)
        return result
    
    def remove_gamma(self, data: np.ndarray, gamma: float) -> np.ndarray:
        """감마를 제거하고 선형화합니다."""
        if gamma == 1.0:
            return data
        
        # 양수 값에만 감마 적용
        result = data.copy()
        mask = result > 0
        result[mask] = np.power(result[mask], gamma)
        return result
    
    def srgb_to_linear(self, data: np.ndarray) -> np.ndarray:
        """sRGB에서 Linear RGB로 변환합니다 (정확한 sRGB 변환식 사용)."""
        result = data.copy()
        
        # sRGB 변환 공식
        mask_lo = result <= 0.04045
        mask_hi = ~mask_lo
        
        # 낮은 값은 선형 스케일링
        result[mask_lo] = result[mask_lo] / 12.92
        
        # 높은 값은 지수 함수 사용
        result[mask_hi] = np.power((result[mask_hi] + 0.055) / 1.055, 2.4)
        
        return result
    
    def linear_to_srgb(self, data: np.ndarray) -> np.ndarray:
        """Linear RGB에서 sRGB로 변환합니다 (정확한 sRGB 변환식 사용)."""
        result = data.copy()
        
        # sRGB 변환 공식 (역방향)
        mask_lo = result <= 0.0031308
        mask_hi = ~mask_lo
        
        # 낮은 값은 선형 스케일링
        result[mask_lo] = 12.92 * result[mask_lo]
        
        # 높은 값은 지수 함수 사용
        result[mask_hi] = 1.055 * np.power(result[mask_hi], 1/2.4) - 0.055
        
        return result
    
    def rgb_matrix_transform(self, data: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """RGB 색상에 변환 행렬을 적용합니다."""
        # 3채널 이상 가정
        if data.shape[-1] < 3:
            self.logger.warning("RGB 변환을 위해 최소 3채널이 필요합니다.")
            return data
        
        # 4채널(RGBA)인 경우 알파 채널 분리
        has_alpha = data.shape[-1] == 4
        if has_alpha:
            rgb = data[..., :3]
            alpha = data[..., 3:4]
        else:
            rgb = data
        
        # RGB 변환 적용
        shape = rgb.shape
        pixels = rgb.reshape(-1, 3)
        transformed = np.dot(pixels, matrix.T)
        result_rgb = transformed.reshape(shape)
        
        # 알파 채널 다시 결합
        if has_alpha:
            return np.concatenate([result_rgb, alpha], axis=-1)
        return result_rgb
    
    def convert_colorspace(self, data: np.ndarray, 
                           from_profile: ColorProfile, 
                           to_profile: ColorProfile) -> np.ndarray:
        """한 색 공간에서 다른 색 공간으로 이미지 데이터를 변환합니다."""
        self.logger.debug(f"색 공간 변환: {from_profile.name} → {to_profile.name}")
        
        # 동일한 프로파일인 경우 그대로 반환
        if from_profile.name == to_profile.name:
            return data
        
        result = data.copy()
        
        # Step 1: 소스가 non-linear면 선형화
        if not from_profile.is_linear:
            if from_profile.space_type.name == "SRGB":
                result = self.srgb_to_linear(result)
            else:
                result = self.remove_gamma(result, from_profile.gamma)
        
        # Step 2: 색 공간 변환 (나중에 구현할 매트릭스 변환)
        # 현재는 색 공간 변환 매트릭스 미구현으로 건너뜀
        
        # Step 3: 타겟이 non-linear면 감마 적용
        if not to_profile.is_linear:
            if to_profile.space_type.name == "SRGB":
                result = self.linear_to_srgb(result)
            else:
                result = self.apply_gamma(result, to_profile.gamma)
        
        return result
    
    def tone_map(self, hdr_data: np.ndarray, method: ToneMapMethod = ToneMapMethod.REINHARD,
                exposure: float = 1.0, gamma: float = 2.2) -> np.ndarray:
        """HDR 이미지 데이터를 LDR로 톤 매핑합니다."""
        self.logger.debug(f"톤 매핑 적용: {method.value}, 노출={exposure}, 감마={gamma}")
        
        # 노출 조정
        data = hdr_data * exposure
        
        # 톤 매핑 방식에 따라 처리
        if method == ToneMapMethod.SIMPLE:
            # 단순 스케일링
            max_val = np.max(data)
            if max_val > 1.0:
                data = data / max_val
        
        elif method == ToneMapMethod.REINHARD:
            # Reinhard 톤 매핑
            data = data / (1.0 + data)
        
        elif method == ToneMapMethod.FILMIC:
            # Filmic 톤 매핑 (단순화된 버전)
            # John Hable's filmic curve
            a = 0.22
            b = 0.30
            c = 0.10
            d = 0.20
            e = 0.01
            f = 0.30
            
            def filmic_curve(x):
                return ((x * (a * x + c * b) + d * e) / (x * (a * x + b) + d * f)) - e/f
            
            # 정규화를 위한 화이트포인트 
            white = 11.2
            white_scale = filmic_curve(white)
            
            # 데이터가 4채널(RGBA)인 경우 알파 채널 분리
            has_alpha = data.shape[-1] == 4
            if has_alpha:
                rgb = data[..., :3]
                alpha = data[..., 3:4]
            else:
                rgb = data
            
            # 각 채널에 filmic curve 적용
            rgb = filmic_curve(rgb) / white_scale
            
            # 알파 채널 결합
            if has_alpha:
                data = np.concatenate([rgb, alpha], axis=-1)
            else:
                data = rgb
        
        elif method == ToneMapMethod.ACES:
            # ACES filmic tone mapping curve
            a = 2.51
            b = 0.03
            c = 2.43
            d = 0.59
            e = 0.14
            
            # 데이터가 4채널(RGBA)인 경우 알파 채널 분리
            has_alpha = data.shape[-1] == 4
            if has_alpha:
                rgb = data[..., :3]
                alpha = data[..., 3:4]
            else:
                rgb = data
            
            # ACES tone mapping 적용
            rgb = (rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e)
            
            # 클리핑
            rgb = np.clip(rgb, 0.0, 1.0)
            
            # 알파 채널 결합
            if has_alpha:
                data = np.concatenate([rgb, alpha], axis=-1)
            else:
                data = rgb
        
        # 감마 적용 (sRGB 변환이 더 정확하지만 단순화를 위해 감마만 적용)
        result = self.apply_gamma(data, gamma)
        
        # 최종 결과 클리핑
        return np.clip(result, 0.0, 1.0)
    
    def adjust_brightness_contrast(self, data: np.ndarray, brightness: float = 0.0, 
                              contrast: float = 0.0) -> np.ndarray:
        """이미지의 밝기와 대비를 조정합니다.
        
        Args:
            data: 이미지 데이터 배열
            brightness: 밝기 조정값 (-1.0 ~ 1.0)
            contrast: 대비 조정값 (-1.0 ~ 1.0)
            
        Returns:
            조정된 이미지 데이터
        """
        # 데이터가 4채널(RGBA)인 경우 알파 채널 분리
        has_alpha = data.shape[-1] == 4
        if has_alpha:
            rgb = data[..., :3].copy()
            alpha = data[..., 3:4]
        else:
            rgb = data.copy()
        
        # 밝기 조정
        if brightness != 0:
            # -1 ~ 1 범위를 적절한 계수로 변환
            factor = brightness * 0.5  # -0.5 ~ 0.5 범위로 조정
            rgb += factor
        
        # 대비 조정
        if contrast != 0:
            # -1 ~ 1 범위를 적절한 계수로 변환
            factor = 1.0 + contrast  # 0 ~ 2 범위로 조정
            # 중간값(0.5)을 기준으로 대비 조정
            rgb = (rgb - 0.5) * factor + 0.5
        
        # 클리핑
        rgb = np.clip(rgb, 0.0, 1.0)
        
        # 알파 채널 결합
        if has_alpha:
            return np.concatenate([rgb, alpha], axis=-1)
        return rgb
    
    def adjust_saturation(self, data: np.ndarray, saturation: float = 0.0) -> np.ndarray:
        """이미지의 채도를 조정합니다.
        
        Args:
            data: 이미지 데이터 배열
            saturation: 채도 조정값 (-1.0 ~ 1.0)
            
        Returns:
            조정된 이미지 데이터
        """
        if saturation == 0:
            return data
        
        # 데이터가 4채널(RGBA)인 경우 알파 채널 분리
        has_alpha = data.shape[-1] == 4
        if has_alpha:
            rgb = data[..., :3].copy()
            alpha = data[..., 3:4]
        else:
            rgb = data.copy()
        
        # 그레이스케일 변환 (휘도)
        # BT.709 휘도 계수
        gray = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
        gray = gray[..., np.newaxis]
        
        # -1 ~ 1 범위를 적절한 계수로 변환
        factor = 1.0 + saturation
        
        # 채도 조정: 컬러와 그레이스케일 사이를 보간
        rgb = rgb * factor + gray * (1 - factor)
        
        # 클리핑
        rgb = np.clip(rgb, 0.0, 1.0)
        
        # 알파 채널 결합
        if has_alpha:
            return np.concatenate([rgb, alpha], axis=-1)
        return rgb
    
    def adjust_exposure(self, data: np.ndarray, stops: float = 0.0) -> np.ndarray:
        """이미지의 노출을 조정합니다.
        
        Args:
            data: 이미지 데이터 배열
            stops: 노출 조정값 (EV, 일반적으로 -5 ~ 5 범위)
            
        Returns:
            조정된 이미지 데이터
        """
        if stops == 0:
            return data
        
        # 데이터가 4채널(RGBA)인 경우 알파 채널 분리
        has_alpha = data.shape[-1] == 4
        if has_alpha:
            rgb = data[..., :3].copy()
            alpha = data[..., 3:4]
        else:
            rgb = data.copy()
        
        # 노출 스톱을 곱셈 계수로 변환 (2의 거듭제곱)
        factor = np.power(2.0, stops)
        
        # 노출 조정
        rgb *= factor
        
        # 알파 채널 결합
        if has_alpha:
            return np.concatenate([rgb, alpha], axis=-1)
        return rgb 