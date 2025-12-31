"""ビデオ処理関連クラス"""
from typing import Optional
from pathlib import Path
import asyncio
import threading
import queue
import logging
from datetime import datetime
import config

from video_capture import VideoCaptureManager
from keyframe_extractor import KeyframeExtractor
from vlm_client import VLMClient
from file_manager import FileManager
from queue_manager import QueueManager

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """ビデオ処理クラス"""

    def __init__(self):
        self.queue_manager = QueueManager()
        self.vlm_client = VLMClient()
        self.keyframe_extractor = KeyframeExtractor()
        self.capture_manager: Optional[VideoCaptureManager] = None
        self.vlm_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.current_description = "\n\n分析準備中..."
        self.description_lock = threading.Lock()
        self.start_time = None
        # セグメントの開始時間（秒単位）を保持する辞書
        self.segment_start_times = {}
        # 分析結果履歴
        self.analysis_history = []
        # 履歴更新用コールバック
        self.history_callback = None

    def set_description(self, description: str):
        """説明文を設定"""
        with self.description_lock:
            self.current_description = description

    def get_description(self) -> str:
        """説明文を取得"""
        with self.description_lock:
            return self.current_description

    def _vlm_loop_wrapper(self):
        """asyncioループを別スレッドで実行するためのラッパー"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.vlm_processing_loop())
        except Exception as e:
            logger.error(f"VLMループでの予期しないエラー: {e}")
        finally:
            loop.close()

    async def vlm_processing_loop(self):
        """VLM処理ループ"""
        logger.info("VLM処理ループを開始しました...")
        while self.is_running:
            try:
                # タイムアウト付きでキューから取得
                video_info = self.queue_manager.get_video_info(timeout=0.5)
                if video_info:
                    await self.process_video_segment(video_info['segment_id'], video_info['file_path'])
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue
            except Exception as e:
                logger.error(f"VLM処理ループエラー: {e}")
                await asyncio.sleep(1.0)

    async def process_video_segment(self, segment_id: int, video_path: str):
        """ビデオセグメントを処理"""
        import time
        start_time = time.time()
        try:
            # パスの存在確認
            video_file = Path(video_path)
            if not video_file.exists():
                logger.error(f"ビデオファイルが見つかりません: {video_path}")
                return

            keyframes = self.keyframe_extractor.extract_from_video(video_file, segment_id)
            if keyframes:
                description = self.vlm_client.analyze_images(keyframes)
                if description:
                    # セグメントIDに基づいた正確な開始・終了時間を計算
                    start_total_seconds = (segment_id - 1) * config.get_capture_interval()
                    end_total_seconds = segment_id  * config.get_capture_interval()

                    start_min, start_sec = divmod(start_total_seconds, 60)
                    end_min, end_sec = divmod(end_total_seconds, 60)

                    formatted_time_range = f"{start_min:02d}:{start_sec:02d}〜{end_min:02d}:{end_sec:02d}"
                    description_with_time = f"（{formatted_time_range}）\n\n{description}"
                    self.set_description(description_with_time)

                    # 履歴に追加
                    if self.history_callback:
                        self.history_callback(description_with_time)
                else:
                    self.set_description(description)
                    # 履歴に追加
                    if self.history_callback:
                        self.history_callback(description)

                # キーフレームを使用した後、削除する
                for keyframe in keyframes:
                    try:
                        if keyframe.exists():
                            keyframe.unlink()
                            logger.info(f"キーフレーム削除: {keyframe.name}")
                        else:
                            logger.warning(f"キーフレームがすでに削除されています: {keyframe}")
                    except Exception as e:
                        logger.error(f"キーフレーム削除エラー ({keyframe}): {e}")
            # ビデオファイルも不要になったら削除する
            try:
                if video_file.exists():
                    video_file.unlink()
                    logger.info(f"ビデオファイル削除: {video_file.name}")
                else:
                    logger.warning(f"ビデオファイルがすでに削除されています: {video_file}")
            except Exception as e:
                logger.error(f"ビデオファイル削除エラー ({video_file}): {e}")
        except Exception as e:
            logger.error(f"セグメント処理エラー: {e}")
        finally:
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(f"セグメント {segment_id} の処理時間: {elapsed_time:.2f} 秒")

    def start(self):
        """処理の開始"""
        self.is_running = True
        self.start_time = datetime.now()
        self.capture_manager = VideoCaptureManager()

        # VLMスレッド開始
        self.vlm_thread = threading.Thread(target=self._vlm_loop_wrapper, daemon=True)
        self.vlm_thread.start()

    def stop(self):
        """処理の停止"""
        self.is_running = False
        self.queue_manager.stop()
        if self.capture_manager:
            self.capture_manager.release()
        if self.vlm_thread:
            self.vlm_thread.join(timeout=2.0)
        FileManager.cleanup_all_files()

    def update_frame(self):
        """フレームを読み込み、必要に応じてセグメント化する"""
        if not self.capture_manager:
            return None

        ret, frame = self.capture_manager.cap.read()
        if not ret:
            logger.warning("フレームの読み込みに失敗しました")
            return None

        # セグメント処理（オリジナルのロジックを維持）
        if self.capture_manager.should_start_new_segment():
            if self.capture_manager.current_output_path and self.capture_manager.segment_count > 0:
                video_info = self.capture_manager.get_current_segment_info()
                success = self.queue_manager.put_video_info(video_info)
                if not success:
                    logger.error("キューへの追加に失敗しました")
            self.capture_manager.start_new_segment(frame)

        self.capture_manager.write_frame(frame)
        return frame