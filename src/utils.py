"""汎用的なユーティリティ関数を定義するモジュール

このモジュールは、アプリケーション全体で共通して使用される
ユーティリティ関数を提供します。
"""

from datetime import datetime
from pathlib import Path


def format_time(seconds: int) -> str:
    """秒をMM:SS形式にフォーマット"""
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def get_elapsed_time(start_time: datetime) -> str:
    """経過時間をMM:SS形式で取得"""
    if not start_time:
        return "00:00"

    elapsed = datetime.now() - start_time
    total_seconds = int(elapsed.total_seconds())
    return format_time(total_seconds)


def get_segment_start_time(start_time: datetime) -> str:
    """セグメント開始時間をMM:SS形式で取得"""
    if not start_time:
        return "00:00"

    # 現在のセグメントの開始時間（秒単位）
    current_segment_start = int((datetime.now() - start_time).total_seconds())
    return format_time(current_segment_start)


def setup_directories() -> None:
    """必要なディレクトリを作成

    出力ディレクトリとキーフレーム保存用ディレクトリが存在しない場合に作成する。
    """
    from config import OUTPUT_DIR, KEYFRAMES_DIR

    for dir_path in [OUTPUT_DIR, KEYFRAMES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)