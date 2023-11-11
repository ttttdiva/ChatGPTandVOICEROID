def decode_unicode_escapes(s):
    if '\\u' in s:
        return s.encode('utf-8').decode('unicode_escape')
    else:
        return s

# Unicodeエスケープされた日本語の文字列
escaped_str = "\u4e07\u77f3\u9945\u982d\u306e\u770c"

# 通常の日本語文字列
japanese_str = "万石鹿頭の県"

# Unicodeエスケープされた文字列をデコード
decoded_escaped_str = decode_unicode_escapes(escaped_str)

# 通常の文字列はそのまま
decoded_japanese_str = decode_unicode_escapes(japanese_str)

print(decoded_escaped_str)  # デコードされた日本語が出力される
print(decoded_japanese_str)  # 元の日本語がそのまま出力される
