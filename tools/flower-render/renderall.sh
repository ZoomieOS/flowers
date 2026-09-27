#!/bin/bash
cd /home/claude/render
run(){ python3 flowers.py $1 $2 $3 out 96 $4 $5 > out/$1-$2.log 2>&1; echo "done $1-$2"; }
run anthurium 1 11 30 -6
run anthurium 2 12 38 8
run dahlia 1 21 38 -5
run dahlia 2 22 30 7
run dahlia 3 23 45 0
run eustoma 1 31 40 -8
run eustoma 2 32 32 10
run eustoma 3 33 48 0
run campanula 1 41 35 0
run campanula 2 42 35 0
run campanula 3 43 35 0
run campanula 4 44 35 0
run twine 1 51 0 0
run hydrangea 1 61 42 0
echo ALLDONE
