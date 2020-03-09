#!/usr/bin/env bash
systemctl stop goodnews
systemctl disable goodnews
touch /etc/systemd/system/goodnews.service
cp /home/ubuntu/GoodNews/services/goodnews.service /etc/systemd/system/goodnews.service
systemctl start goodnews
systemctl enable goodnews
