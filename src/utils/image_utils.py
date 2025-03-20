import OpenImageIO as oiio
import numpy as np
from typing import Dict, Any, Tuple

class ImageFormatUtils:
    """이미지 포맷 변환에 필요한 유틸리티 함수 모음"""
    
    # 포맷 특성 정보
    FORMAT_PROPERTIES = {
        'PNG': {
            'extension': '.png',
            'has_alpha': True,
            'compression': 'lossless',
            'bit_depth': 8,
            'color_space': 'sRGB',
            'supports_metadata': True,
            'is_hdr': False
        },
        'JPEG': {
            'extension': '.jpg',
            'has_alpha': False,
            'compression': 'lossy',
            'bit_depth': 8,
            'color_space': 'sRGB',
            'supports_metadata': True,
            'is_hdr': False
        },
        'TIFF': {
            'extension': '.tif',
            'has_alpha': True,
            'compression': 'configurable',
            'bit_depth': 'variable',  # 8, 16, 32
            'color_space': 'variable',
            'supports_metadata': True,
            'is_hdr': False  # 가능하지만 기본은 SDR
        },
        'EXR': {
            'extension': '.exr',
            'has_alpha': True,
            'compression': 'lossless',
            'bit_depth': 'float',  # 16/32 bit float
            'color_space': 'linear',
            'supports_metadata': True,
            'is_hdr': True
        },
        'TGA': {
            'extension': '.tga',
            'has_alpha': True,
            'compression': 'variable',  # RLE 또는 무압축
            'bit_depth': 8,
            'color_space': 'sRGB',
            'supports_metadata': False,
            'is_hdr': False
        }
    }
    
    @staticmethod
    def is_hdr_format(format_name: str) -> bool:
        """HDR 포맷인지 여부를 반환합니다."""
        return ImageFormatUtils.FORMAT_PROPERTIES.get(format_name, {}).get('is_hdr', False)
    
    @staticmethod
    def has_alpha_support(format_name: str) -> bool:
        """알파 채널을 지원하는지 여부를 반환합니다."""
        return ImageFormatUtils.FORMAT_PROPERTIES.get(format_name, {}).get('has_alpha', False)
    
    @staticmethod
    def get_color_space(format_name: str) -> str:
        """해당 포맷의 기본 색공간을 반환합니다."""
        return ImageFormatUtils.FORMAT_PROPERTIES.get(format_name, {}).get('color_space', 'sRGB')
    
    @staticmethod
    def get_format_property(format_name: str, property_name: str, default=None) -> Any:
        """포맷의 특정 속성을 반환합니다."""
        return ImageFormatUtils.FORMAT_PROPERTIES.get(format_name, {}).get(property_name, default)
    
    @staticmethod
    def apply_tone_mapping(pixel_data: np.ndarray, 
                          exposure: float = 1.0, 
                          gamma: float = 2.2) -> np.ndarray:
        """
        HDR 이미지에 톤 매핑을 적용합니다.
        
        Args:
            pixel_data: 픽셀 데이터 배열
            exposure: 노출 조정 값
            gamma: 감마 값
            
        Returns:
            톤 매핑이 적용된 픽셀 데이터
        """
        # 채널 수 확인 (RGB 또는 RGBA)
        has_alpha = pixel_data.shape[2] == 4
        
        # 알파 채널 분리
        if has_alpha:
            rgb_data = pixel_data[:, :, :3]
            alpha = pixel_data[:, :, 3:4]
        else:
            rgb_data = pixel_data
            alpha = None
        
        # 노출 적용
        exposed = rgb_data * exposure
        
        # 간단한 Reinhard 톤 매핑 적용
        mapped = exposed / (exposed + 1.0)
        
        # 감마 보정 적용 (Linear to sRGB)
        gamma_corrected = np.power(mapped, 1.0 / gamma)
        
        # 값 범위 조정 (0-1)
        result = np.clip(gamma_corrected, 0, 1)
        
        # 알파 채널 재결합
        if has_alpha:
            result = np.concatenate([result, alpha], axis=2)
            
        return result
    
    @staticmethod
    def remove_alpha_channel(pixel_data: np.ndarray, background_color=(1, 1, 1)) -> np.ndarray:
        """
        알파 채널을 제거하고 배경색과 합성합니다.
        
        Args:
            pixel_data: 픽셀 데이터 배열 (RGBA)
            background_color: 배경색 (RGB)
            
        Returns:
            알파 채널이 제거된 픽셀 데이터 (RGB)
        """
        if pixel_data.shape[2] != 4:
            return pixel_data  # 이미 알파 채널이 없음
            
        rgb = pixel_data[:, :, :3]
        alpha = pixel_data[:, :, 3:4]
        
        # 배경색 생성
        bg = np.ones_like(rgb) * np.array(background_color)
        
        # 알파 합성
        alpha_expanded = np.repeat(alpha, 3, axis=2)
        composited = rgb * alpha_expanded + bg * (1 - alpha_expanded)
        
        return composited
    
    @staticmethod
    def adjust_bit_depth(spec: oiio.ImageSpec, target_format: str) -> oiio.ImageSpec:
        """
        대상 포맷에 맞게 비트 깊이를 조정합니다.
        
        Args:
            spec: 원본 이미지 스펙
            target_format: 대상 포맷 이름
            
        Returns:
            조정된 이미지 스펙
        """
        # 새로운 스펙 복사
        new_spec = oiio.ImageSpec(spec)
        
        # 대상 포맷의 비트 깊이 속성 가져오기
        bit_depth = ImageFormatUtils.get_format_property(target_format, 'bit_depth')
        
        # 비트 깊이 조정
        if bit_depth == 8:
            new_spec.format = oiio.UINT8
        elif bit_depth == 16:
            new_spec.format = oiio.UINT16
        elif bit_depth == 'float' or bit_depth == 32:
            new_spec.format = oiio.FLOAT
        
        return new_spec
    
    @staticmethod
    def get_optimal_compression(input_format: str, output_format: str) -> Dict[str, Any]:
        """
        입출력 포맷에 따른 최적의 압축 설정을 반환합니다.
        
        Args:
            input_format: 입력 포맷 이름
            output_format: 출력 포맷 이름
            
        Returns:
            압축 설정 딕셔너리
        """
        compression_settings = {}
        
        if output_format == "JPEG":
            # JPEG 압축 품질 설정 (0-100)
            compression_settings["quality"] = 90  # 기본값
            
            # HDR → JPEG 변환 시 더 높은 품질
            if ImageFormatUtils.is_hdr_format(input_format):
                compression_settings["quality"] = 95
                
        elif output_format == "PNG":
            # PNG 압축 레벨 (0-9)
            compression_settings["compressionlevel"] = 6  # 기본값
            
        elif output_format == "TIFF":
            # TIFF 압축 방식
            compression_settings["compression"] = "zip"  # Zip 압축
            
            # HDR → TIFF 변환 시
            if ImageFormatUtils.is_hdr_format(input_format):
                compression_settings["compression"] = "none"  # 무압축
                
        elif output_format == "EXR":
            # EXR 압축 방식
            compression_settings["compression"] = "zip"  # Zip 압축
            
        elif output_format == "TGA":
            # TGA 압축 여부
            compression_settings["rle"] = True  # RLE 압축 사용
        
        return compression_settings
    
    @staticmethod
    def get_conversion_settings(input_format: str, output_format: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        입출력 포맷에 따른 변환 설정을 반환합니다.
        
        Args:
            input_format: 입력 포맷 이름
            output_format: 출력 포맷 이름
            
        Returns:
            (전처리 설정, 후처리 설정) 튜플
        """
        pre_settings = {}
        post_settings = {}
        
        # HDR → LDR 변환 설정
        if ImageFormatUtils.is_hdr_format(input_format) and not ImageFormatUtils.is_hdr_format(output_format):
            pre_settings["apply_tone_mapping"] = True
            pre_settings["exposure"] = 1.0
            pre_settings["gamma"] = 2.2
        
        # LDR → HDR 변환 설정 (HDR 출력 형식 최적화)
        if not ImageFormatUtils.is_hdr_format(input_format) and ImageFormatUtils.is_hdr_format(output_format):
            # HDR 출력 시 float 형식으로 변환 보장
            post_settings["format"] = "float"
            
            # HDR은 일반적으로 linear 색 공간 사용
            post_settings["colorspace"] = "linear"
            
        # HDR → HDR 변환 설정
        if ImageFormatUtils.is_hdr_format(input_format) and ImageFormatUtils.is_hdr_format(output_format):
            # float 형식 보장
            post_settings["format"] = "float"
        
        # 알파 채널 처리
        if ImageFormatUtils.has_alpha_support(input_format) and not ImageFormatUtils.has_alpha_support(output_format):
            pre_settings["remove_alpha"] = True
            pre_settings["background_color"] = (1, 1, 1)  # 흰색 배경
        
        # 압축 설정
        post_settings.update(ImageFormatUtils.get_optimal_compression(input_format, output_format))
        
        return pre_settings, post_settings 