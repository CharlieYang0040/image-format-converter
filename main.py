# main.py

import sys
from src.ui.app_window import AppWindow
from src.services.log_service import LogService

def main():
    logger = LogService()
    logger.info("이미지 변환기 애플리케이션 시작")
    
    try:
        app = AppWindow()
        app.create_window()
        app._setup_ui()
        app.run()
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {str(e)}")
        raise
    finally:
        logger.info("이미지 변환기 애플리케이션 종료")

if __name__ == "__main__":
    main()