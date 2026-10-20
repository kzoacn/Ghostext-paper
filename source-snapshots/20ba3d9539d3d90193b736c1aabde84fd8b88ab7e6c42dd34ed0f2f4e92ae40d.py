"""Author-written public contexts, frozen before the new model experiments."""
from __future__ import annotations


CONTEXTS = [
    ("evening_walk", "The evening walk through the neighborhood was quiet. Along the street,",
     "傍晚散步时，社区里的街道很安静。沿着路边，"),
    ("corner_cafe", "Inside the small cafe, the afternoon light fell across the wooden tables.",
     "小咖啡馆里，午后的阳光照在木桌上。"),
    ("library", "The library was nearly empty when the last class ended. On the second floor,",
     "最后一节课结束后，图书馆里已经没什么人了。在二楼，"),
    ("garden", "After the rain, the garden paths were still wet. Near the gate,",
     "雨停以后，花园里的小路仍然湿漉漉的。在大门旁边，"),
    ("market", "At the neighborhood market, the stalls were opening for the morning.",
     "清晨，社区菜市场里的摊位陆续开始营业。"),
    ("train", "The train reached the next station a few minutes early. Through the window,",
     "火车提前几分钟到达了下一站。透过车窗，"),
    ("science", "In the school laboratory, the class prepared a simple experiment with water.",
     "学校的实验室里，同学们准备做一个与水有关的小实验。"),
    ("museum", "The museum opened a new room about the history of local transportation.",
     "博物馆新开放了一个介绍当地交通历史的展厅。"),
    ("mountain", "The trail climbed gently through the forest before reaching an open hillside.",
     "山路穿过树林缓缓上升，随后来到一片开阔的山坡。"),
    ("workshop", "In the repair workshop, a bicycle stood beside a box of carefully sorted tools.",
     "修理铺里，一辆自行车停在装着分类工具的箱子旁边。"),
]


def prompts(backend_name):
    result = []
    for index, (family, en, zh) in enumerate(CONTEXTS):
        for language, context in [("en", en), ("zh", zh)]:
            if backend_name == "gpt2" and language == "zh":
                continue
            prompt = context
            if backend_name == "qwen":
                prompt = (
                    "Continue the following passage in natural English prose:\n" + context
                    if language == "en" else "请用自然连贯的中文续写下面的段落：\n" + context
                )
            result.append({
                "prompt_id": f"{index:02d}_{language}_{family}", "family": family,
                "language": language, "split": "development" if index < 5 else "test",
                "prompt": prompt,
            })
    return result
