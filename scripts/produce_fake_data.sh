
# let's anchor things with a proper parent directory
export CLOCKWORK_ROOT=..
export slurm_state_ALLOCATIONS_RELATED_TO_MILA=${CLOCKWORK_ROOT}/slurm_state_test/fake_allocations_related_to_mila.json

for CLUSTER_NAME in beluga graham cedar mila
do
    # "node"  to  "node anonymized"
    python3 -m slurm_state.anonymize_scontrol_report \
        --keep 100 \
        --cluster_name ${CLUSTER_NAME} \
        --input_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_node \
        --output_file ${CLOCKWORK_ROOT}/tmp/slurm_report/${CLUSTER_NAME}/scontrol_show_node_anonymized
    # "job"  to  "job anonymized"
    python3 -m slurm_state.anonymize_scontrol_report \
        --keep 100 \
        --cluster_name ${CLUSTER_NAME} \
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
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_jobs_anonymized.json \
    --inputs \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/beluga/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/cedar/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/graham/job_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/mila/job_anonymized_dump_file.json

python3 concat_json_lists.py --keep 100 \
    --output ${CLOCKWORK_ROOT}/tmp/slurm_report/subset_100_nodes_anonymized.json \
    --inputs \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/beluga/node_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/cedar/node_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/graham/node_anonymized_dump_file.json \
    ${CLOCKWORK_ROOT}/tmp/slurm_report/mila/node_anonymized_dump_file.json
