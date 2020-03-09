#!/usr/bin/env bash
systemctl stop language_processing
systemctl disable language_processing
touch /etc/systemd/system/language_processing.service
cp /home/ubuntu/GoodNews/services/language_processing.service /etc/systemd/system/language_processing.service
systemctl start language_processing
systemctl enable language_processing
