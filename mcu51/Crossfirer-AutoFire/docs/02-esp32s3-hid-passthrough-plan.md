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
