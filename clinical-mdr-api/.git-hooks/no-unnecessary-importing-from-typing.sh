#!/usr/bin/env bash

RED=$'\e[0;31m'
NC=$'\e[0m'

grep -Prnzo "from typing import.*(\b(?:Optional|Union|List|Set|Dict|Tuple)\b|\([\s\S]*?\b(?:Optional|Union|List|Set|Dict|Tuple)\b[\s\S]*?\))" ./clinical_mdr_api
if [ $? -eq 0 ]; then
    printf "\n${RED}These files import Optional, Union, List, Set, Dict or Tuple.${NC}\n"
    exit 1
fi