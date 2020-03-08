#!/usr/bin/env bash
systemctl stop language_processing
systemctl disable language_processing
touch /etc/systemd/system/language_processing.service
cp /home/ubuntu/GoodNews/language_processing/language_processing.service /etc/systemd/system/language_processing.service
systemctl start language_processing
systemctl enable language_processing
