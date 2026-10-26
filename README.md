# y700-cpuctl

![license](https://img.shields.io/badge/license-MIT-blue.svg)
![platform](https://img.shields.io/badge/platform-Magisk%20%7C%20KernelSU%20%7C%20Kitsune-brightgreen)
![device](https://img.shields.io/badge/device-TB--9707F%20%2F%20sheng-orange)
![generation](https://img.shields.io/badge/generation-Y700%20Gen%201%20(2022)-red)

联想拯救者 **Y700 一代（2022 款）** 的 CPU 频率分档控制模块。

### 机型标识

| 项目 | 值 |
|---|---|
| **代数** | **Y700 一代**（2022 年 6 月上市，8.8 英寸 2.5K 120 Hz） |
| **机型代号** | **`TB-9707F`**（联想官方型号，包装与保修查询用的就是这个） |
| **设备代号** | **`sheng`**（`ro.product.device` / `ro.build.product`，本文所有 `case "$DEVICE"` 判断都用它） |
| SoC | 高通骁龙 870 / `kona`，kernel 4.19 |
| 出厂系统 | ZUI 13（Android 11） |

> 各代**不通用**（联想官方型号对照）：一代 `TB-9707F`（本文）、二代 `TB320FC`（2023，骁龙 8+ Gen 1）、三代 `TB321FU`、四代 `TB322FU`、五代 `TB323FU`。集群划分与频点都不同，刷错不损坏设备，但档位不会生效。
> 另外，装了 HyperOS 移植包后机内 `ro.product.model` 会显示 `24018RPACC`（移植包带过来的机型串），硬件型号仍以 `TB-9707F` 为准。

**自带本地网页界面**：手机浏览器打开 `http://127.0.0.1:8088/` 就能看三簇实时频率、切档位、改上下限。单文件 HTML，零外部依赖，不联网也能用，可以「添加到主屏幕」当 App 用。

---

## 特性

- **六个档位**：省电 / 均衡 / 性能 / 游戏 / 极速 / 出厂，一键切换，三簇独立设上下限
- **自动维持守护**：每 15 秒校正一次。系统 perf HAL 偷偷改回来会立刻拉回去，档位不会自己飘
- **温度保护**：CPU 温度达到上限（默认 48 °C）时主动让权给系统温控，不再强行拉频
- **网页界面**：三张集群卡、实时频率与区间条、自定义上下限、温度保护调节，2 秒刷新
- **开机自启**：`service.sh` 等 `boot_completed` 后自动恢复上次档位、守护与界面
- **纯 sysfs**：只读写 `/sys/devices/system/cpu/cpufreq/*`，不注入进程、不 hook 内核

---

## 环境

| 项目 | 版本 |
|---|---|
| 当前系统 | HyperOS 1.0.11.0 移植，Android 14 |
| Root | Magisk / KernelSU / Kitsune Mask（26.4 实测） |
| 集群 | `policy0` = cpu0–3，`policy4` = cpu4–6，`policy7` = cpu7 |

> 需要 busybox 提供 `httpd`，Magisk 自带 `/data/adb/magisk/busybox`，不用另装。

---

## 安装

**方式一：管理器刷入（推荐）**

下载 Release 里的 `y700-cpuctl-v1.2.zip`，在 Magisk / KernelSU 的「模块 → 从本地安装」中选它，重启。

**方式二：命令行**

```bash
adb push y700-cpuctl-v1.2.zip /data/local/tmp/
su -c 'magisk --install-module /data/local/tmp/y700-cpuctl-v1.2.zip'
# 重启生效
```

**方式三：不重启立即用（调试用）**

```bash
adb push y700-cpuctl-v1.2.zip /data/local/tmp/
su -c 'M=/data/adb/modules/y700_cpuctl; rm -rf $M; mkdir -p $M; \
       busybox unzip -o /data/local/tmp/y700-cpuctl-v1.2.zip -d $M >/dev/null; \
       chmod 755 $M/bin/* $M/system/bin/* $M/service.sh $M/action.sh $M/uninstall.sh \
                 $M/webroot/cgi-bin/api.cgi'
su -c '/data/adb/modules/y700_cpuctl/bin/cpuctl apply balanced'
su -c '/data/adb/modules/y700_cpuctl/bin/cpuctl watch on'
su -c '/data/adb/modules/y700_cpuctl/bin/cpuctl web on'
```

这样模块目录直接可见，管理器能识别，但 `/system/bin/cpuctl` 这个 PATH 副本要等重启才由 Magisk 挂载出来。

自己从源码打包：`./package.sh`，产物在 `dist/`。

---

## 使用

| 方式 | 操作 |
|---|---|
| 模块按钮 | 管理器里点本模块的「操作」按钮，自动起服务并拉起浏览器 |
| 终端 | `su -c cpuctl web open` |
| 手动 | 浏览器打开 `http://127.0.0.1:8088/` |

> 服务只监听 `127.0.0.1`，局域网内其他设备访问不到。要在电脑上调，用 `adb forward tcp:18088 tcp:8088`。

### 档位

| 键 | 名称 | 小核 0-3 | 大核 4-6 | 超大核 7 | 调速器 |
|---|---|---|---|---|---|
| `powersave` | 省电 | 0.30–1.08 GHz | 0.71–1.57 GHz | 0.84–1.86 GHz | schedutil |
| `balanced` | 均衡（默认） | 0.30–1.52 GHz | 0.71–2.05 GHz | 0.84–2.55 GHz | schedutil |
| `performance` | 性能 | 0.30–1.80 GHz | 0.71–2.42 GHz | 0.84–2.84 GHz | schedutil |
| `game` | 游戏 | 0.98–1.80 GHz | 1.29–2.42 GHz | 1.63–3.19 GHz | schedutil |
| `max` | 极速（测速） | 锁 1.80 GHz | 锁 2.42 GHz | 锁 3.19 GHz | performance |
| `stock` | 出厂默认 | 0.30–1.80 GHz | 0.71–2.42 GHz | 0.84–3.19 GHz | schedutil |

`game` 的特点不是抬上限，而是**抬高下限**——避免重载时掉到低频造成卡顿，上限仍按 schedutil 自己跑。
`max` 用 `performance` 调速器锁死最高频，只适合跑分，持续用会明显发热。

### 界面

- **顶部**：当前档位、CPU 温度（<45 °C 青 / 45–52 °C 橙 / >52 °C 红）、守护是否在跑
- **三张集群卡**：实时频率、调速器、min–max 区间条与当前位置指针
- **档位区**：六键，当前档高亮；调过自定义频率后档位变「自定义」，六个按钮都不亮，此时「自定义频率」标题旁显示绿色 `生效中`，避免"到底哪个档在跑"的困惑
- **自定义频率**：每簇一对滑块，刻度严格对齐 `scaling_available_frequencies`，最低不会越过最高
- **高级**：自动维持开关、温度保护上限 38–60 °C

自定义滑块加了 `touch-action: pan-y`：手指上下滑页面不会误改频率，只有水平拖动才改。

### 命令

```bash
su -c cpuctl status                    # 文本状态（档位/守护/温度/三簇 min-max-cur）
su -c cpuctl list                      # 档位一览
su -c cpuctl apply game                # 切档
su -c cpuctl set p7 1632000 3187200    # 自定义单簇（kHz），档位转为 custom
su -c cpuctl watch on|off|status       # 自动维持守护
su -c cpuctl temp                      # 温度
su -c cpuctl web on|off|restart|status|open
su -c cpuctl boot                      # 手动跑一次开机流程
```

不重启时 `cpuctl` 还不在 PATH 里，用完整路径 `/data/adb/modules/y700_cpuctl/bin/cpuctl`。

---

## 架构

```
浏览器 ──HTTP──> busybox httpd (127.0.0.1:8088)
                    └─ CGI ──> api.cgi ──> bin/cpuctl ──> /sys/.../cpufreq/*
```

```
/
├── module.prop              模块元数据
├── customize.sh             刷入时：机型提示 + 权限修正
├── service.sh               开机自启（late_start service）
├── action.sh                管理器「操作」按钮入口
├── uninstall.sh             卸载：停服务 + 还原出厂频率
├── httpd.conf               busybox httpd 路由
├── bin/
│   ├── cpuctl               命令行 + 服务生命周期管理
│   ├── watch_spawn.sh       独立拉起守护（避免调用方被 mksh 复制）
│   └── web_spawn.sh         独立拉起 httpd（同上）
├── system/bin/cpuctl        PATH 里的短命令（单行 wrapper）
└── webroot/
    ├── index.html           单文件前端（HTML+CSS+JS，无 CDN）
    └── cgi-bin/api.cgi      CGI 接口，由 httpd 以 root 执行
```

运行时状态都放在 `/data/adb/y700_cpuctl/`：`profile`、`watch_enabled`、`watch.lock.d/`、`web_port`、`temp_limit`。

---

## HTTP API

`GET /cgi-bin/api.cgi?action=...`

| action | 参数 | 说明 |
|---|---|---|
| `state` | — | 档位、温度、守护状态、三簇 min/max/cur/gov/avail |
| `apply` | `profile=powersave\|balanced\|performance\|game\|max\|stock` | 切档 |
| `set` | `cluster=p0\|p4\|p7`、`min`、`max` | 自定义单簇，自动转 `custom` |
| `watch` | `value=0\|1` | 开/关守护 |
| `temp_limit` | `value=38000..60000` | 温度保护上限（毫摄氏度） |
| `gov` | `value=schedutil\|performance\|...` | 切调速器 |

参数走白名单与纯数字校验，脚本里没有 `eval`，参数不拼进命令，非法输入一律返回 `{"ok":false}`。

---

## 开机自启

```
Magisk late_start service
  └─ service.sh       轮询 sys.boot_completed 直到 =1
       └─ cpuctl boot
            ├─ 清掉陈旧 watch.pid / web.pid / 锁目录
            ├─ sleep 25（等 perf HAL 初始化完，否则频率会被系统覆盖）
            ├─ 恢复上次保存的档位
            ├─ watch_enabled=1 则拉起守护
            └─ 无 web_disabled 标记则拉起 httpd
```

实测开机后约 30 秒面板就绪，不需要任何手动操作。没起来按顺序查：

```bash
su -c 'ls /data/adb/modules/y700_cpuctl/disable'       # 有 disable 说明模块被禁用
su -c 'cat /data/adb/y700_cpuctl/watch_enabled'         # 0 表示守护被关过, 不会自启
su -c 'ls /data/adb/y700_cpuctl/web_disabled'           # 存在表示界面被关过
su -c 'ps -A -o ARGS | grep -E "__watch|httpd"'         # 看进程在不在
su -c 'sh /data/adb/modules/y700_cpuctl/bin/cpuctl boot' # 手动跑一次
```

---

## 改代码前必读（都是踩过的坑）

1. **`httpd.conf` 必须用空格分隔**
   busybox 的格式是 `<URL前缀> <文件匹配> <解释器>`。写成 `...:...:...` 会被解析成「地址 用户名 密码」的 **认证规则**，表现是所有 CGI 返回 `401`。
   ```conf
   /cgi-bin *.cgi /system/bin/sh
   ```

2. **busybox httpd 不响应 SIGTERM**
   只 `kill` 会留空壳继续占端口，新实例绑定失败变僵尸。必须 `kill` 后 1 秒 `kill -9`；启动前也要扫残留。

3. **端口自动顺延**
   8088 依次试到 8092，占用就换下一个，端口记在 `web_port`。前端全用相对路径，换端口无感。

4. **CRLF 会打死 CGI**
   Windows 上编辑后必须转 LF，否则 shebang 变成 `#!/system/bin/sh\r`，直接 502 或空响应。本仓库用 `.gitattributes` 强制 LF。

5. **守护会自我复制（最坑的一个）**
   守护循环里调用「函数体内含 `&`」的函数时，`mksh` 会把整个调用上下文 fork 成子 shell；子 shell 继承了 `CPUCTL_WATCH_LOCKED=1`，于是跳过加锁直接跑循环 —— 每检查一次 WebUI 就多一个守护进程。
   修法：后台启动挪进 `bin/watch_spawn.sh`、`bin/web_spawn.sh`，让 `cpuctl` 的函数体内完全不出现 `&`；循环开头再校验锁的持有者是不是自己，作为兜底。

6. **pid 文件跨重启会骗人**
   `watch.pid` 存的是上次开机的 PID，新系统里这个号可能被别的进程占用，`kill -0` 一看就「守护还活着」，开机后守护根本不启动。
   改用 `mkdir` 原子锁目录 `watch.lock.d/`（存 PID）+ 校验 argv 真是 `__watch`，并在 `boot` 开头清掉陈旧 pid。

7. **toybox 的 `setsid` 没有 `-f`**
   不加 `-f` 会 fork 一个父进程一直 `wait`，每次重启 WebUI 就多一个同名壳进程。改用 `nohup`（直接 exec，不留父壳）。

8. **`busybox httpd -f` 自己会 fork 工作进程**
   处理请求时会 fork 同命令行的子进程，所以 `ps` 里两个同名 httpd 是正常的，不要当多实例清理——会打断正在处理的请求。判断是否真在服务看 `netstat -ltnp`。

9. **系统会偷偷改 min/max**
   HyperOS 的 perf HAL 会按场景 boost，界面显示的是 sysfs 实时值，可能和档位标称值不一致，属正常现象。

---

## 卸载

管理器里删除模块即可。`uninstall.sh` 会：杀 httpd 与守护 → 恢复出厂频率与 `schedutil` → 清理 `/data/adb/y700_cpuctl`。

注意它**会把状态目录一起删掉**，包括 `backup/`。`stock` 档是硬编码的出厂值，不读备份，所以随时能 `cpuctl apply stock` 还原。

---

## 适配其他机型

模块本身不含机型判断逻辑，移植需要改三处：

1. `bin/cpuctl` 顶部的 `P0` / `P4` / `P7` 三个 `policy*` 路径
2. `profile_apply()` 里各档位的频率值（对齐目标机的 `scaling_available_frequencies`）
3. `uninstall.sh` 里的出厂值

`cmd_status` / 网页界面 / CGI 都是从 sysfs 动态读的，一般不需求改。

---

## License

[MIT](LICENSE)
