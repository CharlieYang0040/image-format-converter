import OpenImageIO as oiio
import os
from typing import Dict, List, Tuple, Any
from src.converters.base_converter import BaseConverter
from src.utils.debug.debug_utils import get_detailed_error_info, format_error_for_log

class OIIOConverter(BaseConverter):
    """OpenImageIO 라이브러리를 사용한 이미지 변환기"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = {
            'PNG': '.png',
            'JPEG': '.jpg',
            'TIFF': '.tif',
            'EXR': '.exr',
            'BMP': '.bmp',
            'HDR': '.hdr'
        }
    
    def get_supported_formats(self) -> List[str]:
        """지원되는 이미지 포맷 목록을 반환합니다."""
        formats = list(self.supported_formats.keys())
        self.logger.debug(f"지원되는 포맷 목록: {formats}")
        return formats
    
    def convert_image(self, input_path: str, output_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        이미지를 변환합니다.
        
        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로
            
        Returns:
            (성공 여부, 메시지, 추가 정보) 튜플
        """
        self.logger.info(f"이미지 변환 시작: {input_path} -> {output_path}")
        input_image = None
        output_image = None
        debug_info = {}
        
        try:
            # 입력 이미지 존재 확인
            if not os.path.exists(input_path):
                error_msg = f"입력 파일이 존재하지 않습니다: {input_path}"
                self.logger.error(error_msg)
                return False, error_msg, {"error_type": "FileNotFound"}
                
            # 출력 디렉토리 생성
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    error_msg = f"출력 디렉토리 생성 실패: {error_info['message']}"
                    self.logger.error(format_error_for_log(error_info))
                    return False, error_msg, {"error_info": error_info}
            
            # 입력 이미지 열기
            input_image = oiio.ImageInput.open(input_path)
            if not input_image:
                error_msg = f"입력 이미지를 열 수 없습니다: {input_path}"
                self.logger.error(error_msg)
                error_details = oiio.geterror()  # OpenImageIO 에러 상세 정보 가져오기
                debug_info = {"oiio_error": error_details}
                self.logger.error(f"OIIO 에러 상세: {error_details}")
                return False, error_msg, debug_info
            
            # 입력 이미지 스펙 확인
            spec = input_image.spec()
            self.logger.debug(f"입력 이미지 스펙: {spec.width}x{spec.height}, 채널: {spec.nchannels}, 포맷: {spec.format}")
            debug_info["input_spec"] = {
                "width": spec.width,
                "height": spec.height,
                "channels": spec.nchannels,
                "format": str(spec.format)
            }
            
            # 출력 이미지 생성
            output_image = oiio.ImageOutput.create(output_path)
            if not output_image:
                error_msg = f"출력 이미지를 생성할 수 없습니다: {output_path}"
                self.logger.error(error_msg)
                error_details = oiio.geterror()
                debug_info = {"oiio_error": error_details}
                self.logger.error(f"OIIO 에러 상세: {error_details}")
                return False, error_msg, debug_info
            
            # 이미지 복사 및 변환
            pixels = input_image.read_image()
            if pixels is None:
                error_msg = "이미지 데이터를 읽을 수 없습니다."
                self.logger.error(error_msg)
                error_details = oiio.geterror()
                debug_info = {"oiio_error": error_details}
                self.logger.error(f"OIIO 에러 상세: {error_details}")
                return False, error_msg, debug_info
                
            success = output_image.open(output_path, spec) and output_image.write_image(pixels)
            
            if success:
                self.logger.info(f"이미지 변환 완료: {output_path}")
                return True, "이미지 변환이 완료되었습니다.", debug_info
            else:
                error_msg = "이미지 변환 중 오류가 발생했습니다."
                error_details = oiio.geterror()
                debug_info = {"oiio_error": error_details}
                self.logger.error(f"{error_msg} 상세: {error_details}")
                return False, error_msg, debug_info
                
        except Exception as e:
            error_info = get_detailed_error_info(e)
            error_msg = f"이미지 변환 중 오류 발생: {error_info['message']}"
            self.logger.error(format_error_for_log(error_info))
            return False, error_msg, {"error_info": error_info}
            
        finally:
            # 리소스 정리
            if input_image:
                try:
                    input_image.close()
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    self.logger.error(f"입력 이미지 리소스 정리 중 오류: {format_error_for_log(error_info)}")
                    
            if output_image:
                try:
                    output_image.close()
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    self.logger.error(f"출력 이미지 리소스 정리 중 오류: {format_error_for_log(error_info)}")
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
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
                error_details = oiio.geterror()
                self.logger.error(f"{error_msg}: {image_path} 상세: {error_details}")
                return {"error": error_msg, "oiio_error": error_details}
            
            spec = input_image.spec()
            file_size = os.path.getsize(image_path)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            
            info = {
                "width": spec.width,
                "height": spec.height,
                "channels": spec.nchannels,
                "format": str(spec.format),
                "file_size_bytes": file_size,
                "file_size_mb": file_size_mb,
                "file_extension": os.path.splitext(image_path)[1].lower()
            }
            
            # 추가 메타데이터 정보 수집
            metadata = {}
            for i in range(len(spec.extra_attribs)):
                attr = spec.extra_attribs[i]
                metadata[attr.name] = attr.value
                
            if metadata:
                info["metadata"] = metadata
            
            self.logger.debug(f"이미지 정보: {info}")
            return info
            
        except Exception as e:
            error_info = get_detailed_error_info(e)
            error_msg = f"이미지 정보 조회 중 오류 발생: {error_info['message']}"
            self.logger.error(format_error_for_log(error_info))
            return {"error": error_msg, "error_info": error_info}
            
        finally:
            if input_image:
                try:
                    input_image.close()
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    self.logger.error(f"이미지 리소스 정리 중 오류: {format_error_for_log(error_info)}") 