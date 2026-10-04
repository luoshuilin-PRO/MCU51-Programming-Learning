# Crossfirer 自动开火模块学习项目

本目录从 JiaPai12138/Crossfirer 中单独提取“自动开火（AutoFire / trigger-bot）”部分，用于源码阅读和 AutoHotkey 图像/颜色检测学习。

## 来源

- 上游项目：JiaPai12138/Crossfirer
- 上游文件：Crossfirer_v2.x/Crossfirer_Shooter.ahk
- 上游许可证：GNU GPL v3
- 本目录保留原始源码副本与 GPL-3.0 许可证。

## 先学什么

自动开火最重要的执行链：

1. 热键/模式控制
2. `AutoFire()` 主循环
3. `Shoot_Time()` 判断是否出现目标红名
4. `PixelSearch` 在屏幕指定区域搜索颜色
5. 条件成立后通过 `press_key("LButton", ...)` 产生鼠标左键输入

原始 Shooter 文件还通过 `#Include Crossfirer_Functions.ahk` 依赖上游公共函数，因此当前先作为“源码提取与阅读项目”，不把 Crossfirer 的压枪、自瞄、挂机、C4 等其他模块复制进来。

## 学习路线

- Lesson 01：看懂 AHK 文件入口、global、热键与 #If
- Lesson 02：拆解 AutoFire() 循环
- Lesson 03：理解屏幕坐标 X/Y/W/H
- Lesson 04：理解 PixelSearch 和颜色值
- Lesson 05：拆解 Shoot_Time()
- Lesson 06：理解鼠标事件 press_key()
- Lesson 07：把上游公共函数依赖逐步改造成最小独立版本

> 目标不是一次搬完整 Crossfirer，而是把自动开火模块逐步“去依赖”，最终形成可独立阅读、测试和修改的小项目。
