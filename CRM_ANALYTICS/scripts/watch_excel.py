#!/usr/bin/env python3
"""
Watch for changes in Excel file and trigger pipeline automatically
"""

import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelChangeHandler(FileSystemEventHandler):
    def __init__(self, pipeline_script):
        self.pipeline_script = pipeline_script
        self.last_modified = None
    
    def on_modified(self, event):
        if event.src_path.endswith('CRM Data Set - Case Study.xlsx'):
            current_time = time.time()
            if self.last_modified and (current_time - self.last_modified) < 5:
                return  # Debounce
            
            self.last_modified = current_time
            logger.info(f"Excel file changed: {event.src_path}")
            logger.info("Triggering pipeline...")
            
            # Run pipeline
            result = subprocess.run(['python', self.pipeline_script], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Pipeline completed successfully")
            else:
                logger.error(f"Pipeline failed: {result.stderr}")

def watch_excel(excel_path, pipeline_script):
    event_handler = ExcelChangeHandler(pipeline_script)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(excel_path), recursive=False)
    observer.start()
    
    logger.info(f"Watching for changes in: {excel_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    excel_path = "../Source/CRM Data Set - Case Study.xlsx"
    pipeline_script = "run_pipeline.py"
    
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
    else:
        watch_excel(excel_path, pipeline_script)