#!/bin/bash
watcher_dir="/Users/00077990/yanda/pi24/watch_dir"
rclone_container_dir="/data"
sleep_timer=1

for file in file1 file2 file3 file4 file5; do
    echo $rclone_container_dir/$file
    docker exec -it dlm_rclone touch $rclone_container_dir/$file
    echo $watcher_dir/$file
    touch $watcher_dir/$file
    sleep $sleep_timer
done

for dir in dir1 dir2.ms; do
    echo $rclone_container_dir/$dir
    docker exec -it dlm_rclone mkdir $rclone_container_dir/$dir
    docker exec -it dlm_rclone mkdir $rclone_container_dir/$dir/test1
    echo $watcher_dir/$dir
    mkdir $watcher_dir/$dir
    touch $watcher_dir/$dir/test1
    sleep $sleep_timer
done

ls -al $watcher_dir
rm -rf $watcher_dir
mkdir $watcher_dir
ls -al $watcher_dir
docker exec -it dlm_rclone ls -alR $rclone_container_dir
docker exec -it dlm_rclone rm -rf $rclone_container_dir
docker exec -it dlm_rclone ls -alR $rclone_container_dir
