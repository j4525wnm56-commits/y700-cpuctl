#!/system/bin/sh
# y700_cpuctl WebUI CGI 接口
# 由 busybox httpd 以 root 身份调用, 仅监听 127.0.0.1
#
# 安全约束:
#   1. 所有入参必须通过白名单/纯数字校验, 任何参数都不拼进 shell 命令
#   2. 不调用 eval, 调外部脚本时参数已校验
#   3. 只读 sysfs 与 /data/adb/y700_cpuctl 下的状态文件

PATH=/system/bin:/system/xbin:/data/adb/magisk
export PATH

ST=/data/adb/y700_cpuctl
MOD=/data/adb/modules/y700_cpuctl
BIN="$MOD/bin/cpuctl"
CFG=/sys/devices/system/cpu/cpufreq

[ -d "$ST" ] || mkdir -p "$ST" 2>/dev/null

hdr() {
    printf 'Content-Type: application/json; charset=utf-8\r\n'
    printf 'Cache-Control: no-store, no-cache, must-revalidate\r\n'
    printf 'Pragma: no-cache\r\n'
    printf '\r\n'
}

fail() {
    hdr
    printf '{"ok":false,"error":"%s"}\n' "$1"
    exit 0
}

isdigit() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

get() { cat "$1" 2>/dev/null; }

# CPU 集群最高温度, 毫摄氏度; 取不到时返回 0
temp_mdeg() {
    local best=0 z ty v
    for z in /sys/class/thermal/thermal_zone*; do
        ty=$(get "$z/type")
        case "$ty" in
            cpu-*-usr|cpuss-*-usr)
                v=$(get "$z/temp")
                isdigit "$v" || continue
                [ "$v" -gt "$best" ] && best="$v"
                ;;
        esac
    done
    echo "$best"
}

emit_cluster() {
    local id="$1" p="$2" cpus="$3" label="$4" first="$5"
    local mn mx cur gov hmn hmx avail arr f
    [ -d "$p" ] || return 0
    mn=$(get "$p/scaling_min_freq"); isdigit "$mn" || mn=0
    mx=$(get "$p/scaling_max_freq"); isdigit "$mx" || mx=0
    cur=$(get "$p/scaling_cur_freq"); isdigit "$cur" || cur=0
    gov=$(get "$p/scaling_governor"); [ -z "$gov" ] && gov=unknown
    hmn=$(get "$p/cpuinfo_min_freq"); isdigit "$hmn" || hmn="$mn"
    hmx=$(get "$p/cpuinfo_max_freq"); isdigit "$hmx" || hmx="$mx"
    avail=$(get "$p/scaling_available_frequencies")
    arr=""
    for f in $avail; do
        isdigit "$f" && arr="$arr${arr:+,}$f"
    done
    [ "$first" = "1" ] || printf ','
    printf '{"id":"%s","cpus":"%s","label":"%s","min":%s,"max":%s,"cur":%s,"gov":"%s","hwMin":%s,"hwMax":%s,"avail":[%s]}' \
        "$id" "$cpus" "$label" "$mn" "$mx" "$cur" "$gov" "$hmn" "$hmx" "$arr"
}

emit_state() {
    local prof lim w wrun pid
    prof=$(get "$ST/profile"); [ -z "$prof" ] && prof=balanced
    lim=$(get "$ST/temp_limit"); isdigit "$lim" || lim=48000
    w=$(get "$ST/watch_enabled"); isdigit "$w" || w=0
    wrun=0
    pid=$(get "$ST/watch.pid")
    if [ "$w" = "1" ] && isdigit "$pid" && kill -0 "$pid" 2>/dev/null; then
        wrun=1
    fi
    hdr
    printf '{"ok":true,"profile":"%s","temp":%s,"tempLimit":%s,"watch":%s,"watchRunning":%s,"clusters":[' \
        "$prof" "$(temp_mdeg)" "$lim" "$w" "$wrun"
    emit_cluster p0 "$CFG/policy0" "0-3" "小核" 1
    emit_cluster p4 "$CFG/policy4" "4-6" "大核" 0
    emit_cluster p7 "$CFG/policy7" "7" "超大核" 0
    printf ']}\n'
}

# ---------- 解析查询串 ----------
action=""
p_profile=""
p_cluster=""
p_min=""
p_max=""
p_value=""

_ifs="$IFS"
IFS='&'
for kv in $QUERY_STRING; do
    k=${kv%%=*}
    v=${kv#*=}
    case "$k" in
        action)  action="$v" ;;
        profile) p_profile="$v" ;;
        cluster) p_cluster="$v" ;;
        min)     p_min="$v" ;;
        max)     p_max="$v" ;;
        value)   p_value="$v" ;;
    esac
done
IFS="$_ifs"

# ---------- 路由 ----------
case "$action" in
    state)
        emit_state
        ;;

    apply)
        case "$p_profile" in
            powersave|balanced|performance|game|max|stock) ;;
            *) fail "unknown profile" ;;
        esac
        sh "$BIN" apply "$p_profile" >/dev/null 2>&1
        emit_state
        ;;

    set)
        case "$p_cluster" in
            p0|p4|p7) ;;
            *) fail "bad cluster" ;;
        esac
        isdigit "$p_min" || fail "bad min"
        isdigit "$p_max" || fail "bad max"
        [ ${#p_min} -le 8 ] && [ ${#p_max} -le 8 ] || fail "freq too long"
        sh "$BIN" set "$p_cluster" "$p_min" "$p_max" >/dev/null 2>&1
        emit_state
        ;;

    watch)
        case "$p_value" in
            0) sh "$BIN" watch off >/dev/null 2>&1 ;;
            1) sh "$BIN" watch on  >/dev/null 2>&1 ;;
            *) fail "bad value" ;;
        esac
        emit_state
        ;;

    temp_limit)
        isdigit "$p_value" || fail "bad value"
        [ ${#p_value} -le 6 ] || fail "bad value"
        [ "$p_value" -ge 35000 ] && [ "$p_value" -le 65000 ] || fail "out of range"
        echo "$p_value" > "$ST/temp_limit"
        emit_state
        ;;

    gov)
        # 预留: 手动切换调速器
        case "$p_value" in
            schedutil|performance|powersave|ondemand|conservative|userspace) ;;
            *) fail "bad governor" ;;
        esac
        for pol in policy0 policy4 policy7; do
            [ -d "$CFG/$pol" ] && echo "$p_value" > "$CFG/$pol/scaling_governor" 2>/dev/null
        done
        emit_state
        ;;

    *)
        fail "unknown action"
        ;;
esac
