"""
1990年深圳火车站场景数据
"""
SCENE_1990 = {
    "id": "scene_1990",
    "title": "南下的列车",
    "description": "1990年，深圳火车站。绿皮火车轰鸣着进站，站台上挤满了背着蛇皮袋的年轻人。陈守义站在人群中，手里攥着一张去深圳的硬座票，背后是装满皮影道具的旧木箱。广播里循环播放着"深圳特区欢迎您"，空气中弥漫着柴油味和方便面的香气。",
    "time_period": "1990年 秋",
    "scene_type": "narrative",
    "mood": "离别与希望",
    "bgm": "火车站嘈杂+远处汽笛",
    "npcs": ["chen_shouyi_1990", "stranger_1990"],
    "hotspots": [
        {"id": "train_ticket", "x": 350, "y": 200, "radius": 25, "hint": "一张皱巴巴的硬座票", "fragment_id": "train_ticket_fragment"},
        {"id": "puppet_trunk", "x": 600, "y": 350, "radius": 30, "hint": "装满皮影道具的旧木箱", "fragment_id": "puppet_trunk_fragment"},
        {"id": "farewell_letter", "x": 150, "y": 280, "radius": 20, "hint": "一封没寄出的信", "fragment_id": "farewell_letter_fragment"},
        {"id": "station_clock", "x": 400, "y": 80, "radius": 25, "hint": "巨大的时钟", "fragment_id": "station_clock_fragment"}
    ],
    "ambient_sounds": ["火车汽笛", "人群嘈杂", "广播声"],
    "visual_elements": {
        "palette": ["#8B7355", "#D2B48C", "#F5DEB3", "#CD853F"],
        "atmosphere": "尘土飞扬的站台，阳光透过站台顶棚洒下"
    }
}
