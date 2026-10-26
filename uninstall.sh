#!/system/bin/sh
# 卸载时: 停守护 + 停 WebUI + 恢复出厂默认频率/调速器
STATE=/data/adb/y700_cpuctl

# 按命令行结构杀进程, 不按 pid 文件杀 —— 陈旧 pid 可能指向无关进程
for p in $(ps -A -o PID,ARGS 2>/dev/null | grep -F "bin/cpuctl __watch" | grep -v grep | awk '{print $1}'); do
    kill -9 "$p" 2>/dev/null
done
for p in $(ps -A -o PID,ARGS 2>/dev/null | grep -F "busybox httpd -f -p 127.0.0.1:" | grep -v grep | awk '{print $1}'); do
    kill -9 "$p" 2>/dev/null
done

# 先删状态目录(含锁目录), 避免残留锁让下次安装起不来
rm -rf "$STATE"

for p in /sys/devices/system/cpu/cpufreq/policy0 \
         /sys/devices/system/cpu/cpufreq/policy4 \
         /sys/devices/system/cpu/cpufreq/policy7; do
    [ -d "$p" ] || continue
    mx=$(cat "$p/cpuinfo_max_freq" 2>/dev/null)
    mn=$(cat "$p/cpuinfo_min_freq" 2>/dev/null)
    [ -n "$mx" ] && echo "$mx" > "$p/scaling_max_freq" 2>/dev/null
    [ -n "$mn" ] && echo "$mn" > "$p/scaling_min_freq" 2>/dev/null
    echo schedutil > "$p/scaling_governor" 2>/dev/null
done
