# 双 ESP32-S3 HID 透传与视觉触发：项目规划记录

> 记录日期：2026-10-04  
> 当前阶段：规划完成，下一步先连接单块硬件确认信息，暂不接 SPI、暂不烧录 macroPassthrough。

## 1. 项目目标

使用两块 ESP32-S3 N16R8 搭建 USB HID 鼠标透传系统，并逐步加入 PC 端颜色/像素识别和宏功能。

最终数据链：

```text
真实鼠标
   ↓ USB
ESP32-S3 A：USB Host
   ↓ SPI
ESP32-S3 B：USB HID Device
   ↓ USB
Windows

Windows 屏幕
   ↓
ROI / 像素 / HSV 颜色识别
   ↓
Trigger
   ↓
ESP32-S3
   ↓
HID 左键 / 后续 Macro Engine
```

第一版只追求最小闭环：**颜色识别成功 → Trigger → ESP32-S3 → HID 左键单击一次**。罗技宏转换放在这个闭环验证成功之后。

## 2. 参考项目

上游项目：`arfevrier/macroPassthrough`

其核心架构：

- `usb-input`：ESP32-S3 A，USB Host + SPI Master，读取真实鼠标/键盘 HID Report。
- `usb-output`：ESP32-S3 B，SPI Slave + TinyUSB HID Device，向 Windows 输出 HID Report。
- 两块 S3 之间使用 SPI 通信。
- Output 端源码已经包含 Macro 相关结构，后续可作为宏引擎研究入口。

## 3. 已确认的上游 SPI GPIO

GPIO 定义不在两个 `config.h` 中，而在：

```text
usb-input/main/macpass_spi.h
usb-output/main/macpass_spi.h
```

### HID Report 通道（SPI2）

Input 为 Master/Sender，Output 为 Slave/Receiver：

```text
MOSI = GPIO39
MISO = GPIO40
SCLK = GPIO41
CS   = GPIO42
```

### PC 返回通道（SPI3）

Output 为 Master/Sender，Input 为 Slave/Receiver，用于 PC 输出报告，例如键盘 LED：

```text
MOSI2 = GPIO38
MISO2 = GPIO37
SCLK2 = GPIO36
CS2   = GPIO35
```

如果完全按照原版固件，两块板同号 GPIO 对接并共地：

```text
INPUT              OUTPUT
GPIO39  ─────────  GPIO39
GPIO40  ─────────  GPIO40
GPIO41  ─────────  GPIO41
GPIO42  ─────────  GPIO42

GPIO38  ─────────  GPIO38
GPIO37  ─────────  GPIO37
GPIO36  ─────────  GPIO36
GPIO35  ─────────  GPIO35

GND     ─────────  GND
```

**注意：目前不要按此表直接接线。** 用户的开发板为 ESP32-S3 N16R8（16 MB Flash + 8 MB PSRAM），在确认实际模组、PSRAM 配置及 GPIO 可用性前，不决定是否沿用 GPIO35~42。必要时修改两端 `macpass_spi.h` 重新映射 SPI GPIO。

## 4. 用户现有硬件

两块相同的 ESP32-S3 N16R8 开发板。

商家引脚图显示：

- ESP32-S3
- N16：16 MB Flash
- R8：8 MB PSRAM
- 双 USB-C
- GPIO19 = USB D-
- GPIO20 = USB D+
- BOOT / RST
- GPIO35~42 均有引出

GPIO19/20 属于原生 USB 数据线，当前规划不拿它们作为 SPI GPIO。

## 5. 当前决定：先确认硬件，再烧录，再接线

为了减少排错变量，采用以下顺序：

```text
1. ESP32-S3 A 单独连接 Windows
        ↓
2. 确认两个 USB-C 各自用途
        ↓
3. 确认芯片识别
        ↓
4. 确认 Flash = 16 MB
        ↓
5. 确认 PSRAM = 8 MB / 类型
        ↓
6. 确认 GPIO35~42 是否适合当前 N16R8 配置
        ↓
7. ESP32-S3 B 做相同确认
        ↓
8. 决定沿用或修改 macroPassthrough SPI GPIO
        ↓
9. 编译固件
        ↓
10. A 烧录 usb-input
        ↓
11. B 烧录 usb-output
        ↓
12. 两块板断电
        ↓
13. 按最终 GPIO 表连接 SPI + GND
        ↓
14. 上电测试原版 HID 透传
```

烧录固件本身不要求两块 S3 已经通过 SPI 相连，因此优先独立确认、独立烧录。

## 6. 第一阶段验收标准

暂时不加入颜色识别和宏。

```text
真实鼠标
   ↓
S3 A
   ↓ SPI
S3 B
   ↓
Windows
```

必须确认：

- 鼠标移动正常
- 左键正常
- 右键正常
- 滚轮正常
- 透传稳定

只有原版透传通过，才继续增加功能。

## 7. 第二阶段：最小视觉触发

透传成功后，不立即做复杂罗技宏。

先验证：

```text
PC 测试画面 / 《星露谷物语》
        ↓
固定 ROI
        ↓
像素或 HSV 颜色识别
        ↓
MATCH
        ↓
发送 Trigger
        ↓
ESP32-S3
        ↓
Left Down
        ↓
短延时
        ↓
Left Up
```

PC 端第一版计划做成 CMD/PowerShell 控制台形式，显示 ROI、目标颜色、命中率、Trigger 状态等。

颜色检测优先路线：

1. 固定像素测试
2. 小 ROI
3. HSV 阈值
4. 像素数量/占比
5. 连续帧确认
6. Cooldown
7. 后续需要时再考虑模板匹配

## 8. 第三阶段：罗技宏转换

在“颜色识别 → ESP32 单击”闭环稳定以后，再研究 Logitech Lua → ESP32 Macro Engine。

目标不是让 ESP32 直接运行 Logitech Lua，而是转换语义，例如：

```lua
PressMouseButton(1)
Sleep(40)
ReleaseMouseButton(1)
```

转换为自己的中间宏格式，例如：

```text
DOWN L
WAIT 40
UP L
END
```

ESP32 固件长期保存 Macro Engine；具体宏以后可以考虑运行时加载到 RAM，而不是每修改一个宏就重新烧录整个固件。

## 9. 下一次继续的位置

**下一步只做一件事：拿一块 ESP32-S3 N16R8，通过 USB 连接 Windows，确认硬件信息。**

此时：

- 不接两块板之间的 SPI。
- 不急着烧录 macroPassthrough。
- 不安装 OpenCV。
- 不做罗技宏转换。

确认硬件和最终 GPIO 后，再进入 ESP-IDF 编译/烧录阶段。
