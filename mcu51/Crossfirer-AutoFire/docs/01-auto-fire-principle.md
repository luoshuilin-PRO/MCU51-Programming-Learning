# 01 - 自动开火原理

Crossfirer 的这一功能不是读取游戏内存，而是观察屏幕像素。

核心思路：

```text
游戏画面
   ↓
取得游戏窗口位置
   ↓
扫描准星附近/红名出现区域
   ↓
PixelSearch 搜索目标颜色
   ↓
Shoot_Time() 返回 True
   ↓
AutoFire() 根据当前模式决定动作
   ↓
发送鼠标左键
```

## 第一批需要认识的符号

- `AutoMode`：自动开火总开关。
- `mo_shi`：当前射击模式。
- `AutoFire(...)`：自动开火主循环。
- `Shoot_Time(...)`：判断现在是否满足开火条件。
- `PixelSearch`：AutoHotkey 的屏幕颜色搜索命令。
- `LButton`：鼠标左键。
- `press_key()`：上游公共函数提供的按键/鼠标输入封装。

下一课从 `Crossfirer_Shooter.original.ahk` 文件顶部开始逐段阅读。
