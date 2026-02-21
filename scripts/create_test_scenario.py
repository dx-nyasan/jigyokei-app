import json
import os

# 佐藤精密工業のシナリオデータ
SCENARIO_DATA = {
    "company_name": "佐藤精密工業",
    "industry": "製造業（金属部品加工）",
    "location": "東京都葛飾区（荒川氾濫リスク地域）",
    "employees": 15,
    "user_persona": "佐藤社長（50代、ITは苦手だが補助金申請のためにジギョケイが必要）",
    "chat_steps": [
        {"role": "user", "message": "葛飾区で15人で金属加工をやってる佐藤精密工業です。補助金の加点のためにジギョケイを作りたい。"},
        {"role": "assistant", "trigger": "事業概要のサジェスト"},
        {"role": "user", "message": "荒川の近くなんだけど、水害とか考えたほうがいいかな？"},
        {"role": "assistant", "trigger": "ハザードマップ・リスクのサジェスト"},
        {"role": "user", "message": "土嚢を準備するくらいしか思いつかないけど、どう書けばいい？"},
        {"role": "assistant", "trigger": "具体的な初動対応のサジェスト"},
        {"role": "user", "message": "いいですね、それでお願いします。"},
        {"role": "assistant", "trigger": "下書き作成完了"}
    ]
}

def create_test_files():
    data_dir = "tests/data"
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "test_scenario_sato.json"), "w", encoding="utf-8") as f:
        json.dump(SCENARIO_DATA, f, ensure_ascii=False, indent=2)
    print(f"Created: {os.path.join(data_dir, 'test_scenario_sato.json')}")

if __name__ == "__main__":
    create_test_files()
