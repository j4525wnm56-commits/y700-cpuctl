#!/system/bin/sh
# 独立启动守护进程。
# 与 web_spawn.sh 同理: 函数体内的 & 会让 mksh 把调用上下文 fork 成子 shell,
# 放到独立脚本里执行可以避免调用方被复制。
# 用 nohup: 既脱离父 shell 的挂断信号, 又不会像 setsid 那样留下 wait 的父进程。
SELF=/data/adb/modules/y700_cpuctl/bin/cpuctl

nohup sh "$SELF" __watch >/dev/null 2>&1 &
