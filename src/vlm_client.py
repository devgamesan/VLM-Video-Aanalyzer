"""VLM（Vision Language Model）クライアントモジュール"""
import base64
from typing import List, Optional
from pathlib import Path
from PIL import Image
from io import BytesIO
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import logging

import config


class VLMClient:
    """VLMクライアントクラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_config = config.VLM_CONFIG
        self.logger.info(self.model_config)
        self.client = ChatOpenAI(**self.model_config)

    @staticmethod
    def resize_and_encode_image(image_path: Path) -> tuple:
        """
        画像をリサイズしてBase64エンコード

        Returns:
            tuple: (base64_string, data_url, mime_type)
        """
        # configからmax_sizeを取得
        max_size = config.VLM_IMAGE_MAX_SIZE

        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        buffered = BytesIO()

        # 画像フォーマットに応じて保存
        if img.mode in ('RGBA', 'LA', 'P'):
            img.save(buffered, format="PNG", quality=95)
            mime_type = "image/png"
        else:
            img.save(buffered, format="JPEG", quality=95)
            mime_type = "image/jpeg"

        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        data_url = f"data:{mime_type};base64,{img_str}"

        return img_str, data_url, mime_type

    def analyze_images(self, image_paths: List[Path], prompt: str = None) -> Optional[str]:
        """複数画像を分析"""
        if not image_paths:
            return "画像がありません"

        logger = logging.getLogger(__name__)
        logger.info(f"入力画像数: {len(image_paths)}")

        prompt = prompt or config.VLM_PROMPT
        message_content = [{"type": "text", "text": prompt}]

        for image_path in image_paths:
            if not image_path.exists():
                logger.warning(f"警告: 画像が見つかりません {image_path}")
                continue

            _, data_url, _ = self.resize_and_encode_image(image_path)
            message_content.append({
                "type": "image_url",
                "image_url": {"url": data_url},
            })

        try:
            message = HumanMessage(content=message_content)
            response = self.client.invoke([message])
            return response.content
        except Exception as e:
            logger.error(f"VLM分析エラー: {e}")
            return None