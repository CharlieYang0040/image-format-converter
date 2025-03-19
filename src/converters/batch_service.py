import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Tuple, Callable
from src.converters.enhanced_converter import EnhancedConverter
from src.utils.debug.debug_utils import get_detailed_error_info, format_error_for_log
from src.services.log_service import LogService

class BatchService:
    """배치 이미지 변환 서비스"""
    
    def __init__(self):
        self.logger = LogService()
        self.converter = EnhancedConverter()
        self.max_workers = min(32, os.cpu_count() + 4)  # 기본 스레드 수
        self.running = False
        self.progress_callback = None
        self.cancel_requested = False
        
        # 작업 상태 관리
        self.tasks = {}  # 모든 작업 목록
        self.pending_tasks = []  # 대기 중인 작업 목록
        self.processing_tasks = {}  # 처리 중인 작업 목록
        self.completed_tasks = []  # 완료된 작업 목록
        self.failed_tasks = []  # 실패한 작업 목록
        
        # 스레드 관리
        self.executor = None
        self.monitor_thread = None
        self.lock = threading.Lock()  # 스레드 안전성을 위한 락
        
    def add_file_task(self, input_path: str, output_path: str, options: Dict[str, Any] = None):
        """단일 파일 변환 작업 추가"""
        task = {
            "input_path": input_path,
            "output_path": output_path,
            "options": options or {},
            "status": "pending",
            "error": None,
            "start_time": None,
            "end_time": None,
            "duration": 0
        }
        
        with self.lock:
            task_id = len(self.tasks)
            task["id"] = task_id
            self.tasks[task_id] = task
            self.pending_tasks.append(task_id)
            
        self.logger.debug(f"작업 추가: {input_path} -> {output_path}")
        return task_id
        
    def add_folder_task(self, input_folder: str, output_folder: str, 
                       output_format: str = None, recursive: bool = True,
                       options: Dict[str, Any] = None):
        """폴더 내 이미지 변환 작업 추가"""
        added_count = 0
        
        if not os.path.isdir(input_folder):
            self.logger.error(f"입력 폴더가 존재하지 않음: {input_folder}")
            return added_count
            
        # 옵션 초기화
        if options is None:
            options = {}
            
        # 지원되는 확장자 목록
        supported_extensions = []
        for format_name, ext in self.converter.supported_formats.items():
            supported_extensions.append(ext.lower())
            
        # 출력 확장자 결정
        output_ext = None
        if output_format:
            for format_name, ext in self.converter.supported_formats.items():
                if format_name.lower() == output_format.lower():
                    output_ext = ext
                    break
        
        # 폴더 내 이미지 파일 검색
        for root, dirs, files in os.walk(input_folder):
            # 재귀 검색이 아닌 경우 첫 레벨만 처리
            if not recursive and root != input_folder:
                continue
                
            for file in files:
                # 파일 확장자 확인
                _, ext = os.path.splitext(file)
                if ext.lower() not in supported_extensions:
                    continue
                    
                # 입력 파일 경로
                input_file_path = os.path.join(root, file)
                
                # 출력 경로 계산
                rel_path = os.path.relpath(input_file_path, input_folder)
                
                if output_ext:
                    # 지정된 출력 포맷이 있는 경우 확장자 변경
                    output_file_path = os.path.join(
                        output_folder, 
                        os.path.splitext(rel_path)[0] + output_ext
                    )
                else:
                    # 없는 경우 원본 확장자 유지
                    output_file_path = os.path.join(output_folder, rel_path)
                    
                # 작업 추가
                self.add_file_task(input_file_path, output_file_path, options)
                added_count += 1
                
        self.logger.info(f"폴더 작업 추가 완료: {added_count}개 파일")
        return added_count
        
    def start(self, progress_callback: Callable = None):
        """변환 작업 시작"""
        if self.running:
            self.logger.warning("이미 배치 작업이 실행 중입니다")
            return False
            
        if len(self.pending_tasks) == 0:
            self.logger.warning("변환할 작업이 없습니다")
            return False
            
        self.running = True
        self.cancel_requested = False
        self.progress_callback = progress_callback
        
        # 스레드 풀 생성
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 모니터링 스레드 시작
        self.monitor_thread = threading.Thread(target=self._monitor_progress)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("배치 변환 작업 시작")
        return True
        
    def _monitor_progress(self):
        """작업 진행 상황 모니터링 및 작업 제출"""
        while self.running and (len(self.pending_tasks) > 0 or len(self.processing_tasks) > 0):
            if self.cancel_requested:
                self.logger.info("작업 취소 요청 처리 중...")
                break
                
            # 처리 중인 작업이 최대 워커 수보다 적은 경우 새 작업 제출
            with self.lock:
                available_workers = self.max_workers - len(self.processing_tasks)
                if available_workers > 0 and len(self.pending_tasks) > 0:
                    for _ in range(min(available_workers, len(self.pending_tasks))):
                        if len(self.pending_tasks) == 0:
                            break
                            
                        task_id = self.pending_tasks.pop(0)
                        task = self.tasks[task_id]
                        
                        # 작업 상태 업데이트
                        task["status"] = "processing"
                        task["start_time"] = time.time()
                        self.processing_tasks[task_id] = task
                        
                        # 작업 제출
                        self.executor.submit(
                            self._process_task, 
                            task_id,
                            task["input_path"], 
                            task["output_path"], 
                            task["options"]
                        )
            
            # 진행 상황 콜백 호출
            if self.progress_callback:
                self.progress_callback(
                    len(self.completed_tasks) + len(self.failed_tasks),
                    len(self.tasks),
                    self._get_progress_info()
                )
                
            # CPU 부하 감소를 위한 대기
            time.sleep(0.1)
            
        # 작업이 모두 완료되었거나 취소된 경우
        if self.executor:
            self.executor.shutdown(wait=False)
            
        self.running = False
        
        # 최종 진행 상황 콜백 호출
        if self.progress_callback:
            self.progress_callback(
                len(self.completed_tasks) + len(self.failed_tasks),
                len(self.tasks),
                self._get_progress_info()
            )
            
        self.logger.info(f"배치 작업 완료: 총 {len(self.tasks)}개 중 {len(self.completed_tasks)}개 성공, {len(self.failed_tasks)}개 실패")
        
    def _process_task(self, task_id: int, input_path: str, output_path: str, options: Dict[str, Any]):
        """개별 변환 작업 처리"""
        if self.cancel_requested:
            with self.lock:
                # 작업 상태를 취소로 변경
                if task_id in self.processing_tasks:
                    task = self.processing_tasks.pop(task_id)
                    task["status"] = "cancelled"
                    task["end_time"] = time.time()
                    task["duration"] = task["end_time"] - task["start_time"]
                    self.failed_tasks.append(task_id)
            return
        
        try:
            # 출력 디렉토리 생성
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # 이미지 변환 수행
            success, message, debug_info = self.converter.convert_image(input_path, output_path)
            
            with self.lock:
                if task_id in self.processing_tasks:
                    task = self.processing_tasks.pop(task_id)
                    task["end_time"] = time.time()
                    task["duration"] = task["end_time"] - task["start_time"]
                    
                    if success:
                        task["status"] = "completed"
                        self.completed_tasks.append(task_id)
                    else:
                        task["status"] = "failed"
                        task["error"] = message
                        self.failed_tasks.append(task_id)
                        self.logger.error(f"변환 실패: {input_path}, 오류: {message}")
                        
        except Exception as e:
            error_info = get_detailed_error_info(e)
            
            with self.lock:
                if task_id in self.processing_tasks:
                    task = self.processing_tasks.pop(task_id)
                    task["status"] = "failed"
                    task["error"] = error_info["message"]
                    task["end_time"] = time.time()
                    task["duration"] = task["end_time"] - task["start_time"]
                    self.failed_tasks.append(task_id)
                    
            self.logger.error(f"변환 예외 발생: {input_path}, 오류: {format_error_for_log(error_info)}")
            
    def cancel(self):
        """실행 중인 작업 취소"""
        if not self.running:
            return
            
        self.cancel_requested = True
        self.logger.info("배치 작업 취소 요청")
        
    def _get_progress_info(self):
        """현재 진행 상황 정보"""
        with self.lock:
            # 작업 상태별 정보 수집
            pending = []
            processing = []
            completed = []
            failed = []
            
            # 대기 중인 작업
            for task_id in self.pending_tasks:
                task = self.tasks[task_id]
                pending.append({
                    "input_path": task["input_path"],
                    "output_path": task["output_path"],
                    "status": task["status"],
                    "duration": 0
                })
                
            # 처리 중인 작업
            for task_id, task in self.processing_tasks.items():
                current_time = time.time()
                duration = current_time - task["start_time"] if task["start_time"] else 0
                processing.append({
                    "input_path": task["input_path"],
                    "output_path": task["output_path"],
                    "status": task["status"],
                    "duration": duration
                })
                
            # 완료된 작업
            for task_id in self.completed_tasks:
                task = self.tasks[task_id]
                completed.append({
                    "input_path": task["input_path"],
                    "output_path": task["output_path"],
                    "status": task["status"],
                    "duration": task["duration"]
                })
                
            # 실패한 작업
            for task_id in self.failed_tasks:
                task = self.tasks[task_id]
                failed.append({
                    "input_path": task["input_path"],
                    "output_path": task["output_path"],
                    "status": task["status"],
                    "error": task["error"],
                    "duration": task["duration"]
                })
                
            return {
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "total": len(self.tasks),
                "completed_count": len(self.completed_tasks),
                "failed_count": len(self.failed_tasks),
                "percentage": int((len(self.completed_tasks) + len(self.failed_tasks)) / len(self.tasks) * 100) if self.tasks else 0
            }
            
    def is_running(self):
        """작업 실행 중 여부"""
        return self.running
        
    def get_results(self):
        """변환 결과 요약"""
        return {
            "total": len(self.tasks),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "success_rate": (len(self.completed_tasks) / len(self.tasks) * 100) if self.tasks else 0
        }
        
    def reset(self):
        """작업 상태 초기화"""
        if self.running:
            self.cancel()
            
        with self.lock:
            self.tasks = {}
            self.pending_tasks = []
            self.processing_tasks = {}
            self.completed_tasks = []
            self.failed_tasks = [] 