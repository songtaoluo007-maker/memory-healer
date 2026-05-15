<script setup lang="ts">
defineProps<{
  sceneId: string
}>()
</script>

<template>
  <!-- 1972年 西安老巷 -->
  <svg v-if="sceneId === 'scene_1972'" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" class="scene-illustration">
    <!-- 天空渐变 -->
    <defs>
      <linearGradient id="sky1972" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ff7b54" />
        <stop offset="40%" stop-color="#ff9a56" />
        <stop offset="70%" stop-color="#ffd4a2" />
        <stop offset="100%" stop-color="#ffe8c4" />
      </linearGradient>
      <linearGradient id="wall1972" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#8b7355" />
        <stop offset="100%" stop-color="#6b5b45" />
      </linearGradient>
      <radialGradient id="lantern" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0%" stop-color="#ff6b35" stop-opacity="0.8" />
        <stop offset="100%" stop-color="#ff6b35" stop-opacity="0" />
      </radialGradient>
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <!-- 天空 -->
    <rect width="800" height="500" fill="url(#sky1972)" />

    <!-- 远处的城墙轮廓 -->
    <path d="M0 180 L100 175 L150 160 L200 165 L280 155 L320 158 L400 150 L480 155 L520 160 L600 152 L680 158 L720 165 L800 160 L800 200 L0 200 Z" fill="#5c4a3a" opacity="0.6" />

    <!-- 城墙垛口 -->
    <g fill="#5c4a3a" opacity="0.6">
      <rect x="100" y="170" width="12" height="15" />
      <rect x="130" y="165" width="12" height="15" />
      <rect x="160" y="168" width="12" height="15" />
      <rect x="280" y="155" width="12" height="15" />
      <rect x="310" y="158" width="12" height="15" />
      <rect x="400" y="148" width="12" height="15" />
      <rect x="430" y="150" width="12" height="15" />
      <rect x="600" y="150" width="12" height="15" />
      <rect x="630" y="153" width="12" height="15" />
    </g>

    <!-- 老槐树 -->
    <rect x="680" y="180" width="18" height="160" fill="#5c4a3a" />
    <ellipse cx="690" cy="160" rx="60" ry="50" fill="#4a7c3f" opacity="0.8" />
    <ellipse cx="670" cy="140" rx="40" ry="35" fill="#5a8c4f" opacity="0.7" />
    <ellipse cx="710" cy="150" rx="45" ry="40" fill="#3a6c2f" opacity="0.7" />
    <!-- 槐花 -->
    <g fill="#fff8dc" opacity="0.6">
      <circle cx="660" cy="135" r="2" />
      <circle cx="680" cy="125" r="2" />
      <circle cx="700" cy="130" r="2" />
      <circle cx="720" cy="140" r="2" />
      <circle cx="690" cy="145" r="2" />
    </g>

    <!-- 左侧墙壁 -->
    <rect x="0" y="200" width="250" height="300" fill="url(#wall1972)" />
    <!-- 砖墙纹理 -->
    <g stroke="#7a6b55" stroke-width="0.5" opacity="0.3">
      <line x1="0" y1="220" x2="250" y2="220" />
      <line x1="0" y1="240" x2="250" y2="240" />
      <line x1="0" y1="260" x2="250" y2="260" />
      <line x1="0" y1="280" x2="250" y2="280" />
      <line x1="0" y1="300" x2="250" y2="300" />
      <line x1="0" y1="320" x2="250" y2="320" />
      <line x1="125" y1="200" x2="125" y2="220" />
      <line x1="60" y1="220" x2="60" y2="240" />
      <line x1="185" y1="220" x2="185" y2="240" />
      <line x1="125" y1="240" x2="125" y2="260" />
    </g>

    <!-- 右侧墙壁 -->
    <rect x="550" y="200" width="250" height="300" fill="url(#wall1972)" />
    <g stroke="#7a6b55" stroke-width="0.5" opacity="0.3">
      <line x1="550" y1="220" x2="800" y2="220" />
      <line x1="550" y1="240" x2="800" y2="240" />
      <line x1="550" y1="260" x2="800" y2="260" />
      <line x1="550" y1="280" x2="800" y2="280" />
    </g>

    <!-- 地面青石板 -->
    <rect x="250" y="340" width="300" height="160" fill="#6b6b6b" />
    <g stroke="#5a5a5a" stroke-width="0.5" opacity="0.4">
      <line x1="250" y1="360" x2="550" y2="360" />
      <line x1="250" y1="380" x2="550" y2="380" />
      <line x1="250" y1="400" x2="550" y2="400" />
      <line x1="250" y1="420" x2="550" y2="420" />
      <line x1="350" y1="340" x2="350" y2="500" />
      <line x1="450" y1="340" x2="450" y2="500" />
    </g>

    <!-- 纸窗（透出暖光） -->
    <rect x="80" y="250" width="60" height="80" rx="2" fill="#3a2a1a" />
    <rect x="85" y="255" width="50" height="70" rx="1" fill="#ffe4b5" opacity="0.7" />
    <rect x="160" y="250" width="60" height="80" rx="2" fill="#3a2a1a" />
    <rect x="165" y="255" width="50" height="70" rx="1" fill="#ffe4b5" opacity="0.7" />

    <!-- 灯笼 -->
    <g filter="url(#glow)">
      <ellipse cx="400" cy="220" rx="25" ry="15" fill="url(#lantern)" />
      <rect x="388" y="215" width="24" height="30" rx="12" fill="#cc3300" opacity="0.9" />
      <rect x="394" y="210" width="12" height="8" rx="2" fill="#8b6914" />
      <line x1="400" y1="200" x2="400" y2="210" stroke="#8b6914" stroke-width="1.5" />
      <!-- 灯笼上的字 -->
      <text x="400" y="235" text-anchor="middle" fill="#ffd700" font-size="8" font-family="serif">拾忆</text>
    </g>

    <!-- 皮影戏台 -->
    <g>
      <!-- 戏台框架 -->
      <rect x="310" y="280" width="180" height="120" rx="4" fill="#8b6914" opacity="0.9" />
      <!-- 白色幕布 -->
      <rect x="320" y="290" width="160" height="90" rx="2" fill="#fff8dc" opacity="0.85" />
      <!-- 幕布上的皮影剪影 -->
      <g fill="#2a1a0a" opacity="0.7">
        <!-- 关羽 -->
        <ellipse cx="370" cy="330" rx="8" ry="12" />
        <rect x="366" y="340" width="8" height="20" rx="2" />
        <line x1="362" y1="345" x2="355" y2="335" stroke="#2a1a0a" stroke-width="2" />
        <line x1="378" y1="345" x2="385" y2="355" stroke="#2a1a0a" stroke-width="2" />
        <!-- 青龙偃月刀 -->
        <line x1="355" y1="335" x2="340" y2="310" stroke="#2a1a0a" stroke-width="2.5" />
        <path d="M338 308 L342 312 L335 315 Z" fill="#2a1a0a" />
      </g>
      <!-- 暖光效果 -->
      <rect x="320" y="290" width="160" height="90" rx="2" fill="#ffd700" opacity="0.15" />
    </g>

    <!-- 氤氲的光粒子 -->
    <g fill="#ffd700" opacity="0.3">
      <circle cx="350" cy="270" r="1.5">
        <animate attributeName="cy" values="270;250;270" dur="3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.3;0.6;0.3" dur="3s" repeatCount="indefinite" />
      </circle>
      <circle cx="420" cy="260" r="1">
        <animate attributeName="cy" values="260;240;260" dur="4s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.2;0.5;0.2" dur="4s" repeatCount="indefinite" />
      </circle>
      <circle cx="380" cy="255" r="1.8">
        <animate attributeName="cy" values="255;235;255" dur="3.5s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.3;0.5;0.3" dur="3.5s" repeatCount="indefinite" />
      </circle>
    </g>

    <!-- 暮色光晕 -->
    <ellipse cx="400" cy="100" rx="300" ry="100" fill="#ff9a56" opacity="0.15" />
  </svg>

  <!-- 2024年 深圳城中村 -->
  <svg v-else-if="sceneId === 'scene_2024'" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" class="scene-illustration">
    <defs>
      <linearGradient id="sky2024" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1a1a2e" />
        <stop offset="40%" stop-color="#16213e" />
        <stop offset="100%" stop-color="#0f3460" />
      </linearGradient>
      <linearGradient id="neonGlow" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#e94560" stop-opacity="0.6" />
        <stop offset="100%" stop-color="#e94560" stop-opacity="0" />
      </linearGradient>
    </defs>

    <!-- 夜空 -->
    <rect width="800" height="500" fill="url(#sky2024)" />

    <!-- 远处的高楼大厦 -->
    <g fill="#1a2a4e" opacity="0.8">
      <rect x="50" y="80" width="60" height="250" />
      <rect x="120" y="60" width="45" height="270" />
      <rect x="175" y="100" width="55" height="230" />
      <rect x="600" y="70" width="50" height="260" />
      <rect x="660" y="90" width="60" height="240" />
      <rect x="730" y="50" width="55" height="280" />
    </g>

    <!-- 高楼窗户灯光 -->
    <g fill="#ffd700" opacity="0.4">
      <rect x="60" y="100" width="8" height="6" />
      <rect x="80" y="120" width="8" height="6" />
      <rect x="60" y="150" width="8" height="6" />
      <rect x="130" y="80" width="6" height="5" />
      <rect x="145" y="110" width="6" height="5" />
      <rect x="610" y="90" width="7" height="5" />
      <rect x="625" y="120" width="7" height="5" />
      <rect x="670" y="110" width="8" height="6" />
      <rect x="690" y="140" width="8" height="6" />
      <rect x="740" y="70" width="7" height="5" />
      <rect x="755" y="100" width="7" height="5" />
    </g>

    <!-- 霓虹灯招牌 -->
    <g>
      <rect x="280" y="120" width="100" height="30" rx="4" fill="#e94560" opacity="0.8">
        <animate attributeName="opacity" values="0.6;0.9;0.6" dur="2s" repeatCount="indefinite" />
      </rect>
      <text x="330" y="142" text-anchor="middle" fill="white" font-size="14" font-family="sans-serif">旅馆</text>
      <rect x="420" y="130" width="80" height="25" rx="4" fill="#00bcd4" opacity="0.7">
        <animate attributeName="opacity" values="0.5;0.8;0.5" dur="2.5s" repeatCount="indefinite" />
      </rect>
      <text x="460" y="148" text-anchor="middle" fill="white" font-size="12" font-family="sans-serif">网吧</text>
    </g>

    <!-- 城中村密集建筑 -->
    <g fill="#2a2a3e">
      <rect x="200" y="200" width="180" height="300" />
      <rect x="250" y="180" width="120" height="320" />
      <rect x="420" y="210" width="160" height="290" />
      <rect x="450" y="190" width="100" height="310" />
    </g>

    <!-- 出租屋窗户（暖光） -->
    <rect x="300" y="250" width="50" height="40" rx="2" fill="#1a1a2e" />
    <rect x="305" y="255" width="40" height="30" rx="1" fill="#ffe4b5" opacity="0.6" />
    <!-- 窗帘缝隙 -->
    <line x1="325" y1="255" x2="325" y2="285" stroke="#1a1a2e" stroke-width="2" />

    <!-- 透过窗户看到的人影 -->
    <g opacity="0.4">
      <ellipse cx="320" cy="270" rx="6" ry="10" fill="#3a2a1a" />
    </g>

    <!-- 晾衣绳 -->
    <g stroke="#5a5a6e" stroke-width="0.5">
      <line x1="210" y1="230" x2="380" y2="230" />
      <line x1="430" y1="240" x2="570" y2="240" />
    </g>
    <!-- 衣服 -->
    <g fill="#4a4a5e" opacity="0.5">
      <rect x="240" y="230" width="15" height="20" rx="2" />
      <rect x="270" y="230" width="12" height="18" rx="2" />
      <rect x="310" y="230" width="14" height="22" rx="2" />
      <rect x="460" y="240" width="13" height="19" rx="2" />
      <rect x="500" y="240" width="15" height="21" rx="2" />
    </g>

    <!-- 空调外机 -->
    <g fill="#3a3a4e">
      <rect x="220" y="260" width="30" height="20" rx="2" />
      <rect x="380" y="270" width="25" height="18" rx="2" />
    </g>

    <!-- 地面 -->
    <rect x="0" y="330" width="800" height="170" fill="#1a1a2e" />
    <!-- 湿漉漉的地面反光 -->
    <g fill="#e94560" opacity="0.1">
      <ellipse cx="300" cy="380" rx="40" ry="5" />
      <ellipse cx="500" cy="400" rx="30" ry="4" />
    </g>
    <g fill="#00bcd4" opacity="0.08">
      <ellipse cx="450" cy="370" rx="35" ry="4" />
    </g>

    <!-- 路灯 -->
    <rect x="580" y="280" width="4" height="50" fill="#3a3a4e" />
    <ellipse cx="582" cy="278" rx="15" ry="8" fill="#ffd700" opacity="0.3" />
    <circle cx="582" cy="278" r="4" fill="#ffd700" opacity="0.6">
      <animate attributeName="opacity" values="0.4;0.7;0.4" dur="3s" repeatCount="indefinite" />
    </circle>

    <!-- 电动车 -->
    <g transform="translate(150, 340)">
      <ellipse cx="0" cy="15" rx="12" ry="12" fill="none" stroke="#4a4a5e" stroke-width="2" />
      <ellipse cx="40" cy="15" rx="12" ry="12" fill="none" stroke="#4a4a5e" stroke-width="2" />
      <path d="M5 5 L20 -10 L35 -10 L40 5" fill="none" stroke="#4a4a5e" stroke-width="2" />
      <rect x="15" y="-15" width="12" height="8" rx="2" fill="#3a3a4e" />
    </g>

    <!-- 夜空中的光污染 -->
    <ellipse cx="400" cy="50" rx="350" ry="80" fill="#e94560" opacity="0.05" />
  </svg>

  <!-- 2089年 拾忆实验室 -->
  <svg v-else-if="sceneId === 'scene_2089'" viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" class="scene-illustration">
    <defs>
      <linearGradient id="sky2089" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0a0a2e" />
        <stop offset="50%" stop-color="#0d1b3e" />
        <stop offset="100%" stop-color="#1a2a4e" />
      </linearGradient>
      <radialGradient id="holoGlow" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0%" stop-color="#4fc3f7" stop-opacity="0.4" />
        <stop offset="100%" stop-color="#4fc3f7" stop-opacity="0" />
      </radialGradient>
      <radialGradient id="brainGlow" cx="0.5" cy="0.5" r="0.5">
        <stop offset="0%" stop-color="#7c4dff" stop-opacity="0.3" />
        <stop offset="100%" stop-color="#7c4dff" stop-opacity="0" />
      </radialGradient>
      <filter id="holoFilter">
        <feGaussianBlur stdDeviation="2" />
      </filter>
    </defs>

    <!-- 深色背景 -->
    <rect width="800" height="500" fill="url(#sky2089)" />

    <!-- 网格线 -->
    <g stroke="#1a3a6e" stroke-width="0.3" opacity="0.3">
      <line v-for="i in 20" :key="'h'+i" x1="0" :y1="i*25" x2="800" :y2="i*25" />
      <line v-for="i in 32" :key="'v'+i" :x1="i*25" y1="0" :x2="i*25" y2="500" />
    </g>

    <!-- 实验室墙壁 -->
    <rect x="50" y="100" width="700" height="350" rx="8" fill="#1a2a4e" stroke="#2a4a7e" stroke-width="1" />

    <!-- 全息投影 - 大脑 -->
    <g>
      <ellipse cx="400" cy="200" rx="80" ry="60" fill="url(#brainGlow)" />
      <!-- 大脑轮廓 -->
      <path d="M360 200 Q370 160 400 155 Q430 160 440 200 Q445 230 420 245 Q400 250 380 245 Q355 230 360 200"
            fill="none" stroke="#7c4dff" stroke-width="1.5" opacity="0.6">
        <animate attributeName="opacity" values="0.4;0.7;0.4" dur="3s" repeatCount="indefinite" />
      </path>
      <!-- 神经网络线条 -->
      <g stroke="#4fc3f7" stroke-width="0.5" opacity="0.4">
        <line x1="370" y1="180" x2="390" y2="195">
          <animate attributeName="opacity" values="0.2;0.6;0.2" dur="2s" repeatCount="indefinite" />
        </line>
        <line x1="410" y1="175" x2="420" y2="190">
          <animate attributeName="opacity" values="0.3;0.6;0.3" dur="2.5s" repeatCount="indefinite" />
        </line>
        <line x1="380" y1="200" x2="400" y2="215">
          <animate attributeName="opacity" values="0.2;0.5;0.2" dur="1.8s" repeatCount="indefinite" />
        </line>
        <line x1="400" y1="190" x2="410" y2="210">
          <animate attributeName="opacity" values="0.3;0.5;0.3" dur="2.2s" repeatCount="indefinite" />
        </line>
      </g>
      <!-- 神经节点 -->
      <g fill="#4fc3f7">
        <circle cx="370" cy="180" r="2">
          <animate attributeName="opacity" values="0.3;0.8;0.3" dur="2s" repeatCount="indefinite" />
        </circle>
        <circle cx="410" cy="175" r="2">
          <animate attributeName="opacity" values="0.4;0.8;0.4" dur="2.5s" repeatCount="indefinite" />
        </circle>
        <circle cx="390" cy="195" r="2.5">
          <animate attributeName="opacity" values="0.3;0.7;0.3" dur="1.8s" repeatCount="indefinite" />
        </circle>
        <circle cx="420" cy="190" r="2">
          <animate attributeName="opacity" values="0.4;0.8;0.4" dur="2.2s" repeatCount="indefinite" />
        </circle>
        <circle cx="400" cy="215" r="2">
          <animate attributeName="opacity" values="0.3;0.7;0.3" dur="3s" repeatCount="indefinite" />
        </circle>
      </g>
    </g>

    <!-- 全息投影 - 记忆碎片漂浮 -->
    <g opacity="0.5">
      <rect x="300" y="140" width="30" height="20" rx="3" fill="none" stroke="#4fc3f7" stroke-width="0.8" transform="rotate(-15 315 150)">
        <animate attributeName="y" values="140;130;140" dur="4s" repeatCount="indefinite" />
      </rect>
      <rect x="470" y="150" width="25" height="18" rx="3" fill="none" stroke="#4fc3f7" stroke-width="0.8" transform="rotate(10 482 159)">
        <animate attributeName="y" values="150;138;150" dur="3.5s" repeatCount="indefinite" />
      </rect>
      <rect x="340" y="250" width="28" height="16" rx="3" fill="none" stroke="#7c4dff" stroke-width="0.8" transform="rotate(5 354 258)">
        <animate attributeName="y" values="250;240;250" dur="4.5s" repeatCount="indefinite" />
      </rect>
    </g>

    <!-- 躺椅 -->
    <g>
      <ellipse cx="400" cy="380" rx="80" ry="30" fill="#2a3a5e" stroke="#3a5a8e" stroke-width="1" />
      <path d="M330 380 Q330 350 360 340 L440 340 Q470 350 470 380" fill="#2a3a5e" stroke="#3a5a8e" stroke-width="1" />
      <!-- 神经接口 -->
      <circle cx="400" cy="340" r="8" fill="none" stroke="#4fc3f7" stroke-width="1" opacity="0.6">
        <animate attributeName="r" values="8;10;8" dur="2s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0.7;0.4" dur="2s" repeatCount="indefinite" />
      </circle>
    </g>

    <!-- 控制台 -->
    <g>
      <rect x="600" y="300" width="120" height="80" rx="6" fill="#1a2a4e" stroke="#2a4a7e" stroke-width="1" />
      <!-- 屏幕 -->
      <rect x="610" y="310" width="100" height="50" rx="4" fill="#0a1a3e" />
      <!-- 屏幕内容 -->
      <g fill="#4fc3f7" opacity="0.6">
        <rect x="620" y="320" width="40" height="3" rx="1" />
        <rect x="620" y="328" width="60" height="3" rx="1" />
        <rect x="620" y="336" width="35" height="3" rx="1" />
        <rect x="620" y="344" width="50" height="3" rx="1" />
      </g>
      <!-- 指示灯 -->
      <circle cx="630" cy="370" r="3" fill="#4caf50">
        <animate attributeName="opacity" values="0.5;1;0.5" dur="1.5s" repeatCount="indefinite" />
      </circle>
      <circle cx="645" cy="370" r="3" fill="#ff9800">
        <animate attributeName="opacity" values="0.3;0.7;0.3" dur="2s" repeatCount="indefinite" />
      </circle>
    </g>

    <!-- 小雨坐在控制台前 -->
    <g>
      <!-- 身体 -->
      <ellipse cx="660" cy="350" rx="18" ry="25" fill="#3a4a6e" />
      <!-- 头 -->
      <circle cx="660" cy="318" r="12" fill="#e8c4a0" />
      <!-- 头发 -->
      <path d="M648 315 Q650 305 660 303 Q670 305 672 315" fill="#2a1a0a" />
      <path d="M648 315 Q645 325 648 335" fill="#2a1a0a" />
      <path d="M672 315 Q675 325 672 335" fill="#2a1a0a" />
      <!-- 手里的照片 -->
      <rect x="670" y="345" width="15" height="10" rx="1" fill="#ffe4b5" opacity="0.8" transform="rotate(-10 677 350)" />
    </g>

    <!-- 淡蓝色光粒子 -->
    <g>
      <circle cx="200" cy="200" r="1.5" fill="#4fc3f7" opacity="0.4">
        <animate attributeName="cy" values="200;180;200" dur="5s" repeatCount="indefinite" />
      </circle>
      <circle cx="350" cy="150" r="1" fill="#4fc3f7" opacity="0.3">
        <animate attributeName="cy" values="150;130;150" dur="4s" repeatCount="indefinite" />
      </circle>
      <circle cx="500" cy="180" r="1.5" fill="#7c4dff" opacity="0.3">
        <animate attributeName="cy" values="180;160;180" dur="6s" repeatCount="indefinite" />
      </circle>
      <circle cx="650" cy="220" r="1" fill="#4fc3f7" opacity="0.4">
        <animate attributeName="cy" values="220;200;220" dur="4.5s" repeatCount="indefinite" />
      </circle>
      <circle cx="150" cy="300" r="1.2" fill="#7c4dff" opacity="0.3">
        <animate attributeName="cy" values="300;280;300" dur="5.5s" repeatCount="indefinite" />
      </circle>
    </g>

    <!-- 环境光 -->
    <ellipse cx="400" cy="200" rx="250" ry="150" fill="#4fc3f7" opacity="0.05" />
  </svg>

  <!-- 默认场景 -->
  <svg v-else viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" class="scene-illustration">
    <rect width="800" height="500" fill="#1a1a3e" />
    <text x="400" y="250" text-anchor="middle" fill="#4fc3f7" font-size="24" opacity="0.3">记忆碎片...</text>
  </svg>
</template>

<style scoped>
.scene-illustration {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 8px;
}
</style>
