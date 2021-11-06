#!/bin/sh
# /etc/init.d/cam_pi_screen.sh
### BEGIN INIT INFO
# Provides:          cam_pi_screen.sh
# Required-Start:    $network
# Required-Stop:     $network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: cam_pi_screen control
# Description:       Controls the camera pi status screen program
### END INIT INFO
f_message(){
        echo "[+] $1"
}

# Carry out specific functions when asked to by the system
case "$1" in
        start)
                f_message "Starting cam_pi_screen"
                pid=`ps -eaf | grep cam_pi_screen.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                  f_message "cam_pi_screen already running"
                else
                  cd /root/weathercam/cam_pi
                  pipenv run python cam_pi_screen.py &
                  sleep 10
                  f_message "cam_pi_screen started"
                fi
                ;;
        stop)
                f_message "Stopping cam_pi_screen"
                pid=`ps -eaf | grep cam_pi_screen.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                  kill -15 $pid
                  sleep 2
                  f_message "cam_pi_screen stopped"
                fi
                ;;
        restart)
                f_message "Restarting cam_pi_screen"
                pid=`ps -eaf | grep cam_pi_screen.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                  kill -15 $pid
                  sleep 2
                fi
                cd /root/weathercam/cam_pi
                pipenv run python cam_pi_screen.py &
                sleep 35
                f_message "Restarted cam_pi_screen"
                ;;
        status)
                pid=`ps -eaf | grep cam_pi_screen.py | grep -v "grep" | awk '{print $2}' | head -n 1`
                if [ -n "$pid" ];
                then
                        f_message "cam_pi_screen is running with pid ${pid}"
                else
                        f_message "Could not find cam_pi_screen running"
                fi
                ;;
        *)
                f_message "Usage: $0 {start|stop|status|restart}"
                exit 1
                ;;
esac
exit 0
