DB_PATH="/home/iwaya/LEFTE/lefte.db"

sqlite3 "$DB_PATH" "CREATE TABLE IF NOT EXISTS system_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_percent REAL,
    mem_percent REAL,
    cpu_temp REAL
);"

while true; do
    CPU_USAGE=$(awk '
        function get_cpu(  line, d, idle, total, i, n) {
            getline line < "/proc/stat"
            close("/proc/stat")
            
            # split()の戻り値（要素数）を n に格納する
            n = split(line, d)
            
            idle = d[5] + d[6]
            total = 0
            
            # NF の代わりに n を使う
            for (i=2; i<=n; i++) total += d[i]
            
            return (idle" "total)
        }
        BEGIN {
            split(get_cpu(), c1, " ")
            idle1 = c1[1]; total1 = c1[2]
            system("sleep 1")
            split(get_cpu(), c2, " ")
            idle2 = c2[1]; total2 = c2[2]
            
            diff_idle = idle2 - idle1
            diff_total = total2 - total1
            
            if (diff_total > 0)
                print (1.0 - diff_idle / diff_total) * 100
            else
                print 0.0
        }
    ')

    MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100}')

    if command -v vcgencmd &> /dev/null; then
        CPU_TEMP=$(vcgencmd measure_temp | egrep -o '[0-9.]+')
    elif [ -f /sys/class/thermal/thermal_zone0/temp ]; then
        CPU_TEMP=$(awk '{print $1 / 1000}' /sys/class/thermal/thermal_zone0/temp)
    else
        CPU_TEMP=0.0
    fi

    sqlite3 "$DB_PATH" "INSERT INTO system_stats (cpu_percent, mem_percent, cpu_temp) VALUES ($CPU_USAGE, $MEM_USAGE, $CPU_TEMP);"
    
    sleep 4
done