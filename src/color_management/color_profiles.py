"""
색 프로파일 관리 모듈

이미지의 색 프로파일을 관리하고 변환하는 기능을 제공합니다.
주요 색 공간: sRGB, Adobe RGB, ProPhoto RGB, Linear RGB, Linear sRGB 등
"""

import os
import numpy as np
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
import OpenImageIO as oiio
from src.services.log_service import LogService

class ColorSpaceType(Enum):
    """색 공간 타입 정의"""
    SRGB = auto()
    ADOBE_RGB = auto()
    PROPHOTO_RGB = auto()
    LINEAR_RGB = auto()
    LINEAR_SRGB = auto()
    REC709 = auto()
    REC2020 = auto()
    ACES = auto()
    CUSTOM = auto()
    UNKNOWN = auto()
    
    def __str__(self):
        return self.name.replace('_', ' ')
    
    @classmethod
    def from_string(cls, name: str) -> 'ColorSpaceType':
        """문자열에서 색 공간 타입을 반환합니다."""
        name = name.upper().replace(' ', '_')
        try:
            return cls[name]
        except KeyError:
            return cls.UNKNOWN

@dataclass
class ColorProfile:
    """색 프로파일 정보를 저장하는 클래스"""
    name: str
    space_type: ColorSpaceType
    description: str = ""
    primaries: Optional[Dict[str, Tuple[float, float]]] = None  # (x, y) 좌표
    white_point: Optional[Tuple[float, float]] = None  # 백색점 (x, y)
    gamma: float = 2.2  # 감마 값
    is_linear: bool = False
    is_hdr: bool = False
    icc_path: Optional[str] = None  # ICC 프로파일 경로
    
    @property
    def display_name(self) -> str:
        """사용자에게 표시할 이름을 반환합니다."""
        if self.is_linear and "Linear" not in self.name:
            return f"Linear {self.name}"
        return self.name
    
    def to_dict(self) -> Dict:
        """프로파일 정보를 딕셔너리로 변환합니다."""
        return {
            "name": self.name,
            "space_type": self.space_type.name,
            "description": self.description,
            "primaries": self.primaries,
            "white_point": self.white_point,
            "gamma": self.gamma,
            "is_linear": self.is_linear,
            "is_hdr": self.is_hdr,
            "icc_path": self.icc_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ColorProfile':
        """딕셔너리에서 프로파일 객체를 생성합니다."""
        space_type = ColorSpaceType.from_string(data["space_type"])
        return cls(
            name=data["name"],
            space_type=space_type,
            description=data.get("description", ""),
            primaries=data.get("primaries"),
            white_point=data.get("white_point"),
            gamma=data.get("gamma", 2.2),
            is_linear=data.get("is_linear", False),
            is_hdr=data.get("is_hdr", False),
            icc_path=data.get("icc_path")
        )

class ColorProfileManager:
    """색 프로파일 관리 클래스"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ColorProfileManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """초기화 메서드"""
        self.logger = LogService()
        self.profiles: Dict[str, ColorProfile] = {}
        self._load_default_profiles()
        
    def _load_default_profiles(self):
        """기본 색 프로파일들을 로드합니다."""
        # sRGB 프로파일
        self.add_profile(ColorProfile(
            name="sRGB",
            space_type=ColorSpaceType.SRGB,
            description="Standard RGB color space (IEC 61966-2-1)",
            primaries={
                "red": (0.64, 0.33),
                "green": (0.30, 0.60),
                "blue": (0.15, 0.06)
            },
            white_point=(0.3127, 0.3290),  # D65
            gamma=2.2,
            is_linear=False,
            is_hdr=False
        ))
        
        # Linear sRGB 프로파일
        self.add_profile(ColorProfile(
            name="Linear sRGB",
            space_type=ColorSpaceType.LINEAR_SRGB,
            description="Linear version of sRGB color space",
            primaries={
                "red": (0.64, 0.33),
                "green": (0.30, 0.60),
                "blue": (0.15, 0.06)
            },
            white_point=(0.3127, 0.3290),  # D65
            gamma=1.0,
            is_linear=True,
            is_hdr=False
        ))
        
        # Adobe RGB 프로파일
        self.add_profile(ColorProfile(
            name="Adobe RGB",
            space_type=ColorSpaceType.ADOBE_RGB,
            description="Adobe RGB (1998) color space",
            primaries={
                "red": (0.64, 0.33),
                "green": (0.21, 0.71),
                "blue": (0.15, 0.06)
            },
            white_point=(0.3127, 0.3290),  # D65
            gamma=2.2,
            is_linear=False,
            is_hdr=False
        ))
        
        # ProPhoto RGB 프로파일
        self.add_profile(ColorProfile(
            name="ProPhoto RGB",
            space_type=ColorSpaceType.PROPHOTO_RGB,
            description="ProPhoto RGB color space (ROMM RGB)",
            primaries={
                "red": (0.7347, 0.2653),
                "green": (0.1596, 0.8404),
                "blue": (0.0366, 0.0001)
            },
            white_point=(0.3457, 0.3585),  # D50
            gamma=1.8,
            is_linear=False,
            is_hdr=True
        ))
        
        # Rec.709 프로파일
        self.add_profile(ColorProfile(
            name="Rec.709",
            space_type=ColorSpaceType.REC709,
            description="ITU-R Recommendation BT.709",
            primaries={
                "red": (0.64, 0.33),
                "green": (0.30, 0.60),
                "blue": (0.15, 0.06)
            },
            white_point=(0.3127, 0.3290),  # D65
            gamma=2.2,
            is_linear=False,
            is_hdr=False
        ))
        
        # Rec.2020 프로파일
        self.add_profile(ColorProfile(
            name="Rec.2020",
            space_type=ColorSpaceType.REC2020,
            description="ITU-R Recommendation BT.2020 for UHDTV",
            primaries={
                "red": (0.708, 0.292),
                "green": (0.170, 0.797),
                "blue": (0.131, 0.046)
            },
            white_point=(0.3127, 0.3290),  # D65
            gamma=2.2,
            is_linear=False,
            is_hdr=True
        ))
        
        # ACES 프로파일
        self.add_profile(ColorProfile(
            name="ACES",
            space_type=ColorSpaceType.ACES,
            description="Academy Color Encoding System",
            primaries={
                "red": (0.7347, 0.2653),
                "green": (0.0000, 1.0000),
                "blue": (0.0001, -0.0770)
            },
            white_point=(0.32168, 0.33767),  # D60
            gamma=1.0,
            is_linear=True,
            is_hdr=True
        ))
        
        self.logger.debug(f"기본 색 프로파일 {len(self.profiles)}개 로드 완료")
    
    def add_profile(self, profile: ColorProfile):
        """프로파일을 추가합니다."""
        self.profiles[profile.name] = profile
        
    def get_profile(self, name: str) -> Optional[ColorProfile]:
        """이름으로 프로파일을 조회합니다."""
        return self.profiles.get(name)
    
    def get_all_profiles(self) -> List[ColorProfile]:
        """모든 프로파일 목록을 반환합니다."""
        return list(self.profiles.values())
    
    def get_profiles_by_type(self, space_type: ColorSpaceType) -> List[ColorProfile]:
        """특정 유형의 프로파일만 반환합니다."""
        return [p for p in self.profiles.values() if p.space_type == space_type]
    
    def get_default_profile(self) -> ColorProfile:
        """기본 프로파일(sRGB)을 반환합니다."""
        return self.get_profile("sRGB")
    
    def detect_profile_from_image(self, image_path: str) -> Optional[ColorProfile]:
        """이미지 파일에서 색 프로파일을 감지합니다."""
        try:
            input_file = oiio.ImageInput.open(image_path)
            if not input_file:
                self.logger.error(f"이미지 열기 실패: {image_path}")
                return None
            
            try:
                spec = input_file.spec()
                
                # ICC 프로파일 체크
                if "ICCProfile" in spec.extra_attribs:
                    # TODO: ICC 프로파일 파싱 및 분석
                    self.logger.debug(f"ICC 프로파일 발견: {image_path}")
                    return None  # 현재는 미구현
                
                # 색 공간 정보 확인
                if "oiio:ColorSpace" in spec.extra_attribs:
                    color_space = spec.extra_attribs["oiio:ColorSpace"]
                    self.logger.debug(f"이미지 색 공간 정보: {color_space}")
                    
                    # 색 공간에 따른 프로파일 반환
                    if "srgb" in color_space.lower():
                        return self.get_profile("sRGB")
                    elif "linear" in color_space.lower():
                        return self.get_profile("Linear sRGB")
                    elif "adobe" in color_space.lower():
                        return self.get_profile("Adobe RGB")
                    elif "rec709" in color_space.lower():
                        return self.get_profile("Rec.709")
                    elif "rec2020" in color_space.lower():
                        return self.get_profile("Rec.2020")
                    elif "aces" in color_space.lower():
                        return self.get_profile("ACES")
                
                # 포맷 기반 추정
                ext = os.path.splitext(image_path)[1].lower()
                if ext in ['.exr', '.hdr']:
                    return self.get_profile("Linear sRGB")
                elif ext in ['.tiff', '.tif']:
                    # TIFF는 보통 Adobe RGB 많이 사용
                    return self.get_profile("Adobe RGB")
                
                # 기본값 반환
                return self.get_default_profile()
                
            finally:
                input_file.close()
                
        except Exception as e:
            self.logger.error(f"프로파일 감지 중 오류: {str(e)}")
            return self.get_default_profile() 