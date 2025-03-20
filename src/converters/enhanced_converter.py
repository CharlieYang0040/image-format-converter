import OpenImageIO as oiio
import os
import numpy as np
import time
from typing import Dict, List, Tuple, Any, Optional, Callable
from src.converters.base_converter import BaseConverter
from src.utils.debug.debug_utils import get_detailed_error_info, format_error_for_log
from src.utils.image_utils import ImageFormatUtils
from src.color_management import ColorManager, ToneMapMethod

class ConversionStage:
    """변환 단계를 정의하는 열거형 클래스"""
    INIT = 0        # 초기화
    LOAD = 1        # 이미지 로드
    ANALYZE = 2     # 이미지 분석
    COLOR = 3       # 색 공간 변환
    PROCESS = 4     # 이미지 처리
    SAVE = 5        # 이미지 저장
    COMPLETE = 6    # 완료
    
    @staticmethod
    def get_name(stage: int) -> str:
        """단계 이름 반환"""
        names = [
            "초기화",
            "이미지 로드",
            "이미지 분석",
            "색 공간 변환",
            "이미지 처리",
            "이미지 저장",
            "완료"
        ]
        if 0 <= stage < len(names):
            return names[stage]
        return "알 수 없음"

class EnhancedConverter(BaseConverter):
    """다양한 이미지 포맷 간 고품질 변환을 지원하는 변환기"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = {
            'PNG': '.png',
            'JPEG': '.jpg',
            'TIFF': '.tif',
            'EXR': '.exr',
            'TGA': '.tga'  # BMP와 HDR 포맷 제거
        }
        
        # 색 관리 모듈 초기화
        self.color_manager = ColorManager()
        
        # 진행 상황 보고용 콜백
        self._progress_callback = None
        self._start_time = 0
        
        self.logger.info("고급 이미지 변환기 (색 관리 지원) 초기화")
    
    def get_supported_formats(self) -> List[str]:
        """지원되는 이미지 포맷 목록을 반환합니다."""
        formats = list(self.supported_formats.keys())
        self.logger.debug(f"지원되는 포맷 목록: {formats}")
        return formats
    
    def set_progress_callback(self, callback: Callable[[int, float, Dict[str, Any]], None]):
        """진행 상황 보고를 위한 콜백 함수를 설정합니다.
        
        콜백 함수는 다음 매개변수를 받습니다:
        - stage: 현재 진행 중인 단계 (ConversionStage 상수)
        - progress: 현재 단계의 진행률 (0.0 ~ 1.0)
        - info: 추가 정보 딕셔너리
        """
        self._progress_callback = callback
    
    def _report_progress(self, stage: int, progress: float, **info):
        """진행 상황을 보고합니다."""
        # 경과 시간 계산
        elapsed = time.time() - self._start_time
        
        # 콜백 호출
        if self._progress_callback:
            info["elapsed_time"] = elapsed
            info["stage_name"] = ConversionStage.get_name(stage)
            self._progress_callback(stage, progress, info)

    def convert_image(self, input_path: str, output_path: str, options: Dict = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        이미지를 변환합니다.
        
        Args:
            input_path: 입력 이미지 경로
            output_path: 출력 이미지 경로
            options: 변환 옵션 (색 관리, 톤 매핑 등)
            
        Returns:
            (성공 여부, 메시지, 추가 정보) 튜플
        """
        self.logger.info(f"고급 이미지 변환 시작: {input_path} -> {output_path}")
        input_image = None
        debug_info = {}
        
        # 시작 시간 기록
        self._start_time = time.time()
        
        if options is None:
            options = {}
        
        # 초기화 단계 보고
        self._report_progress(ConversionStage.INIT, 0.0, message="변환 준비 중")
        
        try:
            # 입출력 포맷 결정
            input_ext = os.path.splitext(input_path)[1].lower()
            output_ext = os.path.splitext(output_path)[1].lower()
            
            input_format = None
            output_format = None
            
            # 확장자로 포맷 유추
            for format_name, ext in self.supported_formats.items():
                if ext.lower() == input_ext:
                    input_format = format_name
                if ext.lower() == output_ext:
                    output_format = format_name
                    
            if not input_format or not output_format:
                error_msg = f"지원되지 않는 이미지 포맷: 입력({input_ext}), 출력({output_ext})"
                self.logger.error(error_msg)
                self._report_progress(ConversionStage.INIT, 1.0, 
                                    message="오류 발생", error=error_msg)
                return False, error_msg, {"error_type": "UnsupportedFormat"}
            
            # 초기화 단계 완료
            self._report_progress(ConversionStage.INIT, 1.0, message="준비 완료",
                                input_format=input_format, output_format=output_format)
            
            # 입력 이미지 존재 확인
            if not os.path.exists(input_path):
                error_msg = f"입력 파일이 존재하지 않습니다: {input_path}"
                self.logger.error(error_msg)
                self._report_progress(ConversionStage.LOAD, 0.0, 
                                    message="오류 발생", error=error_msg)
                return False, error_msg, {"error_type": "FileNotFound"}
                
            # 출력 디렉토리 생성
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    self._report_progress(ConversionStage.INIT, 1.0, 
                                        message="출력 디렉토리 생성 완료")
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    error_msg = f"출력 디렉토리 생성 실패: {error_info['message']}"
                    self.logger.error(format_error_for_log(error_info))
                    self._report_progress(ConversionStage.INIT, 1.0, 
                                        message="오류 발생", error=error_msg)
                    return False, error_msg, {"error_info": error_info}
            
            # 색 관리 기능 사용 여부 확인
            use_color_management = options.get('use_color_management', True)
            
            if use_color_management:
                # 색 관리 설정 적용
                input_profile_name = options.get('input_profile')
                output_profile_name = options.get('output_profile')
                
                # 이미지 로드 단계 시작
                self._report_progress(ConversionStage.LOAD, 0.0, 
                                    message="이미지 파일 로드 중")
                
                # 색 관리 모듈로 이미지 로드
                pixels, metadata = self.color_manager.read_image_with_colorspace(input_path, input_profile_name)
                
                if pixels is None:
                    error_msg = f"이미지 로드 실패: {metadata.get('error', '알 수 없는 오류')}"
                    self.logger.error(error_msg)
                    self._report_progress(ConversionStage.LOAD, 1.0, 
                                        message="오류 발생", error=error_msg)
                    return False, error_msg, {"error_info": {"message": error_msg}}
                
                # 이미지 로드 완료
                self._report_progress(ConversionStage.LOAD, 1.0, 
                                    message="이미지 로드 완료",
                                    width=metadata["width"], 
                                    height=metadata["height"],
                                    channels=metadata["channels"])
                
                # 이미지 분석 단계
                self._report_progress(ConversionStage.ANALYZE, 0.0, 
                                    message="이미지 분석 중")
                
                # 디버그 정보에 색 프로파일 추가
                debug_info["source_profile"] = metadata.get('source_profile')
                debug_info["working_profile"] = metadata.get('target_profile')
                
                # 이미지 분석 완료
                self._report_progress(ConversionStage.ANALYZE, 1.0, 
                                    message="이미지 분석 완료",
                                    source_profile=metadata.get('source_profile'),
                                    format=metadata.get('format'))
                
                # 색 공간 변환 단계
                self._report_progress(ConversionStage.COLOR, 0.0, 
                                    message="색 공간 처리 중")
                
                # 색상 처리 적용
                pixels = self._apply_color_adjustments(pixels, metadata, input_format, output_format, options)
                
                # 색 공간 변환 완료
                self._report_progress(ConversionStage.COLOR, 1.0, 
                                    message="색 공간 처리 완료")
                
                # 이미지 처리 단계 (생략, 색상 조정에 포함)
                self._report_progress(ConversionStage.PROCESS, 0.0, 
                                    message="이미지 처리 중")
                self._report_progress(ConversionStage.PROCESS, 1.0, 
                                    message="이미지 처리 완료")
                
                # 이미지 저장 단계
                self._report_progress(ConversionStage.SAVE, 0.0, 
                                    message="이미지 저장 중")
                
                # 이미지 저장
                success = self.color_manager.write_image_with_colorspace(
                    output_path, pixels, metadata, output_profile_name
                )
                
                if not success:
                    error_msg = "이미지 저장 실패"
                    self.logger.error(error_msg)
                    self._report_progress(ConversionStage.SAVE, 1.0, 
                                        message="오류 발생", error=error_msg)
                    return False, error_msg, {"error_info": {"message": error_msg}}
                
                # 이미지 저장 완료
                self._report_progress(ConversionStage.SAVE, 1.0, 
                                    message="이미지 저장 완료")
                    
            else:
                # 기존 방식으로 처리 (OpenImageIO 직접 사용)
                # 변환 설정 가져오기
                pre_settings, post_settings = ImageFormatUtils.get_conversion_settings(input_format, output_format)
                
                # 옵션에서 추가 설정 가져오기
                if 'exposure' in options:
                    pre_settings['exposure'] = float(options['exposure'])
                if 'gamma' in options:
                    pre_settings['gamma'] = float(options['gamma'])
                
                # 디버그 정보에 변환 설정 추가
                debug_info["conversion_settings"] = {
                    "input_format": input_format,
                    "output_format": output_format,
                    "pre_processing": pre_settings,
                    "post_processing": post_settings
                }
                
                # 이미지 로드 단계 시작
                self._report_progress(ConversionStage.LOAD, 0.0, 
                                    message="이미지 파일 로드 중")
                
                # 입력 이미지 열기
                input_image = oiio.ImageInput.open(input_path)
                if not input_image:
                    error_msg = f"입력 이미지를 열 수 없습니다: {input_path}"
                    self.logger.error(error_msg)
                    error_details = oiio.geterror()
                    debug_info["oiio_error"] = error_details
                    self.logger.error(f"OIIO 에러 상세: {error_details}")
                    self._report_progress(ConversionStage.LOAD, 1.0, 
                                        message="오류 발생", error=error_msg)
                    return False, error_msg, debug_info
                
                # 이미지 로드 완료
                self._report_progress(ConversionStage.LOAD, 1.0, 
                                    message="이미지 파일 열기 완료")
                
                # 이미지 분석 단계 시작
                self._report_progress(ConversionStage.ANALYZE, 0.0, 
                                    message="이미지 정보 분석 중")
                
                # 입력 이미지 스펙 및 데이터 읽기
                spec = input_image.spec()
                self._report_progress(ConversionStage.ANALYZE, 0.3, 
                                    message="이미지 스펙 분석 완료", 
                                    width=spec.width, height=spec.height, 
                                    channels=spec.nchannels)
                
                # 이미지 데이터 읽기
                self._report_progress(ConversionStage.ANALYZE, 0.5, 
                                    message="이미지 데이터 읽는 중")
                pixel_data = input_image.read_image()
                
                if pixel_data is None:
                    error_msg = "이미지 데이터를 읽을 수 없습니다."
                    self.logger.error(error_msg)
                    error_details = oiio.geterror()
                    debug_info["oiio_error"] = error_details
                    self.logger.error(f"OIIO 에러 상세: {error_details}")
                    self._report_progress(ConversionStage.ANALYZE, 1.0, 
                                        message="오류 발생", error=error_msg)
                    return False, error_msg, debug_info
                
                # 이미지 분석 완료
                self._report_progress(ConversionStage.ANALYZE, 1.0, 
                                    message="이미지 분석 완료")
                
                # 색 공간 변환 단계 (이 방식에서는 생략)
                self._report_progress(ConversionStage.COLOR, 0.0, 
                                    message="색 공간 처리 중")
                self._report_progress(ConversionStage.COLOR, 1.0, 
                                    message="색 공간 처리 완료")
                
                # 이미지 처리 단계
                self._report_progress(ConversionStage.PROCESS, 0.0, 
                                    message="이미지 데이터 처리 중")
                
                # 픽셀 데이터 전처리
                processed_data = self._apply_pre_processing(pixel_data, spec, pre_settings)
                
                # 이미지 처리 완료
                self._report_progress(ConversionStage.PROCESS, 1.0, 
                                    message="이미지 처리 완료")
                
                # 출력 파일 준비
                self._report_progress(ConversionStage.SAVE, 0.0, 
                                    message="출력 파일 준비 중")
                
                # 출력 스펙 조정
                output_spec = ImageFormatUtils.adjust_bit_depth(spec, output_format)
                
                # 특정 포맷에 맞게 채널 수 조정
                if not ImageFormatUtils.has_alpha_support(output_format) and output_spec.nchannels == 4:
                    output_spec.nchannels = 3
                    
                # 출력 이미지 생성 및 쓰기
                self._report_progress(ConversionStage.SAVE, 0.5, 
                                    message="이미지 저장 중")
                
                success = self._write_output_image(processed_data, output_spec, output_path, post_settings)
                
                if not success:
                    error_msg = "이미지 변환 중 오류가 발생했습니다."
                    error_details = oiio.geterror()
                    debug_info["oiio_error"] = error_details
                    self.logger.error(f"{error_msg} 상세: {error_details}")
                    self._report_progress(ConversionStage.SAVE, 1.0, 
                                        message="오류 발생", error=error_msg)
                    return False, error_msg, debug_info
                
                # 이미지 저장 완료
                self._report_progress(ConversionStage.SAVE, 1.0, 
                                    message="이미지 저장 완료")
            
            # 변환 완료
            self._report_progress(ConversionStage.COMPLETE, 1.0, 
                                message="변환 작업 완료")
            
            # 변환 완료 메시지 
            self.logger.info(f"이미지 변환 완료: {output_path}")
            return True, f"{input_format}에서 {output_format}으로 변환 완료", debug_info
            
        except Exception as e:
            error_info = get_detailed_error_info(e)
            error_msg = f"이미지 변환 중 오류 발생: {error_info['message']}"
            self.logger.error(format_error_for_log(error_info))
            self._report_progress(ConversionStage.PROCESS, 1.0, 
                                message="오류 발생", error=error_msg)
            return False, error_msg, {"error_info": error_info}
            
        finally:
            if input_image:
                try:
                    input_image.close()
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    self.logger.error(f"입력 이미지 리소스 정리 중 오류: {format_error_for_log(error_info)}")
    
    def _apply_color_adjustments(self, pixels: np.ndarray, metadata: Dict, 
                              input_format: str, output_format: str, 
                              options: Dict) -> np.ndarray:
        """이미지 픽셀 데이터에 색상 처리를 적용합니다."""
        self.logger.debug(f"이미지 색상 처리: {input_format} -> {output_format}")
        
        # 포맷 변환에 따른 특수 처리
        is_input_hdr = input_format in ["EXR"]
        is_output_hdr = output_format in ["EXR"]
        
        result = pixels.copy()
        
        # HDR -> LDR 변환
        if is_input_hdr and not is_output_hdr:
            # 톤 매핑 옵션
            tone_map_method = options.get("tone_map_method", "Reinhard")
            exposure = float(options.get("exposure", 1.0))
            gamma = float(options.get("gamma", 2.2))
            
            self.logger.debug(f"HDR->LDR 변환: 톤 매핑={tone_map_method}, 노출={exposure}, 감마={gamma}")
            self._report_progress(ConversionStage.PROCESS, 0.2, 
                                message=f"HDR 톤 매핑 적용 중 ({tone_map_method})")
            
            # 톤 매핑 적용
            result = self.color_manager.process_hdr_to_ldr(result, tone_map_method, exposure, gamma)
            
            self._report_progress(ConversionStage.PROCESS, 0.5, 
                                message="톤 매핑 완료")
        
        # 색상 조정
        brightness = float(options.get("brightness", 0.0))
        contrast = float(options.get("contrast", 0.0))
        saturation = float(options.get("saturation", 0.0))
        exposure_stops = float(options.get("exposure_stops", 0.0))
        
        if brightness != 0.0 or contrast != 0.0 or saturation != 0.0 or exposure_stops != 0.0:
            self.logger.debug(f"색상 조정: 밝기={brightness}, 대비={contrast}, 채도={saturation}, 노출={exposure_stops}")
            self._report_progress(ConversionStage.PROCESS, 0.7, 
                                message="색상 조정 적용 중")
            
            result = self.color_manager.apply_color_adjustments(
                result, brightness, contrast, saturation, exposure_stops
            )
            
            self._report_progress(ConversionStage.PROCESS, 0.9, 
                                message="색상 조정 완료")
        
        # 알파 채널 처리 (알파 채널이 있고, 출력 포맷이 알파를 지원하지 않는 경우)
        if metadata["channels"] == 4 and output_format == "JPEG":
            self.logger.debug("알파 채널 제거 (JPEG 출력용)")
            self._report_progress(ConversionStage.PROCESS, 0.95, 
                                message="알파 채널 처리 중")
            
            # 배경색 옵션
            bg_color = options.get("background_color", (1, 1, 1))  # 기본 흰색 배경
            
            # 배경색으로 알파 채널 합성
            bg = np.array(bg_color[:3])  # RGB 부분만 사용
            
            # 알파 채널 분리
            rgb = result[..., :3]
            alpha = result[..., 3:4]
            
            # 알파 블렌딩 (미리 곱해진 알파 가정)
            if not options.get("premultiplied_alpha", False):
                rgb = rgb * alpha
            
            # 배경색과 합성
            blended = rgb + bg * (1 - alpha)
            
            # 3채널로 변환
            result = np.clip(blended, 0, 1)
        
        return result
    
    def _apply_pre_processing(self, pixel_data: np.ndarray, spec: oiio.ImageSpec, 
                             settings: Dict[str, Any]) -> np.ndarray:
        """
        픽셀 데이터에 전처리를 적용합니다.
        
        Args:
            pixel_data: 원본 픽셀 데이터
            spec: 이미지 스펙
            settings: 전처리 설정
            
        Returns:
            전처리된 픽셀 데이터
        """
        result = pixel_data
        
        # 톤 매핑 적용 (HDR → LDR)
        if settings.get("apply_tone_mapping"):
            self.logger.debug("톤 매핑 적용 중...")
            exposure = settings.get("exposure", 1.0)
            gamma = settings.get("gamma", 2.2)
            result = ImageFormatUtils.apply_tone_mapping(result, exposure, gamma)
            
        # 알파 채널 제거
        if settings.get("remove_alpha") and result.shape[2] == 4:
            self.logger.debug("알파 채널 제거 중...")
            bg_color = settings.get("background_color", (1, 1, 1))
            result = ImageFormatUtils.remove_alpha_channel(result, bg_color)
            
        return result
    
    def _write_output_image(self, pixel_data: np.ndarray, spec: oiio.ImageSpec, 
                           output_path: str, settings: Dict[str, Any]) -> bool:
        """
        처리된 픽셀 데이터를 출력 이미지로 저장합니다.
        
        Args:
            pixel_data: 처리된 픽셀 데이터
            spec: 출력 이미지 스펙
            output_path: 출력 경로
            settings: 후처리 설정
            
        Returns:
            성공 여부
        """
        output_image = None
        try:
            # 출력 디렉토리 확인 및 생성
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                    self.logger.debug(f"출력 디렉토리 생성: {output_dir}")
                except Exception as e:
                    self.logger.error(f"출력 디렉토리 생성 실패: {str(e)}")
                    return False
            
            # 출력 파일 확장자 확인
            ext = os.path.splitext(output_path)[1].lower()
            
            # HDR 포맷인 경우 특수 처리
            if ext == '.hdr':
                try:
                    self.logger.debug("HDR 파일 저장 시작")
                    
                    # HDR 포맷은 RGB만 지원 (알파 채널 제거)
                    if pixel_data.shape[2] == 4:
                        self.logger.debug("알파 채널 제거")
                        pixel_data = pixel_data[..., :3]
                    
                    # 음수 값 제거 (HDR은 음수 값을 지원하지 않음)
                    pixel_data = np.maximum(pixel_data, 0)
                    
                    # 임시 EXR 파일로 먼저 저장 (OpenImageIO는 EXR 저장이 더 안정적)
                    temp_exr_path = output_path + ".temp.exr"
                    self.logger.debug(f"임시 EXR 파일로 저장: {temp_exr_path}")
                    
                    # EXR 스펙 설정
                    exr_spec = oiio.ImageSpec(spec.width, spec.height, 3, oiio.FLOAT)
                    
                    # EXR 파일 생성
                    exr_out = oiio.ImageOutput.create(temp_exr_path)
                    if not exr_out:
                        self.logger.error("임시 EXR 파일 생성 실패")
                        return False
                    
                    # EXR 저장
                    if exr_out.open(temp_exr_path, exr_spec):
                        success = exr_out.write_image(pixel_data)
                        exr_out.close()
                        
                        if not success:
                            self.logger.error("임시 EXR 파일 쓰기 실패")
                            return False
                            
                        # OIIO를 사용하여 EXR에서 HDR로 변환
                        try:
                            self.logger.debug(f"EXR → HDR 변환: {temp_exr_path} → {output_path}")
                            
                            # EXR 파일 읽기
                            input_buf = oiio.ImageBuf(temp_exr_path)
                            if not input_buf.has_error():
                                # HDR 파일로 저장
                                output_buf = oiio.ImageBuf()
                                output_buf.copy(input_buf)  # 데이터 복사
                                
                                # HDR로 저장
                                success = output_buf.write(output_path)
                                
                                # 임시 파일 삭제
                                try:
                                    os.remove(temp_exr_path)
                                except:
                                    self.logger.warning(f"임시 파일 삭제 실패: {temp_exr_path}")
                                
                                return success
                            else:
                                self.logger.error(f"임시 EXR 파일 읽기 실패: {input_buf.geterror()}")
                                return False
                        except Exception as e:
                            self.logger.error(f"HDR 변환 중 오류 발생: {str(e)}")
                            return False
                    else:
                        self.logger.error(f"임시 EXR 파일을 열 수 없음: {exr_out.geterror()}")
                        return False
                except Exception as e:
                    self.logger.error(f"HDR 파일 저장 중 오류 발생: {str(e)}")
                    return False
            else:
                # 일반 포맷인 경우 기본 처리
                output_image = oiio.ImageOutput.create(output_path)
                if not output_image:
                    self.logger.error(f"출력 이미지를 생성할 수 없습니다: {output_path}")
                    return False
                
                # 압축 관련 속성 설정
                for key, value in settings.items():
                    if key == "quality" and isinstance(value, int):
                        spec["jpeg:quality"] = value
                    elif key == "compressionlevel" and isinstance(value, int):
                        spec["png:compressionlevel"] = value
                    elif key == "compression" and isinstance(value, str):
                        spec["compression"] = value
                    elif key == "rle" and isinstance(value, bool):
                        spec["targa:rle"] = int(value)
                    
                # 이미지 쓰기
                if output_image.open(output_path, spec):
                    success = output_image.write_image(pixel_data)
                    output_image.close()
                    return success
                else:
                    self.logger.error(f"출력 파일을 열 수 없습니다: {output_path}")
                    return False
                
        except Exception as e:
            error_info = get_detailed_error_info(e)
            self.logger.error(f"이미지 저장 중 오류: {format_error_for_log(error_info)}")
            return False
            
        finally:
            if output_image:
                try:
                    # 아직 닫히지 않았다면 닫기
                    output_image.close()
                except Exception as e:
                    error_info = get_detailed_error_info(e)
                    self.logger.error(f"이미지 리소스 정리 중 오류: {format_error_for_log(error_info)}")
    
    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        이미지의 기본 정보를 반환합니다.
        
        Args:
            image_path: 이미지 경로
            
        Returns:
            이미지 정보를 담은 딕셔너리
        """
        self.logger.debug(f"이미지 정보 조회: {image_path}")
        
        try:
            if not os.path.exists(image_path):
                return {"error": f"파일이 존재하지 않습니다: {image_path}"}
                
            input_file = oiio.ImageInput.open(image_path)
            if not input_file:
                return {"error": f"이미지를 열 수 없습니다: {image_path}"}
            
            try:
                spec = input_file.spec()
                
                # 색 프로파일 감지
                color_profile = self.color_manager.detect_image_profile(image_path)
                profile_name = color_profile.name if color_profile else "Unknown"
                
                # 포맷 확인
                ext = os.path.splitext(image_path)[1].lower()
                format_name = "Unknown"
                for fmt, ext_val in self.supported_formats.items():
                    if ext_val.lower() == ext:
                        format_name = fmt
                        break
                
                # 비트 깊이 계산
                bit_depth = 8
                if str(spec.format) == "float":
                    bit_depth = 32
                elif str(spec.format) == "half":
                    bit_depth = 16
                elif "uint16" in str(spec.format):
                    bit_depth = 16
                
                # HDR 여부 확인
                is_hdr = format_name in ["EXR"] or bit_depth > 8
                
                # 기본 정보
                info = {
                    "width": spec.width,
                    "height": spec.height,
                    "channels": spec.nchannels,
                    "format": format_name,
                    "bit_depth": bit_depth,
                    "is_hdr": is_hdr,
                    "color_profile": profile_name,
                    "file_size": os.path.getsize(image_path)
                }
                
                # 추가 메타데이터
                for k, v in spec.extra_attribs.items():
                    info[f"meta:{k}"] = str(v)
                
                return info
                
            finally:
                input_file.close()
                
        except Exception as e:
            error_info = get_detailed_error_info(e)
            self.logger.error(f"이미지 정보 조회 중 오류: {format_error_for_log(error_info)}")
            return {"error": f"이미지 정보 조회 중 오류: {error_info['message']}"}
    
    def get_color_management_options(self) -> Dict:
        """색 관리 관련 옵션 목록을 반환합니다."""
        options = {
            "profiles": self.color_manager.get_available_profiles(),
            "tone_mapping_methods": self.color_manager.get_available_tone_mapping_methods()
        }
        return options 