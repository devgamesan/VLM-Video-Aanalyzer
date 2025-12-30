import streamlit as st
import cv2
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

from config import setup_directories
from video_processor import VideoProcessor

# 環境変数の読み込み
load_dotenv()

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ページ全体の設定
st.set_page_config(
    layout="wide",
    page_title="リアルタイムVLM分析システム"
)

class VideoAnalysisPipeline:
    """ビデオ分析パイプライン"""

    def __init__(self):
        self.video_processor = VideoProcessor()
        self.is_running = False
        self.start_time = None

    def set_description(self, description: str):
        self.video_processor.set_description(description)

    def get_description(self) -> str:
        return self.video_processor.get_description()

    def start(self):
        """パイプラインの開始"""
        logger.info("パイプラインの開始を開始")
        setup_directories()
        self.is_running = True
        self.start_time = datetime.now()
        self.video_processor.start()

    def stop(self):
        """パイプラインの停止"""
        logger.info("パイプラインの停止を開始")
        self.is_running = False
        self.video_processor.stop()

    def update_frame(self):
        """フレームを読み込み、必要に応じてセグメント化する"""
        return self.video_processor.update_frame()

    def get_elapsed_time(self) -> str:
        """経過時間を取得"""
        if not self.start_time:
            return "00:00"

        elapsed = datetime.now() - self.start_time
        total_seconds = int(elapsed.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_segment_start_time(self) -> str:
        """セグメント開始時間を取得"""
        if not self.start_time:
            return "00:00"

        # 現在のセグメントの開始時間（秒単位）
        current_segment_start = int((datetime.now() - self.start_time).total_seconds())
        minutes, seconds = divmod(current_segment_start, 60)
        return f"{minutes:02d}:{seconds:02d}"

def render_ui(pipeline: VideoAnalysisPipeline):
    """UIレンダリング関数"""
    st.title("リアルタイムVLM分析システム")

    col1, col2 = st.columns([1, 1], gap="small")

    with col1:
        if st.button("分析開始") and not pipeline.is_running:
            pipeline.start()
            st.rerun()
    with col2:
        if st.button("分析停止") and pipeline.is_running:
            pipeline.stop()
            st.rerun()

    if pipeline.is_running:
        # 動画と説明文を横に並べるためのレイアウト
        video_col, description_col = st.columns([3, 2], gap="small")

        with video_col:
            frame_placeholder = st.empty()

        with description_col:
            text_placeholder = st.empty()

        # フレーム更新の処理
        while pipeline.is_running:
            frame = pipeline.update_frame()

            if frame is not None:
                # 表示用に変換
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # 経過時間をビデオ画像上に表示
                elapsed_time = pipeline.get_elapsed_time()
                segment_start_time = pipeline.get_segment_start_time()

                # OpenCVでフレームにテキストを追加
                font = cv2.FONT_HERSHEY_SIMPLEX
                text = f"{elapsed_time}"
                position = (10, 30)  # 左上に表示
                font_scale = 0.8
                color = (255, 255, 255)  # 白色
                thickness = 2

                # テキストの背景を黒に設定（視認性向上）
                text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
                cv2.rectangle(rgb_frame, (position[0]-5, position[1]-text_size[1]-5),
                               (position[0]+text_size[0]+5, position[1]+5), (0, 0, 0), -1)
                cv2.putText(rgb_frame, text, position, font, font_scale, color, thickness)

                # 動画を表示
                frame_placeholder.image(rgb_frame, channels="RGB", width="stretch")

                # 最新の説明文と時間範囲を表示
                description = pipeline.get_description()
                text_placeholder.info(f"**VLM分析結果**\n\n{description}")

            time.sleep(0.03) # 約30fps

def main():
    # セッション状態でパイプラインを管理
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = VideoAnalysisPipeline()

    render_ui(st.session_state.pipeline)

if __name__ == "__main__":
    main()