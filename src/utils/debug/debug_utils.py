import traceback
import inspect
import os
from typing import Any, Dict

def get_detailed_error_info(exception: Exception) -> Dict[str, Any]:
    """
    예외에 대한 상세 정보를 딕셔너리로 반환합니다.
    
    Args:
        exception: 발생한 예외 객체
        
    Returns:
        상세 에러 정보를 담은 딕셔너리
    """
    exc_type = type(exception).__name__
    exc_msg = str(exception)
    exc_traceback = traceback.format_exc()
    
    # 호출 스택 정보 수집
    caller_frame = inspect.currentframe().f_back
    caller_info = ""
    if caller_frame:
        caller_info = f"{os.path.basename(caller_frame.f_code.co_filename)}:{caller_frame.f_lineno}"
    
    return {
        "type": exc_type,
        "message": exc_msg,
        "traceback": exc_traceback,
        "caller": caller_info
    }
    
def format_error_for_log(error_info: Dict[str, Any]) -> str:
    """
    에러 정보를 로그용 문자열로 포맷합니다.
    
    Args:
        error_info: get_detailed_error_info에서 반환된 딕셔너리
        
    Returns:
        포맷된 에러 문자열
    """
    return f"[Error] {error_info['type']}: {error_info['message']}\n" \
           f"위치: {error_info['caller']}\n" \
           f"스택 트레이스:\n{error_info['traceback']}"
           
def format_error_for_ui(error_info: Dict[str, Any]) -> str:
    """
    에러 정보를 UI 표시용 문자열로 포맷합니다.
    
    Args:
        error_info: get_detailed_error_info에서 반환된 딕셔너리
        
    Returns:
        포맷된 에러 문자열
    """
    return f"{error_info['type']}: {error_info['message']}\n" \
           f"발생 위치: {error_info['caller']}" 