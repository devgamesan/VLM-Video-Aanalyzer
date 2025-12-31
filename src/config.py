"""設定定数を定義するモジュール

このモジュールは、アプリケーション全体の設定値を定義し、
環境変数から値を読み込むための設定管理クラスです。
"""
from pathlib import Path
from dotenv import load_dotenv
import os
from typing import Tuple, Dict, Any

# .envファイルを読み込む
load_dotenv()

# パス設定
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR.parent / "captured_videos"
KEYFRAMES_DIR = BASE_DIR.parent / "keyframes"

# デフォルト値の定義（型ヒント付き）
DEFAULT_CAPTURE_INTERVAL: int = 5
DEFAULT_CAMERA_INDEX: int = 0
DEFAULT_TARGET_FPS: float = 30.0
DEFAULT_VLM_MODEL: str = "gpt-4o"
DEFAULT_VLM_IMAGE_MAX_SIZE: Tuple[int, int] = (800, 800)
DEFAULT_FFMPEG_KEYFRAME_COUNT: int = 5
DEFAULT_VLM_PROMPT: str = "動画の内容を簡潔に200文字以内で説明してください。"


def get_capture_interval() -> int:
    """キャプチャ間隔を取得"""
    try:
        return int(os.getenv("CAPTURE_INTERVAL", DEFAULT_CAPTURE_INTERVAL))
    except ValueError:
        return DEFAULT_CAPTURE_INTERVAL


def get_camera_index() -> int:
    """カメラインデックスを取得"""
    try:
        return int(os.getenv("CAMERA_INDEX", DEFAULT_CAMERA_INDEX))
    except ValueError:
        return DEFAULT_CAMERA_INDEX


def get_target_fps() -> float:
    """ターゲットFPSを取得"""
    try:
        return float(os.getenv("TARGET_FPS", DEFAULT_TARGET_FPS))
    except ValueError:
        return DEFAULT_TARGET_FPS


def get_vlm_config() -> Dict[str, Any]:
    """VLM設定を取得"""
    config = {
        "model": os.getenv("VLM_MODEL", DEFAULT_VLM_MODEL),
        "api_key": os.getenv("VLM_API_KEY", ""),  # 空文字をデフォルトに
    }

    # VLM APIのベースURL - VLMサービスへの接続先URL（例: http://localhost:22015/v1）
    vlm_base_url = os.getenv("VLM_BASE_URL")
    if vlm_base_url:
        config["base_url"] = vlm_base_url

    return config


def get_vlm_image_max_size() -> Tuple[int, int]:
    """VLM画像の最大サイズを取得"""
    size_str = os.getenv("VLM_IMAGE_MAX_SIZE", "")
    if size_str:
        try:
            width, height = map(int, size_str.split(","))
            return (width, height)
        except (ValueError, TypeError):
            pass
    return DEFAULT_VLM_IMAGE_MAX_SIZE


def get_ffmpeg_keyframe_count() -> int:
    """FFmpegキーフレーム数を取得"""
    try:
        return int(os.getenv('FFMPEG_KEYFRAME_COUNT', DEFAULT_FFMPEG_KEYFRAME_COUNT))
    except ValueError:
        return DEFAULT_FFMPEG_KEYFRAME_COUNT


def get_ffmpeg_keyframe_args() -> list:
    """FFmpegキーフレーム抽出引数を取得"""
    # キーフレーム数を動的に取得
    keyframe_count = str(get_ffmpeg_keyframe_count())
    return [
        '-vf', 'select=eq(pict_type\\,I)',
        '-vsync', 'vfr',
        '-frames:v', keyframe_count  # キーフレーム数
    ]


def get_vlm_prompt() -> str:
    """VLMプロンプトを取得"""
    return os.getenv("VLM_PROMPT", DEFAULT_VLM_PROMPT)


def get_output_dir() -> Path:
    """出力ディレクトリを取得"""
    return OUTPUT_DIR


def get_keyframes_dir() -> Path:
    """キーフレームディレクトリを取得"""
    return KEYFRAMES_DIR
