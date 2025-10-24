#!/bin/bash

SESSION="omnibase"
tmux new-session -d -s $SESSION

# Pane 0: left top
tmux send-keys -t $SESSION:0 "ros2 run serial_comm serial_communication" C-m

# Split vertically 5 times for left column (total 6 panes: 0–5)
for i in {1..5}; do
    tmux split-window -v -t $SESSION
    tmux select-layout tiled
done

# Assign commands to left column
tmux send-keys -t $SESSION:0 "stp && ros2 run serial_comm serial_communication" C-m
tmux send-keys -t $SESSION:1 "stp && ros2 run rqt_reconfigure rqt_reconfigure" C-m
tmux send-keys -t $SESSION:2 "stp && ros2 topic echo /stm32/omegas" C-m
tmux send-keys -t $SESSION:3 "stp && ros2 topic echo /stm32/errors" C-m
tmux send-keys -t $SESSION:4 "stp && ros2 topic echo /stm32/ctrl_u" C-m
tmux send-keys -t $SESSION:5 "stp && ros2 topic echo /stm32/encoders" C-m

# Now split right column from top left (pane 0 → horizontally)
tmux select-pane -t $SESSION:0
tmux split-window -h -t $SESSION

# Right top becomes pane 6
tmux send-keys -t $SESSION:6 "ros2 topic echo /stm32/timing" C-m

# Split it vertically to get pane 7
tmux split-window -v -t $SESSION:6
tmux send-keys -t $SESSION:7 "ros2 topic echo /stm32/pwm" C-m

# Balance layout and attach
tmux select-layout tiled
tmux attach -t $SESSION
