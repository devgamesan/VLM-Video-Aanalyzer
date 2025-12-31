"""ビデオキャプチャ関連のクラスと関数"""
import cv2
import time
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path
import logging
import re

import config


class VideoCaptureManager:
    """ビデオキャプチャの管理クラス"""

    def __init__(self, camera_source: int | str = config.get_camera_source()) -> None:
        self.logger = logging.getLogger(__name__)

        # URL形式かどうかを判定
        if isinstance(camera_source, str) and re.match(r'^https?://', camera_source):
            # HTTP/RTSPストリームの場合
            self.cap = cv2.VideoCapture(camera_source)
            self.logger.info(f"HTTP/RTSPストリームを開始: {camera_source}")
        else:
            # カメラまたはローカルファイルの場合
            self.cap = cv2.VideoCapture(camera_source)
            if not self.cap.isOpened():
                raise RuntimeError(f"カメラを開けませんでした (index: {camera_source})")
            self.logger.info(f"カメラを開始: {camera_source}")

        self._fps = self._determine_fps()
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.segment_count: int = 0
        self.start_time: float = time.time()
        self.current_output_path: Optional[Path] = None

    def _determine_fps(self) -> float:
        """適切なFPSを決定"""
        fps_setting = self.cap.get(cv2.CAP_PROP_FPS)
        if fps_setting > 0:
            self.logger.info(f"カメラの設定FPS: {fps_setting}")
            return fps_setting
        else:
            self.logger.info(f"デフォルトFPSを使用: {config.get_target_fps()}")
            return config.get_target_fps()

    def start_new_segment(self, frame) -> None:
        """新しいビデオセグメントを開始"""
        self._release_writer()  # 既存のライターを解放

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.segment_count += 1
        self.current_output_path = config.get_output_dir() / f"segment_{self.segment_count}.mp4"

        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            str(self.current_output_path),
            fourcc,
            self.fps,
            (width, height)
        )

        self.logger.info(f"新しいビデオセグメントを開始: {self.current_output_path.name}")
        self.start_time = time.time()

    def write_frame(self, frame) -> None:
        """フレームを書き込み"""
        if self.video_writer is not None:
            self.video_writer.write(frame)

    def should_start_new_segment(self) -> bool:
        """新しいセグメントを開始するタイミングか判定"""
        return (self.video_writer is None or
                time.time() - self.start_time >= config.get_capture_interval())

    def get_current_segment_info(self) -> dict:
        """現在のセグメント情報を取得"""
        return {
            'segment_id': self.segment_count,
            'file_path': str(self.current_output_path),
            'timestamp': datetime.now().isoformat()
        }

    def _release_writer(self) -> None:
        """ビデオライターを解放"""
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            if self.current_output_path and self.current_output_path.exists():
                self.logger.info(f"セグメントを保存: {self.current_output_path.name}")

    def release(self) -> None:
        """リソースを解放"""
        self._release_writer()
        if self.cap is not None:
            self.cap.release()

    @property
    def fps(self) -> float:
        return self._fps


def capture_frame(cap_manager: VideoCaptureManager) -> Tuple[bool, any]:
    """単一フレームをキャプチャ"""
    return cap_manager.cap.read()