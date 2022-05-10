#!/bin/env bash
#
# This script ultimately produces the following three files,
# which can then be manually integrated to git or not.
#
# ${CLOCKWORK_ROOT}/tmp/slurm_report/fake_users.json
# ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json
# ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json

set -eu

# let's anchor things with a proper parent directory
export CLOCKWORK_ROOT=..
export slurm_state_ALLOCATIONS_RELATED_TO_MILA=${CLOCKWORK_ROOT}/slurm_state_test/fake_allocations_related_to_mila.json
export PYTHONPATH="..:${PYTHONPATH:-}"

export FAKE_USERS_FILE=${CLOCKWORK_ROOT}/tmp/slurm_report/fake_users.json

# Generate fake users and insert them in the database
python3 produce_fake_users.py --output_file=${FAKE_USERS_FILE}
python3 store_users_in_db.py --users_file=${FAKE_USERS_FILE}

# We iterate over the subfolders of the slurm_report folder, and use the data
# they contain if their names are related to known clusters

# These lists are destined to contain the generated temporary files
ANONYMIZED_JOBS_FILES=()
ANONYMIZED_NODES_FILES=()

# Iterate over the file of the slurm_report folder (the subfolders are the ones
# interesting us)
for SUBFOLDER in ${CLOCKWORK_ROOT}/tmp/slurm_report/*; do
  # If the file really is a subfolder
  if [ -d "$SUBFOLDER" ]; then
    CLUSTER_NAME="$(basename -- $SUBFOLDER)"
    # If its name is contained in the clusters list
    if [[ "$CLUSTER_NAME" =~ ^(beluga|graham|cedar|narval|mila)$ ]]; then
      # "node"  to  "node anonymized"
      python3 -m slurm_state.anonymize_scontrol_report \
          --keep 100 \
          --cluster_name ${CLUSTER_NAME} \
          --users_file ${FAKE_USERS_FILE} \
          --input_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_node \
          --output_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_node_anonymized
      # "job"  to  "job anonymized"
      python3 -m slurm_state.anonymize_scontrol_report \
          --keep 100 \
          --cluster_name ${CLUSTER_NAME} \
          --users_file ${FAKE_USERS_FILE} \
          --input_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_job \
          --output_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_job_anonymized

      # "job anonymized"  to  "jobs anonymized dump file"
      ANONYMIZED_JOBS_FILE=${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/job_anonymized_dump_file.json
      python3 -m slurm_state.read_report_commit_to_db \
          --cluster_name ${CLUSTER_NAME} \
          --jobs_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_job_anonymized \
          --dump_file $ANONYMIZED_JOBS_FILE
      ANONYMIZED_JOBS_FILES+=(${ANONYMIZED_JOBS_FILE})

      # "node anonymized"  to  "nodes anonymized dump file"
      ANONYMIZED_NODES_FILE=${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/node_anonymized_dump_file.json
      python3 -m slurm_state.read_report_commit_to_db \
          --cluster_name ${CLUSTER_NAME} \
          --nodes_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_node_anonymized \
          --dump_file $ANONYMIZED_NODES_FILE
      ANONYMIZED_NODES_FILES+=($ANONYMIZED_NODES_FILE)
    fi
  fi
done

python3 concat_json_lists.py --keep 100 \
    --inputs ${ANONYMIZED_JOBS_FILES[@]} \
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json

python3 concat_json_lists.py --keep 100 \
    --inputs ${ANONYMIZED_NODES_FILES[@]} \
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json

python3 stitch_json_lists_as_dict.py \
    ${CLOCKWORK_ROOT}/test_common/fake_data.json \
    users ${FAKE_USERS_FILE} \
    jobs ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json \
    nodes ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json

python3 insert_hardcoded_values.py \
    --input_file ${CLOCKWORK_ROOT}/test_common/fake_data.json \
    --output_file ${CLOCKWORK_ROOT}/test_common/fake_data.json

# cp ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json ${CLOCKWORK_ROOT}/test_common/fake_data_nodes.json
# cp ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json ${CLOCKWORK_ROOT}/test_common/fake_data_jobs.json
# cp ${FAKE_USERS_FILE} ${CLOCKWORK_ROOT}/test_common/fake_data_users.json
