#!/system/bin/sh
# Magisk 模块「操作」按钮: 启动 WebUI 并用浏览器打开
MODDIR=${0%/*}
sh "$MODDIR/bin/cpuctl" web open
