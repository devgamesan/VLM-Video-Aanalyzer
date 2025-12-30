"""設定定数を定義するモジュール

このモジュールは、アプリケーション全体の設定値を定義し、
環境変数から値を読み込むための設定管理クラスです。
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

# パス設定
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "captured_videos"
KEYFRAMES_DIR = BASE_DIR / "keyframes"

# キャプチャ設定
# セグメント間隔（秒）- カメラからキャプチャした動画を区切る時間間隔
CAPTURE_INTERVAL = int(os.getenv("CAPTURE_INTERVAL", 5))
# カメラインデックス - 使用するカメラのインデックス番号
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
# ターゲットFPS - 動画のフレームレート（FPS）
TARGET_FPS = float(os.getenv("TARGET_FPS", 30.0))

# VLM設定
# 使用するVLMモデル名 - 画像分析に使用するモデルの識別子
VLM_CONFIG = {
    "model": os.getenv("VLM_MODEL", "gpt-4o"),
    # VLM APIキー - VLMサービスへの認証に使用するAPIキー
    "api_key": os.getenv("VLM_API_KEY", "YOUR_API_KEY"),
}

# VLM APIのベースURL - VLMサービスへの接続先URL（例: http://localhost:22015/v1）
# 環境変数が設定されている場合のみbase_urlを設定
vlm_base_url = os.getenv("VLM_BASE_URL")
if vlm_base_url:
    VLM_CONFIG["base_url"] = vlm_base_url

# 画像リサイズ設定
# 画像リサイズサイズ - VLMに渡す画像の最大サイズ（幅,高さ）
VLM_IMAGE_MAX_SIZE = tuple(map(int, os.getenv("VLM_IMAGE_MAX_SIZE", "800,800").split(",")))

# FFmpeg設定
# 抽出するキーフレーム数 - 1つの動画セグメントから抽出するキーフレームの数
FFMPEG_KEYFRAME_COUNT = os.getenv('FFMPEG_KEYFRAME_COUNT', '5')
FFMPEG_KEYFRAME_ARGS = [
    '-vf', 'select=eq(pict_type\\,I)',
    '-vsync', 'vfr',
    '-frames:v', FFMPEG_KEYFRAME_COUNT # キーフレーム数
]

# プロンプトテンプレート
# VLM分析プロンプト - VLMが動画内容を説明する際の指示文
VLM_PROMPT = os.getenv("VLM_PROMPT", "動画の内容を簡潔に200文字以内説明してください。")

# ディレクトリ作成
def setup_directories() -> None:
    """必要なディレクトリを作成

    出力ディレクトリとキーフレーム保存用ディレクトリが存在しない場合に作成する。
    """
    for dir_path in [OUTPUT_DIR, KEYFRAMES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)