import os
import time
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Tuple, Callable
from src.converters.enhanced_converter import EnhancedConverter
from src.utils.debug.debug_utils import get_detailed_error_info, format_error_for_log
from src.services.log_service import LogService

class BatchTask:
    """배치 작업을 위한 단일 작업 정보"""
    
    def __init__(self, input_path: str, output_path: str, options: Dict[str, Any] = None):
        self.input_path = input_path
        self.output_path = output_path
        self.options = options or {}
        self.status = "pending"  # pending, processing, completed, failed
        self.error = None
        self.start_time = None
        self.end_time = None
        
    def get_duration(self):
        """작업 실행 시간(초)"""
        if not self.start_time:
            return 0
            
        end = self.end_time or time.time()
        return end - self.start_time
        
    def get_status_info(self):
        """작업 상태 정보"""
        return {
            "input_path": self.input_path,
            "output_path": self.output_path,
            "status": self.status,
            "error": self.error,
            "duration": self.get_duration()
        }

class BatchConverter:
    """멀티스레드 배치 이미지 변환기"""
    
    def __init__(self, max_workers=None):
        self.logger = LogService().get_logger("BatchConverter")
        self.converter = EnhancedConverter()
        self.max_workers = max_workers or min(32, os.cpu_count() + 4)
        self.tasks_queue = queue.Queue()
        self.results = {}
        self.running = False
        self.progress_callback = None
        self.completed_count = 0
        self.total_count = 0
        self.executor = None
        self.task_lock = threading.Lock()
        
    def add_task(self, input_path: str, output_path: str, options: Dict[str, Any] = None):
        """변환 작업 추가"""
        task = BatchTask(input_path, output_path, options)
        self.tasks_queue.put(task)
        self.results[input_path] = task
        self.total_count += 1
        
    def add_folder_task(self, input_folder: str, output_folder: str, 
                       extensions: List[str] = None, recursive: bool = True, 
                       options: Dict[str, Any] = None):
        """폴더 내 파일들에 대한 변환 작업 추가"""
        if not os.path.isdir(input_folder):
            self.logger.error(f"입력 폴더가 존재하지 않음: {input_folder}")
            return 0
            
        # 지원되는 확장자
        if not extensions:
            extensions = [ext.lower() for ext in self.converter.supported_formats.values()]
            
        count = 0
        
        # 폴더 내 모든 파일 검색
        for root, dirs, files in os.walk(input_folder):
            if not recursive and root != input_folder:
                continue
                
            for file in files:
                # 지원되는 확장자인지 확인
                _, ext = os.path.splitext(file)
                if ext.lower() not in extensions:
                    continue
                    
                # 상대 경로 계산
                rel_path = os.path.relpath(os.path.join(root, file), input_folder)
                
                # 확장자 변경 (옵션에 지정된 출력 포맷 사용)
                output_ext = None
                if options and "output_format" in options:
                    for fmt, ext_val in self.converter.supported_formats.items():
                        if fmt.lower() == options["output_format"].lower():
                            output_ext = ext_val
                            break
                            
                if not output_ext:
                    output_ext = ext  # 기본값: 원본과 동일한 확장자
                
                output_filename = os.path.splitext(rel_path)[0] + output_ext
                output_path = os.path.join(output_folder, output_filename)
                
                # 출력 디렉토리 생성
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 작업 추가
                self.add_task(os.path.join(root, file), output_path, options)
                count += 1
                
        self.logger.info(f"폴더 작업 추가 완료: {count}개 파일")
        return count
        
    def start(self, progress_callback: Callable[[int, int, Dict], None] = None):
        """변환 작업 시작"""
        if self.running:
            self.logger.warning("이미 배치 작업이 실행 중입니다")
            return False
            
        if self.tasks_queue.empty():
            self.logger.warning("변환할 작업이 없습니다")
            return False
            
        self.progress_callback = progress_callback
        self.running = True
        self.completed_count = 0
        
        # 스레드 풀 생성
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 작업 큐의 각 작업을 스레드 풀에 제출
        while not self.tasks_queue.empty():
            task = self.tasks_queue.get()
            self.executor.submit(self._process_task, task)
            
        # 진행 상황 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=self._monitor_progress)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return True
        
    def _process_task(self, task: BatchTask):
        """개별 작업 처리"""
        task.start_time = time.time()
        task.status = "processing"
        
        try:
            # 출력 디렉토리 생성
            output_dir = os.path.dirname(task.output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            # 이미지 변환 수행
            success, message, debug_info = self.converter.convert_image(
                task.input_path, task.output_path
            )
            
            if success:
                task.status = "completed"
            else:
                task.status = "failed"
                task.error = message
                self.logger.error(f"변환 실패: {task.input_path} -> {task.output_path}, 오류: {message}")
                
        except Exception as e:
            error_info = get_detailed_error_info(e)
            task.status = "failed"
            task.error = error_info["message"]
            self.logger.error(f"변환 예외 발생: {format_error_for_log(error_info)}")
            
        finally:
            task.end_time = time.time()
            with self.task_lock:
                self.completed_count += 1
                
    def _monitor_progress(self):
        """진행 상황 모니터링"""
        while self.running and self.completed_count < self.total_count:
            if self.progress_callback:
                # 진행 상황 콜백 호출
                self.progress_callback(
                    self.completed_count, 
                    self.total_count, 
                    self._get_progress_info()
                )
            time.sleep(0.1)  # CPU 부하 감소를 위한 대기
            
        # 모든 작업이 완료되면 마지막 콜백 호출
        if self.progress_callback:
            self.progress_callback(
                self.completed_count, 
                self.total_count, 
                self._get_progress_info()
            )
            
        self.running = False
        self.executor.shutdown()
        self.logger.info(f"배치 작업 완료: 총 {self.total_count}개 중 {self.completed_count}개 완료")
        
    def _get_progress_info(self):
        """현재 진행 상황 정보"""
        completed = []
        failed = []
        pending = []
        processing = []
        
        for task in self.results.values():
            if task.status == "completed":
                completed.append(task.get_status_info())
            elif task.status == "failed":
                failed.append(task.get_status_info())
            elif task.status == "processing":
                processing.append(task.get_status_info())
            else:
                pending.append(task.get_status_info())
                
        return {
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": processing,
            "total": self.total_count,
            "completed_count": self.completed_count,
            "percentage": int((self.completed_count / self.total_count) * 100) if self.total_count > 0 else 0
        }
        
    def stop(self):
        """실행 중인 작업 중지"""
        if not self.running:
            return
            
        self.running = False
        if self.executor:
            self.executor.shutdown(wait=False)
            
        self.logger.info("배치 작업 중지 요청")
        
    def get_results(self):
        """모든 작업 결과 반환"""
        return {
            "total": self.total_count,
            "completed": sum(1 for task in self.results.values() if task.status == "completed"),
            "failed": sum(1 for task in self.results.values() if task.status == "failed"),
            "tasks": [task.get_status_info() for task in self.results.values()]
        }
        
    def is_running(self):
        """작업 실행 중 여부"""
        return self.running 