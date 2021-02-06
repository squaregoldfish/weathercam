#!/bin/sh
# /etc/init.d/cam_control.sh
### BEGIN INIT INFO
# Provides:          cam_control.sh
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: cam_control control
# Description:       Controls the camera pi control Server
### END INIT INFO
f_message(){
        echo "[+] $1"
}

# Carry out specific functions when asked to by the system
case "$1" in
        start)
                f_message "Starting cam_control"
                pid=`ps -eaf | grep cam_control.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                  f_message "cam_control already running"
                else
                  cd /root/weathercam/cam_control
                  pipenv run python cam_control.py &
                  sleep 20
                  f_message "cam_control started"
                fi
                ;;
        stop)
                f_message "Stopping cam_control"
                pid=`ps -eaf | grep cam_control.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                  kill -15 $pid
                  sleep 2
                  f_message "cam_control stopped"
                fi
                ;;
        restart)
                f_message "Restarting cam_control"
                pid=`ps -eaf | grep cam_control.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                  kill -15 $pid
                  sleep 2
                fi
                cd /root/weathercam/cam_pi
                pipenv run python cam_control.py &
                sleep 20
                f_message "Restarted cam_control"
                ;;
        status)
                pid=`ps -eaf | grep cam_control.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                        f_message "cam_control is running with pid ${pid}"
                else
                        f_message "Could not find cam_control running"
                fi
                ;;
        *)
                f_message "Usage: $0 {start|stop|status|restart}"
                exit 1
                ;;
esac
exit 0
