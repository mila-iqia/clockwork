#!/bin/env bash
#
# This script ultimately produces the following three files,
# which can then be manually integrated to git or not.
#
# ${CLOCKWORK_ROOT}/tmp/slurm_report/fake_users.json
# ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json
# ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json


# let's anchor things with a proper parent directory
export CLOCKWORK_ROOT=..
export slurm_state_ALLOCATIONS_RELATED_TO_MILA=${CLOCKWORK_ROOT}/slurm_state_test/fake_allocations_related_to_mila.json

export FAKE_USERS_FILE=${CLOCKWORK_ROOT}/tmp/slurm_report/fake_users.json
python3 produce_fake_users.py --output_file=${FAKE_USERS_FILE}

for CLUSTER_NAME in beluga graham cedar mila
do
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
    python3 -m slurm_state.read_report_commit_to_db \
        --cluster_desc ${CLOCKWORK_ROOT}/slurm_state/cluster_desc/${CLUSTER_NAME}.json \
        --jobs_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_job_anonymized \
        --dump_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/job_anonymized_dump_file.json

    # "node anonymized"  to  "nodes anonymized dump file"
    python3 -m slurm_state.read_report_commit_to_db \
        --cluster_desc ${CLOCKWORK_ROOT}/slurm_state/cluster_desc/${CLUSTER_NAME}.json \
        --nodes_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_node_anonymized \
        --dump_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/node_anonymized_dump_file.json
done

python3 concat_json_lists.py --keep 100 \
    --inputs \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/beluga/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/cedar/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/graham/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/mila/job_anonymized_dump_file.json \
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json

python3 concat_json_lists.py --keep 100 \
    --inputs \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/beluga/node_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/cedar/node_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/graham/node_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/mila/node_anonymized_dump_file.json \
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json

python3 stitch_json_lists_as_dict.py \
    ${CLOCKWORK_ROOT}/test_common/fake_data.json \
    users ${FAKE_USERS_FILE} \
    jobs ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json \
    nodes ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json

# cp ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json ${CLOCKWORK_ROOT}/test_common/fake_data_nodes.json
# cp ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json ${CLOCKWORK_ROOT}/test_common/fake_data_jobs.json
# cp ${FAKE_USERS_FILE} ${CLOCKWORK_ROOT}/test_common/fake_data_users.json
