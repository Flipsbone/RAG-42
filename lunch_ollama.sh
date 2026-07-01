#!/bin/bash
export OLLAMA_MODELS=~/ollama_models
export OLLAMA_NUM_PARALLEL=$(cat /sys/devices/system/cpu/cpu*/topology/core_id | sort -u | wc -l)

ollama serve
