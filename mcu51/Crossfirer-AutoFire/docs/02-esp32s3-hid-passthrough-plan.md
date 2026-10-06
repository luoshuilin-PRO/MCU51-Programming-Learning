# 双 ESP32-S3 HID 透传与视觉触发：项目规划记录

> 记录日期：2026-10-04  
> 当前阶段（2026-10-05）：Windows 已安装 ESP-IDF，ESP32-S3 已能以 COM3 正常识别。下一步先由 Codex 复核仓库、A/B 固件与真实 GPIO 定义，再分别编译/烧录 A、B 两块板，最后按确认后的接线表连接 SPI。

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


---

# 10. 2026-10-05 更新：Codex 全自动分析、编译、烧录执行规范

## 10.1 当前已知环境

Windows：

```text
Windows 10
```

ESP-IDF 已安装在：

```text
C:\Espressif
```

当前普通 CMD 中直接执行 `idf.py` 可能找不到，因为普通 CMD 尚未加载 ESP-IDF 环境变量；这不代表 ESP-IDF 未安装。

已确认目录包括：

```text
C:\Espressif\frameworks
C:\Espressif\python_env
C:\Espressif\tools
C:\Espressif\idf-env.exe
C:\Espressif\idf_cmd_init.bat
```

系统 Python 已存在，不重新安装。ESP-IDF 如有自己的 Python 虚拟环境，优先使用 ESP-IDF 自带环境。

当前其中一块 ESP32-S3 已经通过 Windows 正常识别为：

```text
COM3
```

硬件：

```text
2 × ESP32-S3 N16R8
Flash = 16 MB
PSRAM = 8 MB
```

定义：

```text
A 板 = INPUT  = usb-input
B 板 = OUTPUT = usb-output
```

## 10.2 Codex 的工作原则

Codex 的任务不是“告诉用户如何操作”，而是：

```text
检查
→ 执行
→ 读取结果
→ 分析错误
→ 修复
→ 继续执行
```

凡是电脑能够完成的工作，全部由 Codex 自己完成，包括：

- Git 仓库检查
- ESP-IDF 环境加载
- Python / Git / CMake / Ninja / esptool 检查
- COM 端口检查
- 芯片识别
- 源码搜索
- GPIO 分析
- build
- flash
- monitor
- 日志分析
- 必要的软件配置修改

不要让用户复制命令、打开 CMD 或手动执行 `idf.py`。

只有以下物理动作允许要求用户参与：

- 插拔 USB
- 指定当前实体板是 A 还是 B
- 按 BOOT / RESET（仅自动下载失败后）
- 连接杜邦线
- 检查实体开发板丝印

## 10.3 第一阶段：禁止立即烧录

第一阶段必须先分析当前上游仓库：

```text
https://github.com/arfevrier/macroPassthrough
```

依次检查：

```text
README.md
usb-input/
usb-output/
CMakeLists.txt
sdkconfig
sdkconfig.defaults
idf_component.yml
partitions.csv
main/
components/
config.h
macpass_spi.h
```

同时记录：

- 当前 branch
- 当前 commit
- 当前仓库建议的 ESP-IDF 版本
- GitHub Actions / CI 实际使用的 ESP-IDF 版本
- usb-input 和 usb-output 的真实构建入口

不能因为本机装了某个 ESP-IDF 版本，就直接假设一定兼容。

## 10.4 第一优先级：重新确认 A/B 两块板的硬件接口

必须重新从**当前版本源码**中搜索：

```text
MOSI
MISO
SCLK
SCK
CLK
CS
SS
SPI
SPI_HOST
GPIO
GPIO_NUM_
PIN
PIN_NUM
USB
UART
HID
```

重点确认：

```text
usb-input/main/macpass_spi.h
usb-output/main/macpass_spi.h
```

历史记录中的原版 GPIO 是：

### HID Report 通道

```text
MOSI = GPIO39
MISO = GPIO40
SCLK = GPIO41
CS   = GPIO42
```

### PC 返回 / LED 通道

