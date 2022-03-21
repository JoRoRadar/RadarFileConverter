#!/bin/bash
# Convert all single quotes to double quotes

sed "s/'/\"\"/g" $1 > temp.csv
cp temp.csv $1
rm temp.csv