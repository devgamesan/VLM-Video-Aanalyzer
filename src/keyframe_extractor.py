"""キーフレーム抽出関連の関数"""
import subprocess
from typing import List
from pathlib import Path
import logging

import config

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KeyframeExtractor:
    """キーフレーム抽出クラス"""

    def __init__(self, ffmpeg_path: str = 'ffmpeg'):
        self.ffmpeg_path = ffmpeg_path

    def extract_from_video(self, video_path: Path, segment_id: int) -> List[Path]:
        """ビデオからキーフレームを抽出"""
        # ファイルの存在確認
        if not video_path.exists():
            logger.error(f"ビデオファイルが見つかりません: {video_path}")
            return []

        # ファイルが有効か確認
        if not video_path.is_file():
            logger.error(f"指定されたパスはファイルではありません: {video_path}")
            return []

        # 出力ディレクトリの存在確認と作成
        try:
            config.KEYFRAMES_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"キーフレーム出力ディレクトリ作成エラー: {e}")
            return []

        output_pattern = str(config.KEYFRAMES_DIR / f"segment_{segment_id}_keyframe_%04d.jpg")

        ffmpeg_cmd = [
            self.ffmpeg_path,
            '-i', str(video_path),
            *config.FFMPEG_KEYFRAME_ARGS,
            output_pattern
        ]

        try:
            logger.info(f"キーフレーム抽出を開始: segment_{segment_id}")
            result = subprocess.run(
                ffmpeg_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"キーフレーム抽出成功: segment_{segment_id}")

            # 抽出されたキーフレームファイルのリストを返す
            keyframe_files = sorted(
                config.KEYFRAMES_DIR.glob(f"segment_{segment_id}_keyframe_*.jpg")
            )
            logger.info(f"キーフレーム数: {len(keyframe_files)}")
            return keyframe_files

        except subprocess.CalledProcessError as e:
            logger.error(f"キーフレーム抽出エラー (segment {segment_id}):")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return []
        except FileNotFoundError:
            logger.error(f"ffmpegが見つかりません。パスを確認してください: {self.ffmpeg_path}")
            return []
        except Exception as e:
            logger.error(f"キーフレーム抽出処理中の予期しないエラー: {e}")
            return []