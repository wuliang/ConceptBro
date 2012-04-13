#! /bin/sh
sleep 3
echo "111"
#ffmpeg -f x11grab -s 1024X768 -r 30 -i :0.0 -codec mpeg4 -sameq record2.mp4
ffmpeg -f x11grab -r 30 -s 1440x900 -i :0.0 -vcodec libx264 -preset ultrafast -crf 0 /tmp/output.mkv 
#-f null -y /dev/null