```text
MOSI2 = GPIO38
MISO2 = GPIO37
SCLK2 = GPIO36
CS2   = GPIO35
```

但是 Codex **不得直接相信历史记录**。

必须重新以当前仓库源码为准确认：

- A 板角色
- B 板角色
- 哪一侧是 SPI Master
- 哪一侧是 SPI Slave
- 是否确实存在两组 SPI
- 每一组 SPI 的真实 GPIO
- PC LED / Output Report 是否走独立返回 SPI

## 10.5 SPI 接线判断规则

不要机械理解为：

```text
MOSI → MISO
```

必须根据 ESP-IDF SPI Master / Slave API 和项目源码确认信号方向。

如果两端源码对同一条总线都使用相同信号命名，则通常应理解为：

```text
Master MOSI → Slave MOSI
Master MISO ← Slave MISO
Master SCLK → Slave SCLK
Master CS   → Slave CS
GND         → GND
```

最终必须输出真实的：

```text
A GPIOxx → B GPIOxx
```

接线表，而不是只给 SPI 名称。

## 10.6 N16R8 GPIO 兼容性检查

确定源码 GPIO 后，再检查 ESP32-S3 N16R8：

- 16 MB Flash
- 8 MB PSRAM
- OPI / Octal PSRAM
- GPIO19 / GPIO20 原生 USB
- BOOT / strapping pins
- JTAG
- UART
- 板载 LED
- 其他板载资源

重点确认 GPIO35~42 是否：

1. 芯片层面可用于当前用途；
2. 没有与 N16R8 的 Flash / PSRAM 配置发生冲突；
3. 在用户这块具体开发板上确实已经引出。

如果仅靠源码和 ESP32-S3 芯片资料无法确认具体开发板排针，则明确要求查看板子丝印或原理图，但不能因此停止软件分析。

## 10.7 烧录前必须先给出接线定义

在任何正式 flash 之前，先输出类似：

```text
A INPUT                    B OUTPUT
GPIOxx ------------------ GPIOxx
GPIOxx ------------------ GPIOxx
GPIOxx ------------------ GPIOxx
GPIOxx ------------------ GPIOxx

第二组 SPI：
GPIOxx ------------------ GPIOxx
GPIOxx ------------------ GPIOxx
GPIOxx ------------------ GPIOxx
GPIOxx ------------------ GPIOxx

GND    ------------------ GND
```

此阶段只确认方案，**不要立即让用户接线**。

两块板先分别独立 USB 连接、独立识别、独立烧录。

## 10.8 ESP-IDF 环境自动检查

完成源码和 GPIO 分析后，Codex 自动检查：

```text
ESP-IDF
Python
Git
CMake
Ninja
esptool
xtensa-esp32s3-elf
```

如果普通 CMD 中 `idf.py` 不可用：

自行寻找并加载：

```text
C:\Espressif\frameworks\...
export.bat
```

或者安装器提供的初始化脚本。

目标是让：

```text
idf.py --version
```

正常工作。

不要因为普通 CMD 没有 PATH 就重新安装 ESP-IDF。

## 10.9 COM3 芯片确认

当前已知有一块板在：

```text
COM3
```

正式烧录前先执行当前 ESP-IDF / esptool 版本对应的芯片识别命令，例如：

```text
python -m esptool --port COM3 chip-id
```

或当前版本的等效命令。

确认至少包括：

- COM3 可访问
- 设备确实为 ESP32-S3
- bootloader 通信正常
- Flash 可访问

COM3 只表示当前连接设备，不永久等于 A 板。

如果无法通过软件知道实体板身份，允许要求用户仅确认一次：

```text
当前 COM3 是否是准备作为 A INPUT 的板子？
```

确认后将该实体板固定定义为 A。

## 10.10 A 板：usb-input

A 板必须使用：

```text
usb-input
```

流程：

```text
进入 usb-input
→ 检查 CMake / sdkconfig / dependencies
→ 必要时 fullclean
→ set-target esp32s3
→ build
→ 检查构建结果
→ flash
→ monitor
```

