"""ファイル操作関連の関数"""
from typing import List
from pathlib import Path
import logging

import config


class FileManager:
    """ファイル管理クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def cleanup_all_files() -> None:
        """生成されたすべてのファイルを削除"""
        logger = logging.getLogger(__name__)
        logger.info("\n生成ファイルを削除します...")

        # 各ディレクトリのファイルを削除
        for dir_path in [config.get_output_dir(), config.get_keyframes_dir()]:
            if dir_path.exists():
                for item in dir_path.iterdir():
                    if item.is_file():
                        try:
                            item.unlink()
                            logger.info(f"削除: {item.name}")
                        except Exception as e:
                            logger.error(f"削除エラー ({item}): {e}")

        # 空のディレクトリを削除
        for dir_path in [config.get_output_dir(), config.get_keyframes_dir()]:
            if dir_path.exists() and not any(dir_path.iterdir()):
                try:
                    dir_path.rmdir()
                    logger.info(f"ディレクトリ削除: {dir_path.name}")
                except Exception as e:
                    logger.error(f"ディレクトリ削除エラー ({dir_path}): {e}")

        logger.info("ファイル削除が完了しました。")

    @staticmethod
    def get_video_files() -> List[Path]:
        """ビデオファイルのリストを取得"""
        return list(config.get_output_dir().glob("*.mp4"))

    @staticmethod
    def get_keyframe_files(segment_id: int) -> List[Path]:
        """指定したセグメントIDのキーフレームファイルを取得"""
        return sorted(config.get_keyframes_dir().glob(f"segment_{segment_id}_keyframe_*.jpg"))
