#!/bin/bash

# Script from Compute Canada, given by Tyler Collins to Guillaume Alain.
# Tweaked some lines laters.

TARGET_DIR="${HOME}/slurm_report/mila"
SHOW_JOB_DEST="scontrol_show_job"
SHOW_NODE_DEST="scontrol_show_node"
SSHARE_DEST="sshare_plan"

scontrol show job  > "${TARGET_DIR}/${SHOW_JOB_DEST}.tmp" && \
  sync;sync && \
  mv "${TARGET_DIR}/${SHOW_JOB_DEST}.tmp" "${TARGET_DIR}/${SHOW_JOB_DEST}"
scontrol show node > "${TARGET_DIR}/${SHOW_NODE_DEST}.tmp" && \
  sync;sync && \
  mv "${TARGET_DIR}/${SHOW_NODE_DEST}.tmp" "${TARGET_DIR}/${SHOW_NODE_DEST}"
sshare -Plan       > "${TARGET_DIR}/${SSHARE_DEST}.tmp" && \
  sync;sync && \
  mv "${TARGET_DIR}/${SSHARE_DEST}.tmp" "${TARGET_DIR}/${SSHARE_DEST}"