原则：

- 不随意覆盖项目原始 sdkconfig；
- 只有发现 Flash、PSRAM、USB、partition 等配置确实与 N16R8 不兼容时才修改；
- 所有源码 / 配置修改必须通过 `git diff` 可追踪；
- 第一次优先普通 flash，不默认 `erase-flash`。

如果普通烧录失败，再检查：

- COM 被占用
- bootloader
- DTR / RTS 自动复位
- target
- CMake cache
- build 目录
- partition
- Flash mode / size
- PSRAM
- ESP-IDF 版本
- component dependencies

只有确定旧 Flash 内容影响当前固件时，才考虑 `erase-flash`。

## 10.11 A 板启动日志检查

烧完 A 后打开 monitor，检查：

```text
Guru Meditation
panic
watchdog
brownout
reboot loop
USB Host error
SPI error
PSRAM init failure
Flash size mismatch
partition error
assert
heap failure
```

确认 A 正常启动后，再进入 B。

## 10.12 B 板：usb-output

A 完成后，用户只负责：

```text
拔下 A
连接准备作为 B OUTPUT 的第二块 ESP32-S3
```

Codex 重新扫描串口。

不要假设 B 一定还是 COM3。

B 板必须使用：

```text
usb-output
```

流程与 A 相同：

```text
检查环境
→ 检查 target
→ build
→ flash
→ monitor
```

重点检查：

- TinyUSB
- USB HID Device
- SPI Slave
- Macro Engine
- Flash
- PSRAM
- partition
- panic / reset loop

不得把 `usb-input` 烧到 B，也不得把 `usb-output` 烧到 A。

## 10.13 两块板都烧完后才实际接 SPI

只有 A、B 都独立烧录并启动正常后：

1. 两块板断电；
2. 再按最终确认的 GPIO 表连接 SPI；
3. A 与 B 必须共地；
4. 再分别连接所需 USB；
5. 启动 passthrough 测试。

第一阶段目标只有：

```text
真实鼠标 / 键盘
        ↓
A INPUT
        ↓
SPI
        ↓
B OUTPUT
        ↓
Windows
```

验收：

- 鼠标移动
- 左键
- 右键
- 滚轮
- 键盘基础按键
- USB HID 枚举
- SPI 稳定
- 无异常重启

## 10.14 暂时不加入高级功能

原版 passthrough 没有稳定之前，不做：

- 图像识别
- HSV / 像素识别
- Logitech Lua 转换
- 自动宏
- 自动压枪
- 复杂 Macro Engine 修改

顺序保持：

```text
原版透传成功
→ 最小颜色识别 Trigger
→ 单次 HID 点击
→ 再研究 Logitech Lua → 自定义 Macro Engine
```

## 10.15 Codex 遇错时的处理规则

不要因为一个命令失败就停止。

Codex 应自己：

```text
读取完整日志
→ 提出原因假设
→ 验证
→ 修复
→ 重新 build / flash / monitor
```

优先排查：

- COM 占用
- 错误 COM
- ESP-IDF 环境
- Python 虚拟环境
- Git / submodule
- CMake
- Ninja
- component dependency
- ESP-IDF version mismatch
- sdkconfig
- Flash mode / size
- PSRAM
- partition
- USB CDC / Serial-JTAG
- TinyUSB
- SPI pins / SPI host
- watchdog
- brownout
- 供电

只有遇到必须实体操作的问题时才停止，例如：

```text
需要人工按 BOOT
需要 RESET
需要更换 USB 口/线
需要插拔另一块板
需要接线
```

并明确报告：

```text
自动流程被物理操作阻塞
```

同时说明已经完成到哪一步。

## 10.16 推荐执行阶段

为了降低双板硬件部署的变量，整个任务分三阶段：

### 阶段 1：分析，不烧录

```text
仓库确认
→ branch / commit
→ usb-input / usb-output 结构
→ GPIO 复核
→ 两组 SPI 复核
→ N16R8 冲突检查
→ 最终 A/B 接线定义
→ ESP-IDF 环境
→ COM3 芯片确认
```

