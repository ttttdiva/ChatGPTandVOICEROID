import base64
from io import BytesIO

import pygetwindow as gw
from PIL import Image, ImageGrab


def capture_screen_to_base64():
    # アクティブなウィンドウの取得
    window = gw.getActiveWindow()

    # アクティブなウィンドウの位置とサイズを取得
    if window:
        left, top, width, height = window.left, window.top, window.width, window.height
        bbox = (left, top, left + width, top + height)

        # スクリーンショットを撮る
        screenshot = ImageGrab.grab(bbox)

        # スクリーンショットのサイズを長辺512pxにスケールダウン（アスペクト比維持）
        # detailed: highの場合は1999まで
        longest_side = max(screenshot.size)
        scale_factor = 1999 / longest_side
        new_size = (int(screenshot.width * scale_factor), int(screenshot.height * scale_factor))
        screenshot = screenshot.resize(new_size, Image.ANTIALIAS)

        # スクリーンショットをBase64にエンコード
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        screenshot.save("./temp.png", format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Base64に変換されたスクリーンショットを取得
base64_screenshot = capture_screen_to_base64()
print(base64_screenshot)
