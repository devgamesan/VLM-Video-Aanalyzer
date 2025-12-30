"""キューとイベント管理モジュール"""
import queue
import threading
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueueManager:
    """キューとスレッド管理クラス"""

    def __init__(self, max_workers: int = 1):
        self.video_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()

    def put_video_info(self, video_info: Dict[str, Any]) -> bool:
        """ビデオ情報をキューに追加"""
        try:
            with self.lock:
                if not isinstance(video_info, dict):
                    logger.error(f"無効なデータ形式です: {type(video_info)}")
                    return False
                self.video_queue.put_nowait(video_info)
                return True
        except queue.Full:
            logger.error("キューが満杯です")
            return False
        except Exception as e:
            logger.error(f"キューへの追加エラー: {e}")
            return False

    def get_video_info(self, timeout: float = 1.0) -> Dict[str, Any]:
        """キューからビデオ情報を取得（タイムアウト付き）"""
        try:
            return self.video_queue.get(timeout=timeout)
        except queue.Empty:
            raise queue.Empty("キューが空です")
        except Exception as e:
            logger.error(f"キューからの取得エラー: {e}")
            raise

    def is_empty(self) -> bool:
        """キューが空かどうかを確認"""
        try:
            return self.video_queue.empty()
        except Exception as e:
            logger.error(f"キュー空判定エラー: {e}")
            return True

    def stop(self) -> None:
        """停止イベントをセット"""
        self.stop_event.set()

    def is_stopped(self) -> bool:
        """停止イベントがセットされているか確認"""
        try:
            return self.stop_event.is_set()
        except Exception as e:
            logger.error(f"停止イベント確認エラー: {e}")
            return True

    def submit_task(self, func, *args):
        """スレッドプールにタスクを追加"""
        try:
            future = self.executor.submit(func, *args)
            return future
        except Exception as e:
            logger.error(f"タスク提出エラー: {e}")
            raise

    def shutdown(self) -> None:
        """スレッドプールをシャットダウン"""
        try:
            self.executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Executorシャットダウンエラー: {e}")

    def wait_for_completion(self, timeout: float = None) -> None:
        """全てのタスクが完了するのを待機"""
        try:
            self.executor.shutdown(wait=True)
        except Exception as e:
            logger.error(f"タスク完了待機エラー: {e}")