### 阶段 2：A 板

```text
usb-input
→ build
→ flash
→ monitor
```

### 阶段 3：B 板

```text
usb-output
→ 自动重新识别 COM
→ build
→ flash
→ monitor
→ 两板断电
→ 接 SPI + GND
→ passthrough 验证
```

## 10.17 Codex 模型和难度记录

任务复杂度评估：

```text
整体：约 7 / 10
软件部分：约 5 / 10
主要难点：双板角色、两套固件、两组 SPI、USB Host/Device、N16R8 GPIO/PSRAM、实体板身份和接线
```

优先使用高推理能力的 Codex 模型执行第一次完整部署。

核心原则：

> 第一次部署宁可让模型多检查一次，也不要在 GPIO、A/B 固件或 Flash/PSRAM 配置尚未确认时直接烧录。

## 10.18 最终执行报告模板

Codex 最终应给出：

### Environment

```text
Windows:
ESP-IDF:
Python:
Git:
CMake:
Ninja:
esptool:
```

### Repository

```text
URL:
Branch:
Commit:
```

### A INPUT

```text
Project:
Chip:
COM:
Flash:
PSRAM:
Build:
Flash result:
Boot:
USB Host:
```

### B OUTPUT

```text
Project:
Chip:
COM:
Flash:
PSRAM:
Build:
Flash result:
Boot:
USB HID:
```

### SPI HID Data

```text
A MOSI:
A MISO:
A CLK:
A CS:

B MOSI:
B MISO:
B CLK:
B CS:
```

### SPI Return / LED

```text
A MOSI:
A MISO:
A CLK:
A CS:

B MOSI:
B MISO:
B CLK:
B CS:
```

### Wiring

给出完整：

```text
A GPIOxx → B GPIOxx
```

接线表。

### Validation

```text
Keyboard passthrough:
Mouse passthrough:
USB HID:
SPI:
Boot logs:
```

### Modifications

列出：

```text
git diff
```

以及所有修改过的文件。

---

## 11. 当前下一步

现在的实际下一步已经从“确认是否安装 ESP-IDF”推进到：

```text
1. 让 Codex 打开 / clone macroPassthrough
2. 重新核对 usb-input / usb-output
3. 重新核对 macpass_spi.h 的两组 GPIO
4. 检查 GPIO35~42 对当前 ESP32-S3 N16R8 是否安全
5. 加载 C:\Espressif 的 ESP-IDF 环境
6. 用 COM3 识别当前 ESP32-S3
7. 先停在这里审核结果
8. 然后烧 A
9. 再换 B 并烧 B
10. 两块板断电后再按最终表接 SPI + GND
11. 验证原版 HID passthrough
```

**当前仍然不应直接进入颜色识别或罗技宏转换。**


---

# 12. 2026-10-06 更新：G502 侧键识别与 B 板诊断固件

## 12.1 当前现象

双 ESP32-S3 透传已经推进到鼠标宏测试阶段。

当前硬件角色继续保持：

```text
A 板 = INPUT  = usb-input
B 板 = OUTPUT = usb-output
```

当前已知板卡身份：

```text
A:
COM3
MAC = ac:a7:04:e2:7e:88

B:
COM4
MAC = 14:c1:9f:39:f4:94
```

当前鼠标为 Logitech G502 新版。

B 板串口日志已经确认：

```text
Project name: usb-keyboard-output
Flash: 16 MB
PSRAM: 8 MB
usb-output started
```

启动初期出现一次：

```text
SPI HID Receive: SPI received transmission invalid with => 0; 0;
```

但后续实际鼠标操作已经能触发当前自定义宏状态，例如：

```text
macro_v1: enabled=1 mode=1 action=1
macro_v1: enabled=1 mode=1 action=0

macro_v1: enabled=1 mode=2 action=2
macro_v1: enabled=1 mode=2 action=0
```

