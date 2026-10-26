#!/system/bin/sh
# 开机自启: 应用上次保存的档位并启动守护
MODDIR=${0%/*}
BIN="$MODDIR/bin/cpuctl"
chmod 755 "$BIN" 2>/dev/null

# 等待系统启动完成、perf HAL 初始化结束, 否则会被系统覆盖
for i in $(seq 1 60); do
    [ "$(getprop sys.boot_completed 2>/dev/null)" = "1" ] && break
    sleep 2
done

sh "$BIN" boot
