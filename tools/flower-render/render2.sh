#!/bin/bash
cd /home/claude/render
run(){ python3 flowers.py $1 $2 $3 out 96 $4 $5 $6 > out/$1-$2.log 2>&1; echo "done $1-$2"; }
run dahlia 4 24 22 -38 1.12
run dahlia 5 25 55 30 0.92
run anthurium 3 15 24 -34 1.0
run eustoma 4 34 22 36 1.05
run eustoma 5 35 58 -20 0.95
run campanula 5 45 35 0 1.22
run campanula 6 46 35 0 1.15
echo ALLDONE