这说明 A → SPI → B 的鼠标事件链路至少已经部分工作。

当前真正的问题不是“完全收不到鼠标”，而是：

> 当前日志只打印宏逻辑解释后的 action，没有打印原始 HID mouse buttons，因此还无法确认 G502 前进 / 后退侧键实际对应哪个 bit / value。

## 12.2 当前诊断目标

暂时不要继续调整正式宏逻辑。

先制作一个 **B 板诊断版 usb-output 固件**。

诊断版与正常固件保持相同透传和宏功能，只增加鼠标原始 HID 日志：

```text
A 接真实鼠标
    ↓
A usb-input
    ↓ SPI
B usb-output
    ↓
打印原始 mouse report
    ↓
原宏逻辑
    ↓
USB HID Device
```

诊断目标：

依次按 G502：

```text
左键
右键
中键
后退侧键
前进侧键
滚轮
滚轮左倾
滚轮右倾
DPI / 狙击键（如果这些键产生 HID 数据）
```

记录每次对应的：

```text
buttons
x
y
wheel
pan
```

重点确认前进 / 后退是否属于：

```text
0x08
0x10
```

或者其他值。

不要预设具体值，必须以实际串口日志为准。

## 12.3 建议加入的诊断日志

文件：

```text
usb-output/main/macpass_macro.c
```

在鼠标分支：

```c
} else if (report->header == HEADER_HID_MOUSE){
```

进入后，临时增加：

```c
ESP_LOGI("MOUSE_RAW",
         "buttons=0x%02X x=%d y=%d wheel=%d pan=%d",
         report->event.mouse.buttons,
         report->event.mouse.x,
         report->event.mouse.y,
         report->event.mouse.wheel,
         report->event.mouse.pan);
```

期望结构类似：

```c
} else if (report->header == HEADER_HID_MOUSE){

    ESP_LOGI("MOUSE_RAW",
             "buttons=0x%02X x=%d y=%d wheel=%d pan=%d",
             report->event.mouse.buttons,
             report->event.mouse.x,
             report->event.mouse.y,
             report->event.mouse.wheel,
             report->event.mouse.pan);

    last_mouse_report = report->event.mouse;
```

不要修改 `hid_mouse_report_t` 的结构，不要先重写宏系统。

## 12.4 B 板诊断版编译与烧录

项目：

```text
C:\Users\Administrator\Documents\ESP32\macroPassthrough\usb-output
```

B 板当前端口：

```text
COM4
```

编译、烧录、监视：

```powershell
idf.py build
idf.py -p COM4 flash monitor
```

如果当前 ESP-IDF 5.4 环境可完成现有 usb-output 的 build/flash，则先使用现有环境完成诊断。

如果出现构建 API 兼容问题，再切换 ESP-IDF 5.5.4。

不要为了这个诊断任务重新设计整个工程。

## 12.5 诊断输出解释

理想情况下：

```text
无按键:
buttons=0x00

左键:
buttons=0x01

右键:
buttons=0x02

中键:
buttons=0x04
```

标准 HID 鼠标常见：

```text
Button 4:
0x08

Button 5:
0x10
```

但 Logitech G502 可能存在：

- Report ID
- 多 HID Interface
- Vendor-defined HID Report
- Consumer Control
- Logitech 自定义接口

因此侧键实际值必须现场测量。

如果：

```text
左/右/中键变化
前进/后退 buttons 完全不变化
```

则下一步转向 A 板 USB Host 原始报告抓取。

## 12.6 若 B 板 buttons 看不到侧键：A 板抓 RAW HID

文件：

```text
usb-input/main/macpass_usb.c
```

在：

```c
HID_HOST_INTERFACE_EVENT_INPUT_REPORT
```

收到：

```c
hid_host_device_get_raw_input_report_data(...)
```

以后打印：

- data_length
- subclass
- proto
- raw bytes

例如临时加入：

```c
ESP_LOGI("HID_RAW",
         "len=%u data=%02X %02X %02X %02X %02X %02X %02X %02X",
         (unsigned)data_length,
         data[0], data[1], data[2], data[3],
         data[4], data[5], data[6], data[7]);
```

