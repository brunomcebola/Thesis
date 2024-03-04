#!/bin/bash

tmux new-session -d -s argos_session 'echo y | /home/thales/Argos/Argos_venv/bin/python /home/thales/Argos/code/argos.py a r -y /home/thales/Argos/code/configs/acquire.yaml'
