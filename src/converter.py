import OpenImageIO as oiio
import os
from typing import List, Tuple, Dict, Any
from src.services.log_service import LogService
import traceback
from src.converters.converter_factory import ConverterFactory

class ImageConverter:
    """이미지 변환 인터페이스 클래스"""
    
    def __init__(self):
        self.logger = LogService()
        self.factory = ConverterFactory()
        self.converter = self.factory.get_converter()
        self.supported_formats = self.converter.supported_formats
    
    def get_supported_formats(self) -> List[str]:
        """지원되는 이미지 포맷 목록을 반환합니다."""
        return self.converter.get_supported_formats()
    
    def convert_image(self, input_path: str, output_path: str) -> Tuple[bool, str]:
        """
        이미지를 변환합니다.
        
        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로
            
        Returns:
            (성공 여부, 메시지) 튜플
        """
        self.logger.info(f"이미지 변환 시작: {input_path} -> {output_path}")
        input_image = None
        output_image = None
        
        try:
            # 입력 이미지 존재 확인
            if not os.path.exists(input_path):
                error_msg = f"입력 파일이 존재하지 않습니다: {input_path}"
                self.logger.error(error_msg)
                return False, error_msg
                
            # 출력 디렉토리 생성
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except Exception as e:
                    error_msg = f"출력 디렉토리 생성 실패: {str(e)}"
                    self.logger.error(error_msg)
                    return False, error_msg
            
            # 입력 이미지 열기
            input_image = oiio.ImageInput.open(input_path)
            if not input_image:
                error_msg = f"입력 이미지를 열 수 없습니다: {input_path}"
                self.logger.error(error_msg)
                return False, error_msg
            
            # 입력 이미지 스펙 확인
            spec = input_image.spec()
            self.logger.debug(f"입력 이미지 스펙: {spec}")
            
            # 출력 이미지 생성
            output_image = oiio.ImageOutput.create(output_path)
            if not output_image:
                error_msg = f"출력 이미지를 생성할 수 없습니다: {output_path}"
                self.logger.error(error_msg)
                return False, error_msg
            
            # 이미지 복사 및 변환
            success, message, debug_info = self.converter.convert_image(input_image, output_image)
            
            if success:
                self.logger.info(f"이미지 변환 완료: {output_path}")
                return True, message
            else:
                error_msg = "이미지 변환 중 오류가 발생했습니다."
                self.logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"오류 발생: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            return False, error_msg
            
        finally:
            # 리소스 정리
            if input_image:
                try:
                    input_image.close()
                except Exception as e:
                    self.logger.error(f"입력 이미지 리소스 정리 중 오류: {str(e)}")
                    
            if output_image:
                try:
                    output_image.close()
                except Exception as e:
                    self.logger.error(f"출력 이미지 리소스 정리 중 오류: {str(e)}")
    
    def get_image_info(self, image_path: str) -> dict:
        """
        이미지의 기본 정보를 반환합니다.
        
        Args:
            image_path: 이미지 경로
            
        Returns:
            이미지 정보를 담은 딕셔너리
        """
        self.logger.debug(f"이미지 정보 조회: {image_path}")
        input_image = None
        
        try:
            if not os.path.exists(image_path):
                error_msg = f"이미지 파일이 존재하지 않습니다: {image_path}"
                self.logger.error(error_msg)
                return {"error": error_msg}
                
            input_image = oiio.ImageInput.open(image_path)
            if not input_image:
                error_msg = "이미지를 열 수 없습니다."
                self.logger.error(f"{error_msg}: {image_path}")
                return {"error": error_msg}
            
            spec = input_image.spec()
            info = {
                "width": spec.width,
                "height": spec.height,
                "channels": spec.nchannels,
                "format": spec.format,
                "pixel_type": str(spec.format),
                "file_size": os.path.getsize(image_path)
            }
            
            self.logger.debug(f"이미지 정보: {info}")
            return info
            
        except Exception as e:
            error_msg = f"이미지 정보 조회 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
            self.logger.error(error_msg)
            return {"error": error_msg}
            
        finally:
            if input_image:
                try:
                    input_image.close()
                except Exception as e:
                    self.logger.error(f"이미지 리소스 정리 중 오류: {str(e)}")