目的：

判断 G502 侧键到底：

1. A 板根本没有收到；
2. A 板收到但固定 `hid_mouse_report_t` 解析丢失；
3. A 收到、SPI 也发送，但 B 宏逻辑未识别。

## 12.7 特别检查：Boot Protocol

当前上游 `usb-input/main/macpass_usb.c` 对 Boot Interface 调用：

```c
hid_class_request_set_protocol(
    hid_device_handle,
    HID_REPORT_PROTOCOL_BOOT
);
```

这可能是 G502 扩展侧键丢失的重要原因。

Boot Mouse Protocol 主要面向最基础鼠标兼容。

如果 RAW 测试证明：

- Boot 模式下只有基础鼠标键；
- G502 扩展侧键没有出现在当前报告；

则下一阶段验证：

```text
Keyboard → BOOT protocol
Mouse    → REPORT protocol
```

即鼠标不要强制切 Boot Protocol。

但当前阶段不要直接改协议，先抓 RAW 数据确认。

## 12.8 Codex 当前任务

Codex 接手时应执行：

```text
1. 读取本文件第 12 节
2. 打开 macroPassthrough 本地仓库
3. git status / git diff，保护当前已有修改
4. 确认 B = COM4 / MAC 14:c1:9f:39:f4:94
5. 在 usb-output/main/macpass_macro.c 增加最小 MOUSE_RAW 日志
6. 不修改正式宏逻辑
7. build
8. flash COM4
9. monitor COM4
10. 提示用户依次按 G502 各按键
11. 根据输出建立 G502 按键表
12. 确认 forward/back 实际 buttons 值
13. 如果侧键没有出现在 buttons，则转到 A 板 RAW HID 抓包
14. 最终只在事实明确后修复正式宏
```

## 12.9 Codex 必须输出的 G502 记录表

```text
G502 Button Map

Left:
Right:
Middle:
Back:
Forward:
Wheel Up:
Wheel Down:
Wheel Tilt Left:
Wheel Tilt Right:
DPI:
Sniper:

Report length:
Report ID:
Mouse buttons byte:
Raw bytes:
```

## 12.10 当前原则

当前阶段的目标不是继续增加功能，而是：

> 准确测量 G502 每个实体按键进入 ESP32-S3 后的真实 HID 数据。

先测量，再修复。

这样可以避免错误地把：

```text
forward = 某个 action
back = 某个 action
```

写死，而不知道真实 HID 来源。



---

# 13. 2026-10-07 更新：外置硬件视觉节点（ESP32-S3-CAM + OV2640）

## 13.1 本次讨论结论

在现有“双 ESP32-S3 HID 透传”项目之外，增加一条独立的硬件视觉实验路线。它不是替换现有 A/B 两块 ESP32-S3，而是增加第三个视觉节点。

当前仅记录设计，暂不要求购买、接线或烧录。

## 13.2 候选硬件

计划候选：

```text
ESP32-S3-CAM N16R8
+
OV2640 摄像头
```

优先购买“ESP32-S3-CAM + OV2640”完整套装，而不是只买无摄像头单板。

当前已有硬件保持：

```text
A = 普通 ESP32-S3 N16R8 / INPUT / USB Host
B = 普通 ESP32-S3 N16R8 / OUTPUT / USB HID Device
```

新增：

```text
C = ESP32-S3-CAM N16R8 + OV2640 / Vision
```

## 13.3 三板架构

```text
                    ┌────────────────────────────┐
显示器 ──光学画面──>│ C: S3-CAM + OV2640        │
                    │ ROI / RGB565 / HSV 判断    │
                    └─────────────┬──────────────┘
                                  │ GPIO / UART
                                  ▼
真实鼠标 → A: USB Host → SPI → B: USB HID Device → PC
```

C 板只负责“看”和“判断”；A/B 继续负责原有 HID 透传。

## 13.4 适合的视觉任务

