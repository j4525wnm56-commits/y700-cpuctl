#!/system/bin/sh
# 独立启动 httpd。
# 必须放在单独脚本里执行: 若在 cpuctl 的函数体内直接写后台启动,
# mksh 会把整个调用上下文 fork 成子 shell, 而子 shell 继承了
# CPUCTL_WATCH_LOCKED=1 会跳过互斥检查并继续跑守护循环,
# 结果就是每检查一次 WebUI 就多出一个守护进程(自我复制)。
#
# 用 nohup 而不是 setsid: toybox 的 setsid 不支持 -f, 不加 -f 它会 fork
# 一个父进程一直 wait 子进程, 每次重启 WebUI 就多堆一个同名壳进程。
MODDIR=/data/adb/modules/y700_cpuctl
STATE=/data/adb/y700_cpuctl
BUSYBOX=/data/adb/magisk/busybox
PORT="$1"

[ -n "$PORT" ] || exit 1

nohup "$BUSYBOX" httpd -f -p "127.0.0.1:$PORT" -h "$MODDIR/webroot" -c "$MODDIR/httpd.conf" >/dev/null 2>&1 &
echo $! > "$STATE/web.pid"
