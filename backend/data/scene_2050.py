"""
2050年颁奖典礼场景数据
"""
SCENE_2050 = {
    "id": "scene_2050",
    "title": "时光的奖赏",
    "description": "2050年，北京国家大剧院。"中国非物质文化遗产传承杰出贡献奖"颁奖典礼正在进行。大屏幕上播放着陈守义一生的皮影戏历程——从1972年西安老巷到2089年量子实验室。小雨作为AI记忆修复项目的负责人，正在台上讲述爷爷的故事。灯光温暖而庄重，掌声如潮水般涌来。",
    "time_period": "2050年 冬",
    "scene_type": "narrative",
    "mood": "荣耀与传承",
    "bgm": "交响乐+掌声",
    "npcs": ["xiaoyu_2050", "journalist_2050"],
    "hotspots": [
        {"id": "award_trophy", "x": 400, "y": 150, "radius": 30, "hint": "水晶奖杯折射着七彩光芒", "fragment_id": "award_trophy_fragment"},
        {"id": "old_photos_wall", "x": 200, "y": 200, "radius": 25, "hint": "墙上挂满了跨越半个世纪的照片", "fragment_id": "old_photos_wall_fragment"},
        {"id": "hologram_stage", "x": 600, "y": 300, "radius": 35, "hint": "全息投影正在表演皮影戏", "fragment_id": "hologram_stage_fragment"},
        {"id": "audience_reactions", "x": 300, "y": 400, "radius": 25, "hint": "观众席中有人悄悄擦眼泪", "fragment_id": "audience_reactions_fragment"}
    ],
    "ambient_sounds": ["掌声", "交响乐", "相机快门声"],
    "visual_elements": {
        "palette": ["#FFD700", "#FFF8DC", "#B8860B", "#2F2F2F"],
        "atmosphere": "金色灯光洒满大厅，水晶奖杯折射出彩虹般的光芒"
    }
}