S3-CAM + OV2640 第一阶段不做复杂 AI/人物识别，而定位为轻量“电子眼/颜色传感器”：

```text
摄像头取图
→ 固定 ROI
→ RGB565 或 HSV
→ 判断指定颜色范围
→ 统计目标颜色像素数量/比例
→ 连续帧确认
→ 输出 Trigger
```

适合实验：

- 红/绿/蓝等固定颜色标记检测
- 指示灯亮灭检测
- UI 状态块颜色变化
- 自己制作的测试画面/单机自动化实验
- MCU 视觉传感器实验

不把简单颜色阈值当作复杂语义目标识别。

## 13.5 与 PC 软件视觉方案并存

保留两条路线用于学习和延迟对比。

### A. PC 软件视觉

```text
Windows/GPU 画面
→ ROI / RGB / HSV
→ COM/UART
→ B
→ HID
```

特点：速度和颜色稳定性通常更好，适合作为性能基准。

### B. 外置硬件视觉

```text
显示器
→ OV2640
→ S3-CAM
→ ROI / RGB565 / HSV
→ GPIO/UART
→ B
→ HID
```

特点：不依赖 Windows 截屏；更适合学习摄像头、framebuffer、颜色空间、GPIO/UART 和嵌入式视觉。

## 13.6 为什么选择 OV2640

当前任务只需要低分辨率 ROI 和颜色阈值，不需要高像素拍照。

开发方向优先：

```text
QVGA / 更低分辨率
PIXFORMAT_RGB565
PSRAM framebuffer
固定 ROI
```

这样比追求高分辨率更符合实时颜色检测用途。

## 13.7 C → B 通信的第一版

第一版优先使用最简单的 GPIO Trigger：

```text
C GPIO OUT ───── B GPIO IN
C GND      ───── B GND
```

检测条件满足：

```text
C 输出触发沿
→ B 收到
→ 执行测试事件
```

等需要传递多种命令后，再升级 UART：

```text
C TX → B RX
C RX ← B TX
GND  ↔ GND
```

并设计独立命令协议。

## 13.8 固件策略

新增 C 板需要单独的 Camera/Vision 固件。

原 A 板原则上不因为视觉节点而修改。

B 板未来如果需要接受 C 板 Trigger，则增加一个独立输入模块；不要破坏现有 A → SPI → B 的鼠标透传链路。

开发顺序：

```text
1. C 板 Camera 示例正常出图
2. 验证 OV2640
3. RGB565 低分辨率采集
4. 固定 ROI
5. 单颜色阈值
6. LED/GPIO 本地验证
7. C → B GPIO Trigger
8. 再考虑 UART 协议
9. 最后与 A/B passthrough 整合
```

## 13.9 与 51 / Arduino 的学习关系

当前设备分工：

```text
51 MCU:
寄存器 / GPIO / 定时器 / 中断 / UART 基础

Arduino UNO 兼容板:
传感器和外设快速验证

ESP32-S3 A/B:
USB Host / USB HID Device / SPI / 双板透传

ESP32-S3-CAM + OV2640:
摄像头 / framebuffer / RGB565 / HSV / 嵌入式视觉
```

后续也可以把 C 板识别结果通过 UART 发给 51，让 51 控制 LED、蜂鸣器或数码管，作为跨 MCU 通信实验。

## 13.10 后续延迟实验

未来可利用现有示波器比较：

```text
PC 软件视觉
vs
S3-CAM + OV2640 外置视觉
vs
人工按键
```

重点记录：

- 平均触发延迟
- 最小/最大延迟
- P95
- 抖动
- 摄像头帧率和曝光对延迟的影响

此实验以自制测试画面/单机实验环境进行。

## 13.11 当前状态

```text
方案：已记录
S3-CAM：暂未购买
OV2640：暂未购买
C 板固件：未开始
A/B 透传：继续按第 12 节推进
```

当前优先级仍然是先把现有双 ESP32-S3 passthrough 和 G502 HID 数据测量做稳定，再开始第三块视觉板。
