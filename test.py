import random

# ベースとなるemotion_valuesの定義
base_emotion_values = {
    "happy": 0.65,
    "sadness": 0.00,
    "anger": 0.00,
    "speed": 1.35,
    "pitch": 1.10,
    "intonation": 1.00,
    # その他の感情パラメータ...
}

# キャラクターごとのadjustment_factorを設定
character_adjustment_factors = {
    "character1": 0.2,
    "character2": 0.9,
    # 他のキャラクターの係数もここに設定...
}


def calculate_function_calling_emotion_values():
    random_num1 = round(random.uniform(-3, 3), 2)
    random_num2 = round(random.uniform(-3, 3), 2)
    random_num3 = round(random.uniform(-3, 3), 2)

    current_emotion_values = {
        "happy": random_num1,
        "sadness": random_num2,
        "anger": random_num3,
        # その他の感情パラメータ...
    }
    return current_emotion_values

# 感情値の履歴を保存するためのクラス
class EmotionHistoryEMA:
    def __init__(self, smoothing_factor=0.65):
        self.smoothing_factor = smoothing_factor
        self.ema_values = {}

    def update_ema(self, current_values):
        if not self.ema_values:  # 初回の場合は現在の値をそのまま使用
            self.ema_values = current_values
            return self.ema_values

        updated_ema = {}
        for emotion, current_value in current_values.items():
            previous_ema = self.ema_values.get(emotion, current_value)
            new_ema = self.smoothing_factor * current_value + (1 - self.smoothing_factor) * previous_ema
            updated_ema[emotion] = round(new_ema, 2)  # 小数点第2位で切り捨て

        self.ema_values = updated_ema
        return updated_ema

# 感情値のEMAを管理するインスタンスを作成
emotion_history_ema = EmotionHistoryEMA()

# 新しい感情値を計算してEMAを更新する関数
def calculate_emotion_values(base_values, dynamic_values, character):
    adjustment_factor = character_adjustment_factors.get(character, 0.1)
    combined_values = {}

    # ベースの感情値と動的感情値を組み合わせる
    for emotion, base_value in base_values.items():
        dynamic_value = dynamic_values.get(emotion, 0) * adjustment_factor
        combined_value = base_value + dynamic_value
        combined_values[emotion] = combined_value

    # EMAを更新して最新の感情値を取得
    ema_values = emotion_history_ema.update_ema(combined_values)

    # 最終的な感情値を調整（小数点の制御）
    final_emotion_values = {emotion: round(value, 2) for emotion, value in ema_values.items()}
    return final_emotion_values







# 使用例
character = "character1"

for i in range(10):
    function_calling_emotion_values = calculate_function_calling_emotion_values()

    if i == 0:
        function_calling_emotion_values = {
            "happy": -3,
            "sadness": 300,
            "anger": -3,
            # その他の感情パラメータ...
        }
    else:
        function_calling_emotion_values = {
            "happy": 0,
            "sadness": 0,
            "anger": 0,
            # その他の感情パラメータ...
        }

    # 定義されている可能性のある感情のキーを含むリスト
    expected_keys = ['happy', 'sadness', 'anger', 'speed', 'pitch', 'intonation']

    # 不足しているキーを確認し、存在しない場合は0.00で補完する
    for key in expected_keys:
        if key not in function_calling_emotion_values:
            function_calling_emotion_values[key] = 0.00

    new_emotion_values = calculate_emotion_values(base_emotion_values, function_calling_emotion_values, character)

    # final_emotion_valuesに適切な範囲で値を収める処理
    for emotion, value in new_emotion_values.items():
        if emotion in ['happy', 'sad', 'anger']:
            # happy, sad, anger の場合、0～1の範囲に収める
            adjusted_value = min(max(value, 0.0), 1.0)
        elif emotion in 'speed':
            # speed の場合、0.5～4の範囲に収める
            adjusted_value = min(max(value, 0.5), 4.0)
        elif emotion in 'pitch':
            # pitch の場合、0.5～2の範囲に収める
            adjusted_value = min(max(value, 0.5), 2.0)
        else:
            # intonation の場合、0～2の範囲に収める
            adjusted_value = min(max(value, 0.0), 2.0)
        
        new_emotion_values[emotion] = round(adjusted_value, 2)

    print(new_emotion_values)
