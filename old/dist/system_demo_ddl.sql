-- ============================================================
-- system_demo - DDL Script
-- Miroir du catalog system (tables MANAGED)
-- Usage : FinOps / Gouvernance / Compute / MLflow / Serving
-- ============================================================

CREATE CATALOG IF NOT EXISTS system_demo;

-- ============================================================
-- SCHEMA : access
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.access;

CREATE TABLE IF NOT EXISTS system_demo.access.assistant_events (
  account_id   STRING    COMMENT 'ID of the account.',
  workspace_id STRING    COMMENT 'ID of the workspace.',
  event_id     STRING    COMMENT 'A unique ID for this event.',
  event_time   TIMESTAMP COMMENT 'Time the event happened (UTC).',
  event_date   DATE      COMMENT 'Date the event happened.',
  user_agent   STRING    COMMENT 'Origination of request.',
  initiated_by STRING    COMMENT 'Email of the user initiating the request.'
) COMMENT 'Assistant events';

CREATE TABLE IF NOT EXISTS system_demo.access.audit (
  account_id        STRING              COMMENT 'The Databricks account identifier.',
  workspace_id      STRING              COMMENT 'The Databricks workspace identifier.',
  version           STRING              COMMENT 'Audit log schema version.',
  event_time        TIMESTAMP           COMMENT 'Timestamp of the event.',
  event_date        DATE                COMMENT 'Calendar date when the event occurred.',
  source_ip_address STRING              COMMENT 'IP address from which the request originated.',
  user_agent        STRING              COMMENT 'User agent string.',
  session_id        STRING              COMMENT 'Unique identifier for the session.',
  user_identity     STRING              COMMENT 'Identity of the person/service principal (serialized STRUCT).',
  service_name      STRING              COMMENT 'The Databricks service that generated the event.',
  action_name       STRING              COMMENT 'Name of the action performed.',
  request_id        STRING              COMMENT 'Unique identifier of the request.',
  request_params    MAP<STRING, STRING> COMMENT 'Map of request parameters.',
  response          STRING              COMMENT 'Response struct (serialized).',
  audit_level       STRING              COMMENT 'ACCOUNT_LEVEL or WORKSPACE_LEVEL.',
  event_id          STRING              COMMENT 'Unique identifier of the audit event.',
  identity_metadata STRING              COMMENT 'Identities from the audit event (serialized STRUCT).'
) COMMENT 'Audit log events';

CREATE TABLE IF NOT EXISTS system_demo.access.clean_room_events (
  account_id                         STRING    COMMENT 'The ID of the Databricks account.',
  metastore_id                       STRING    COMMENT 'The ID of the Unity Catalog metastore.',
  event_id                           STRING    COMMENT 'The ID of the clean room event.',
  clean_room_name                    STRING    COMMENT 'Name of the clean room.',
  central_clean_room_id              STRING    COMMENT 'The ID of central clean room.',
  initiator_global_metastore_id      STRING    COMMENT 'Global metastore ID of the initiating collaborator.',
  event_type                         STRING    COMMENT 'Type of the event.',
  clean_room_created_metadata        STRING    COMMENT 'Metadata for CLEAN_ROOM_CREATED (serialized STRUCT).',
  clean_room_deleted_metadata        STRING    COMMENT 'Metadata for CLEAN_ROOM_DELETED (serialized STRUCT).',
  run_notebook_started_metadata      STRING    COMMENT 'Metadata for RUN_NOTEBOOK_STARTED (serialized STRUCT).',
  run_notebook_completed_metadata    STRING    COMMENT 'Metadata for RUN_NOTEBOOK_COMPLETED (serialized STRUCT).',
  clean_room_assets_updated_metadata STRING    COMMENT 'Metadata for CLEAN_ROOM_ASSETS_UPDATED (serialized STRUCT).',
  event_time                         TIMESTAMP COMMENT 'Timestamp when the event took place.',
  output_schema_deleted_metadata     STRING    COMMENT 'Metadata for OUTPUT_SCHEMA_DELETED (serialized STRUCT).',
  initiator_collaborator_alias       STRING    COMMENT 'Alias of the collaborator who initiated the event.',
  asset_review_created_metadata      STRING    COMMENT 'Metadata for ASSET_REVIEW_CREATED (serialized STRUCT).'
) COMMENT 'Clean room events';

CREATE TABLE IF NOT EXISTS system_demo.access.column_lineage (
  account_id             STRING              COMMENT 'The id of the Databricks account.',
  metastore_id           STRING              COMMENT 'The id of the Unity Catalog metastore.',
  workspace_id           STRING              COMMENT 'The id of the workspace.',
  entity_type            STRING              COMMENT 'Type of entity the lineage was captured from.',
  entity_id              STRING              COMMENT 'ID of the entity.',
  entity_run_id          STRING              COMMENT 'ID of the unique run of the entity.',
  source_table_full_name STRING              COMMENT 'Three-level name of the source table.',
  source_table_catalog   STRING              COMMENT 'Catalog of the source table.',
  source_table_schema    STRING              COMMENT 'Schema of the source table.',
  source_table_name      STRING              COMMENT 'Name of the source table.',
  source_path            STRING              COMMENT 'Location of the source table.',
  source_type            STRING              COMMENT 'Type of the source (TABLE, PATH, VIEW, ...).',
  source_column_name     STRING              COMMENT 'Name of the source column.',
  target_table_full_name STRING              COMMENT 'Three-level name of the target table.',
  target_table_catalog   STRING              COMMENT 'Catalog of the target table.',
  target_table_schema    STRING              COMMENT 'Schema of the target table.',
  target_table_name      STRING              COMMENT 'Name of the target table.',
  target_path            STRING              COMMENT 'Location of the target table.',
  target_type            STRING              COMMENT 'Type of the target.',
  target_column_name     STRING              COMMENT 'Name of the target column.',
  created_by             STRING              COMMENT 'User who generated this lineage.',
  event_time             TIMESTAMP           COMMENT 'Timestamp when the lineage was generated.',
  event_date             DATE                COMMENT 'Date when the lineage was generated.',
  record_id              STRING              COMMENT 'Primary key of each row.',
  event_id               STRING              COMMENT 'Unique ID grouping rows from the same event.',
  statement_id           STRING              COMMENT 'Foreign key to query history.',
  entity_metadata        STRING              COMMENT 'Query context IDs (serialized STRUCT).',
  direct_access          BOOLEAN             COMMENT 'Whether the lineage is a direct access.'
) COMMENT 'Column-level lineage';

CREATE TABLE IF NOT EXISTS system_demo.access.outbound_network (
  account_id          STRING    COMMENT 'The ID of the Databricks account.',
  workspace_id        STRING    COMMENT 'The ID of the workspace.',
  destination_type    STRING    COMMENT 'Type of destination: DNS, IP, or STORAGE.',
  destination         STRING    COMMENT 'Details of the destination.',
  dns_event           STRING    COMMENT 'DNS destination details (serialized STRUCT).',
  storage_event       STRING    COMMENT 'Storage destination details (serialized STRUCT).',
  event_time          TIMESTAMP COMMENT 'Timestamp when the event took place.',
  access_type         STRING    COMMENT 'Type of access event.',
  event_id            STRING    COMMENT 'ID of the event.',
  network_source_type STRING    COMMENT 'Source type of the network event.'
) COMMENT 'Outbound network events';

CREATE TABLE IF NOT EXISTS system_demo.access.table_lineage (
  account_id             STRING              COMMENT 'The id of the Databricks account.',
  metastore_id           STRING              COMMENT 'The id of the Unity Catalog metastore.',
  workspace_id           STRING              COMMENT 'The id of the workspace.',
  entity_type            STRING              COMMENT 'Type of entity the lineage was captured from.',
  entity_id              STRING              COMMENT 'ID of the entity.',
  entity_run_id          STRING              COMMENT 'ID of the unique run of the entity.',
  source_table_full_name STRING              COMMENT 'Three-part name of the source table.',
  source_table_catalog   STRING              COMMENT 'Catalog of the source table.',
  source_table_schema    STRING              COMMENT 'Schema of the source table.',
  source_table_name      STRING              COMMENT 'Name of the source table.',
  source_path            STRING              COMMENT 'Location of the source table.',
  source_type            STRING              COMMENT 'Type of the source.',
  target_table_full_name STRING              COMMENT 'Three-part name of the target table.',
  target_table_catalog   STRING              COMMENT 'Catalog of the target table.',
  target_table_schema    STRING              COMMENT 'Schema of the target table.',
  target_table_name      STRING              COMMENT 'Name of the target table.',
  target_path            STRING              COMMENT 'Location of the target table.',
  target_type            STRING              COMMENT 'Type of the target.',
  created_by             STRING              COMMENT 'User who generated this lineage.',
  event_time             TIMESTAMP           COMMENT 'Timestamp when the lineage was generated.',
  event_date             DATE                COMMENT 'Date when the lineage was generated.',
  record_id              STRING              COMMENT 'Primary key of each row.',
  event_id               STRING              COMMENT 'Unique ID grouping rows from the same event.',
  statement_id           STRING              COMMENT 'Foreign key to query history.',
  entity_metadata        STRING              COMMENT 'Query context IDs (serialized STRUCT).',
  direct_access          BOOLEAN             COMMENT 'Whether the lineage is a direct access.'
) COMMENT 'Table-level lineage';

CREATE TABLE IF NOT EXISTS system_demo.access.workspaces_latest (
  account_id     STRING    COMMENT 'ID of the parent account.',
  workspace_id   STRING    COMMENT 'ID of the workspace.',
  workspace_name STRING    COMMENT 'Human-readable name of the workspace.',
  workspace_url  STRING    COMMENT 'URL of the workspace.',
  create_time    TIMESTAMP COMMENT 'Timestamp when the workspace was created.',
  status         STRING    COMMENT 'NOT_PROVISIONED | PROVISIONING | RUNNING | FAILED | BANNED.'
) COMMENT 'Latest workspace information';

-- ============================================================
-- SCHEMA : ai_gateway
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.ai_gateway;

CREATE TABLE IF NOT EXISTS system_demo.ai_gateway.usage (
  account_id            STRING              COMMENT 'The account id.',
  workspace_id          STRING              COMMENT 'The workspace id.',
  request_id            STRING              COMMENT 'API proxy generated request identifier.',
  schema_version        INT                 COMMENT 'Version of the event schema.',
  endpoint_id           STRING              COMMENT 'UUID of the AI Gateway entity.',
  endpoint_name         STRING              COMMENT 'Name of the top level AI Gateway entity.',
  endpoint_tags         MAP<STRING, STRING> COMMENT 'Static tags configured on the endpoint.',
  endpoint_metadata     STRING              COMMENT 'Endpoint level metadata (serialized STRUCT).',
  event_time            TIMESTAMP           COMMENT 'Timestamp at which request is received.',
  latency_ms            BIGINT              COMMENT 'Latency from request to response in ms.',
  time_to_first_byte_ms BIGINT              COMMENT 'Latency to first byte in ms.',
  destination_type      STRING              COMMENT 'The destination type.',
  destination_name      STRING              COMMENT 'Name of the destination object.',
  destination_id        STRING              COMMENT 'ID of the destination.',
  destination_model     STRING              COMMENT 'Foundation model name (e.g. gpt-4o, llama-3).',
  requester             STRING              COMMENT 'User or service principal name.',
  requester_type        STRING              COMMENT 'Type of the requester.',
  ip_address            STRING              COMMENT 'IP address of the client.',
  url                   STRING              COMMENT 'Request URL received by AI Gateway.',
  user_agent            STRING              COMMENT 'User agent of the client.',
  api_type              STRING              COMMENT 'API type of the request.',
  request_tags          MAP<STRING, STRING> COMMENT 'Tags provided in the request body.',
  input_tokens          BIGINT              COMMENT 'Total count of input tokens.',
  output_tokens         BIGINT              COMMENT 'Total count of output tokens.',
  total_tokens          BIGINT              COMMENT 'Sum of input and output tokens.',
  token_details         STRING              COMMENT 'Detailed token breakdown (serialized STRUCT).',
  response_content_type STRING              COMMENT 'Content-Type of the response.',
  status_code           INT                 COMMENT 'Final HTTP status code.',
  routing_information   STRING              COMMENT 'Detailed routing information (serialized STRUCT).',
  invocation_id         STRING              COMMENT 'Unique identifier for each inference call.',
  invocation_metadata   STRING              COMMENT 'System-generated metadata (serialized STRUCT).',
  service_type          STRING              COMMENT 'MODEL_SERVICE, MCP_SERVICE, or MODEL_PROVIDER_SERVICE.',
  service_id            STRING              COMMENT 'ID of the service.',
  service_name          STRING              COMMENT 'UC fully-qualified name of the service.',
  service_tags          MAP<STRING, STRING> COMMENT 'Tags set for the service.',
  mcp_metadata          STRING              COMMENT 'MCP service specific metadata (serialized STRUCT).'
) COMMENT 'AI Gateway usage events';

-- ============================================================
-- SCHEMA : billing
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.billing;

CREATE TABLE IF NOT EXISTS system_demo.billing.list_prices (
  account_id       STRING    COMMENT 'ID of the account.',
  price_start_time TIMESTAMP COMMENT 'Time this price became effective (UTC).',
  price_end_time   TIMESTAMP COMMENT 'Time this price stopped being effective (UTC).',
  sku_name         STRING    COMMENT 'Name of the SKU.',
  cloud            STRING    COMMENT 'Cloud provider: AWS, AZURE, or GCP.',
  currency_code    STRING    COMMENT 'Currency this price is expressed in.',
  usage_unit       STRING    COMMENT 'Unit of measurement.',
  pricing          STRING    COMMENT 'Structured pricing info (serialized STRUCT).'
) COMMENT 'SKU list prices';

CREATE TABLE IF NOT EXISTS system_demo.billing.usage (
  account_id             STRING              COMMENT 'ID of the account.',
  workspace_id           STRING              COMMENT 'ID of the Workspace.',
  record_id              STRING              COMMENT 'Unique ID for this usage record.',
  sku_name               STRING              COMMENT 'Name of the SKU.',
  cloud                  STRING              COMMENT 'Cloud provider: AWS, AZURE, or GCP.',
  usage_start_time       TIMESTAMP           COMMENT 'Start time of this usage record (UTC).',
  usage_end_time         TIMESTAMP           COMMENT 'End time of this usage record (UTC).',
  usage_date             DATE                COMMENT 'Date of the usage record.',
  custom_tags            MAP<STRING, STRING> COMMENT 'Tags applied to this usage.',
  usage_unit             STRING              COMMENT 'Unit this usage is measured in (e.g. DBUs).',
  usage_quantity         DECIMAL(38, 10)     COMMENT 'Number of units consumed.',
  usage_metadata         STRING              COMMENT 'Metadata about the usage (serialized STRUCT).',
  identity_metadata      STRING              COMMENT 'Metadata about identities (serialized STRUCT).',
  record_type            STRING              COMMENT 'ORIGINAL, retraction, or restatement.',
  ingestion_date         DATE                COMMENT 'Date the record was ingested.',
  billing_origin_product STRING              COMMENT 'Product that originated the usage.',
  product_features       STRING              COMMENT 'Details about product features (serialized STRUCT).',
  usage_type             STRING              COMMENT 'COMPUTE_TIME, STORAGE_SPACE, NETWORK_BYTES, API_CALLS, TOKEN, or GPU_TIME.'
) COMMENT 'Usage and billing records';

CREATE TABLE IF NOT EXISTS system_demo.billing.attributed_usage (
  account_id       STRING              COMMENT 'ID of the account.',
  workspace_id     STRING              COMMENT 'ID of the Workspace.',
  record_id        STRING              COMMENT 'Unique ID for this record.',
  sku_name         STRING              COMMENT 'Name of the SKU.',
  cloud            STRING              COMMENT 'Cloud provider: AWS, AZURE, or GCP.',
  usage_start_time TIMESTAMP           COMMENT 'Start time of the usage period.',
  usage_end_time   TIMESTAMP           COMMENT 'End time of the usage period.',
  usage_date       DATE                COMMENT 'Date of the usage record.',
  usage_unit       STRING              COMMENT 'Unit this usage is measured in.',
  usage_quantity   DECIMAL(38, 10)     COMMENT 'Number of units consumed.',
  usage_metadata   STRING              COMMENT 'Metadata about the usage (serialized STRUCT).',
  attribution      MAP<STRING, STRING> COMMENT 'Attribution map (cost center, team, project, etc.).'
) COMMENT 'Attributed usage records';

-- ============================================================
-- SCHEMA : compute
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.compute;

CREATE TABLE IF NOT EXISTS system_demo.compute.clusters (
  account_id               STRING              COMMENT 'ID of the account.',
  workspace_id             STRING              COMMENT 'ID of the workspace.',
  cluster_id               STRING              COMMENT 'ID of the cluster.',
  cluster_name             STRING              COMMENT 'User-defined name for the cluster.',
  owned_by                 STRING              COMMENT 'Username of the cluster owner.',
  create_time              TIMESTAMP           COMMENT 'Timestamp of the cluster definition change.',
  delete_time              TIMESTAMP           COMMENT 'Timestamp when the cluster was deleted.',
  driver_node_type         STRING              COMMENT 'Driver node type name.',
  worker_node_type         STRING              COMMENT 'Worker node type name.',
  worker_count             BIGINT              COMMENT 'Number of workers (fixed-size clusters).',
  min_autoscale_workers    BIGINT              COMMENT 'Minimum workers (autoscaling).',
  max_autoscale_workers    BIGINT              COMMENT 'Maximum workers (autoscaling).',
  auto_termination_minutes BIGINT              COMMENT 'Configured autotermination duration.',
  enable_elastic_disk      BOOLEAN             COMMENT 'Autoscaling disk enablement status.',
  tags                     MAP<STRING, STRING> COMMENT 'User-defined tags for the cluster.',
  cluster_source           STRING              COMMENT 'Where the cluster was created: UI, API, JOB, PIPELINE.',
  init_scripts             ARRAY<STRING>       COMMENT 'Paths for init scripts.',
  aws_attributes           STRING              COMMENT 'AWS specific settings (serialized STRUCT).',
  azure_attributes         STRING              COMMENT 'Azure specific settings (serialized STRUCT).',
  gcp_attributes           STRING              COMMENT 'GCP specific settings (serialized STRUCT).',
  driver_instance_pool_id  STRING              COMMENT 'Instance pool ID for the driver.',
  worker_instance_pool_id  STRING              COMMENT 'Instance pool ID for workers.',
  dbr_version              STRING              COMMENT 'The Databricks Runtime version.',
  change_time              TIMESTAMP           COMMENT 'Timestamp of change to the compute definition.',
  change_date              DATE                COMMENT 'Change date (for retention).',
  data_security_mode       STRING              COMMENT 'Data security mode.',
  policy_id                STRING              COMMENT 'ID of the cluster policy.'
) COMMENT 'Cluster definitions';

CREATE TABLE IF NOT EXISTS system_demo.compute.node_timeline (
  account_id                      STRING              COMMENT 'ID of the account.',
  workspace_id                    STRING              COMMENT 'ID of the workspace.',
  cluster_id                      STRING              COMMENT 'ID of the compute resource.',
  instance_id                     STRING              COMMENT 'ID of the specific instance.',
  start_time                      TIMESTAMP           COMMENT 'Start time for the record (UTC).',
  end_time                        TIMESTAMP           COMMENT 'End time for the record (UTC).',
  driver                          BOOLEAN             COMMENT 'TRUE if driver node, FALSE if worker.',
  cpu_user_percent                DOUBLE              COMMENT 'CPU time in userland (%).',
  cpu_system_percent              DOUBLE              COMMENT 'CPU time in kernel (%).',
  cpu_wait_percent                DOUBLE              COMMENT 'CPU time waiting for I/O (%).',
  mem_used_percent                DOUBLE              COMMENT 'Memory usage (%).',
  mem_swap_percent                DOUBLE              COMMENT 'Memory swap usage (%).',
  network_sent_bytes              BIGINT              COMMENT 'Bytes sent in network traffic.',
  network_received_bytes          BIGINT              COMMENT 'Bytes received from network traffic.',
  disk_free_bytes_per_mount_point MAP<STRING, BIGINT> COMMENT 'Disk utilization grouped by mount point.',
  node_type                       STRING              COMMENT 'Name of the node type.',
  private_ip                      STRING              COMMENT 'Private IP.'
) COMMENT 'Node-level timeline metrics';

CREATE TABLE IF NOT EXISTS system_demo.compute.node_types (
  account_id STRING COMMENT 'ID of the account.',
  node_type  STRING COMMENT 'Unique identifier for node type.',
  core_count DOUBLE COMMENT 'Number of vCPUs.',
  memory_mb  BIGINT COMMENT 'Total memory in MB.',
  gpu_count  BIGINT COMMENT 'Number of GPUs.'
) COMMENT 'Available node types';

CREATE TABLE IF NOT EXISTS system_demo.compute.instance_pools (
  account_id         STRING    COMMENT 'ID of the account.',
  workspace_id       STRING    COMMENT 'ID of the workspace.',
  instance_pool_id   STRING    COMMENT 'ID of the instance pool.',
  instance_pool_name STRING    COMMENT 'Name of the instance pool.',
  node_type_id       STRING    COMMENT 'Node type used by the pool.',
  min_idle_instances INT       COMMENT 'Minimum idle instances.',
  max_capacity       INT       COMMENT 'Maximum capacity of the pool.',
  create_time        TIMESTAMP COMMENT 'Timestamp when the pool was created.',
  delete_time        TIMESTAMP COMMENT 'Timestamp when the pool was deleted.',
  state              STRING    COMMENT 'State of the instance pool.'
) COMMENT 'Instance pool definitions';

CREATE TABLE IF NOT EXISTS system_demo.compute.instance_events (
  account_id   STRING    COMMENT 'ID of the account.',
  workspace_id STRING    COMMENT 'ID of the workspace.',
  cluster_id   STRING    COMMENT 'ID of the cluster.',
  instance_id  STRING    COMMENT 'ID of the instance.',
  event_type   STRING    COMMENT 'Type of instance event.',
  event_time   TIMESTAMP COMMENT 'Timestamp of the event.'
) COMMENT 'Instance lifecycle events';

CREATE TABLE IF NOT EXISTS system_demo.compute.warehouse_events (
  account_id    STRING    COMMENT 'The ID of the Databricks account.',
  workspace_id  STRING    COMMENT 'The ID of the workspace.',
  warehouse_id  STRING    COMMENT 'The ID of the SQL warehouse.',
  event_type    STRING    COMMENT 'SCALED_UP, SCALED_DOWN, STOPPING, RUNNING, STARTING, or STOPPED.',
  cluster_count INT       COMMENT 'Number of clusters actively running.',
  event_time    TIMESTAMP COMMENT 'Timestamp of the event (UTC).'
) COMMENT 'Warehouse scaling events';

CREATE TABLE IF NOT EXISTS system_demo.compute.warehouses (
  warehouse_id      STRING              COMMENT 'The ID of the SQL warehouse.',
  workspace_id      STRING              COMMENT 'The ID of the workspace.',
  account_id        STRING              COMMENT 'The ID of the Databricks account.',
  warehouse_name    STRING              COMMENT 'The name of the SQL warehouse.',
  warehouse_type    STRING              COMMENT 'CLASSIC, PRO, or SERVERLESS.',
  warehouse_channel STRING              COMMENT 'CURRENT or PREVIEW.',
  warehouse_size    STRING              COMMENT '2X_SMALL to 5X_LARGE.',
  min_clusters      INT                 COMMENT 'Minimum number of clusters.',
  max_clusters      INT                 COMMENT 'Maximum number of clusters.',
  auto_stop_minutes INT                 COMMENT 'Minutes before auto-stop due to inactivity.',
  tags              MAP<STRING, STRING> COMMENT 'Tags for the SQL warehouse.',
  change_time       TIMESTAMP           COMMENT 'Timestamp of change.',
  delete_time       TIMESTAMP           COMMENT 'Timestamp of deletion.',
  created_by        STRING              COMMENT 'Principal who created the warehouse.'
) COMMENT 'Warehouse definitions';

-- ============================================================
-- SCHEMA : lakeflow
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.lakeflow;

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.jobs (
  account_id        STRING              COMMENT 'The ID of the account.',
  workspace_id      STRING              COMMENT 'The ID of the workspace.',
  job_id            STRING              COMMENT 'The ID of the job.',
  name              STRING              COMMENT 'User-supplied name of the job.',
  creator_id        STRING              COMMENT 'ID of the principal who created the job.',
  tags              MAP<STRING, STRING> COMMENT 'Custom tags associated with this job.',
  run_as            STRING              COMMENT 'ID of the user/service principal for the job run.',
  change_time       TIMESTAMP           COMMENT 'Time when the job was last modified (UTC).',
  delete_time       TIMESTAMP           COMMENT 'Time when the job was deleted (UTC).',
  description       STRING              COMMENT 'User-supplied description of the job.',
  trigger           STRING              COMMENT 'Trigger configuration (serialized STRUCT).',
  trigger_type      STRING              COMMENT 'Type of trigger.',
  run_as_user_name  STRING              COMMENT 'Email/ID used for job run permissions.',
  creator_user_name STRING              COMMENT 'Email/ID of the job creator.',
  paused            BOOLEAN             COMMENT 'Whether the job is paused.',
  timeout_seconds   BIGINT              COMMENT 'Timeout duration in seconds.',
  health_rules      ARRAY<STRING>       COMMENT 'Health rules defined for this job.',
  deployment        STRING              COMMENT 'Deployment information (serialized STRUCT).',
  create_time       TIMESTAMP           COMMENT 'Time at which this job was created (UTC).'
) COMMENT 'Job definitions';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.job_tasks (
  account_id      STRING        COMMENT 'The ID of the account.',
  workspace_id    STRING        COMMENT 'The ID of the workspace.',
  job_id          STRING        COMMENT 'The ID of the job.',
  task_key        STRING        COMMENT 'Reference key for the task within the job.',
  depends_on_keys ARRAY<STRING> COMMENT 'Task keys of upstream dependencies.',
  change_time     TIMESTAMP     COMMENT 'Time when the task was last modified (UTC).',
  delete_time     TIMESTAMP     COMMENT 'Time when the task was deleted (UTC).',
  timeout_seconds BIGINT        COMMENT 'Timeout duration in seconds.',
  health_rules    ARRAY<STRING> COMMENT 'Health rules defined for this task.'
) COMMENT 'Job task definitions';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.job_run_timeline (
  account_id                 STRING              COMMENT 'The ID of the account.',
  workspace_id               STRING              COMMENT 'The ID of the workspace.',
  job_id                     STRING              COMMENT 'The ID of the job.',
  run_id                     STRING              COMMENT 'The ID of the job run.',
  period_start_time          TIMESTAMP           COMMENT 'Start time for the run (UTC).',
  period_end_time            TIMESTAMP           COMMENT 'End time for the run (UTC).',
  trigger_type               STRING              COMMENT 'Type of trigger that fired the run.',
  result_state               STRING              COMMENT 'Outcome of the job run.',
  run_type                   STRING              COMMENT 'Type of job run.',
  run_name                   STRING              COMMENT 'User-supplied run name.',
  compute_ids                ARRAY<STRING>       COMMENT 'Compute IDs for the parent job run.',
  termination_code           STRING              COMMENT 'Termination code of the job run.',
  job_parameters             MAP<STRING, STRING> COMMENT 'Job-level parameters used in the run.',
  source_task_run_id         STRING              COMMENT 'ID of the source task run.',
  root_task_run_id           STRING              COMMENT 'ID of the root task run.',
  compute                    STRING              COMMENT 'Compute resources details (serialized ARRAY).',
  termination_type           STRING              COMMENT 'Type of termination.',
  setup_duration_seconds     BIGINT              COMMENT 'Setup phase duration in seconds.',
  queue_duration_seconds     BIGINT              COMMENT 'Queue duration in seconds.',
  run_duration_seconds       BIGINT              COMMENT 'Total run duration in seconds.',
  cleanup_duration_seconds   BIGINT              COMMENT 'Cleanup phase duration in seconds.',
  execution_duration_seconds BIGINT              COMMENT 'Execution phase duration in seconds.'
) COMMENT 'Job run timeline';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.job_task_run_timeline (
  account_id                 STRING              COMMENT 'The ID of the account.',
  workspace_id               STRING              COMMENT 'The ID of the workspace.',
  job_id                     STRING              COMMENT 'The ID of the job.',
  run_id                     STRING              COMMENT 'The ID of the task run.',
  period_start_time          TIMESTAMP           COMMENT 'Start time for the task (UTC).',
  period_end_time            TIMESTAMP           COMMENT 'End time for the task (UTC).',
  task_key                   STRING              COMMENT 'Reference key for the task.',
  compute_ids                ARRAY<STRING>       COMMENT 'IDs of compute used by the task.',
  result_state               STRING              COMMENT 'Outcome of the task run.',
  job_run_id                 STRING              COMMENT 'ID of the job run.',
  parent_run_id              STRING              COMMENT 'ID of the parent run.',
  termination_code           STRING              COMMENT 'Termination code of the task run.',
  compute                    STRING              COMMENT 'Compute resources details (serialized ARRAY).',
  termination_type           STRING              COMMENT 'Type of termination.',
  task_parameters            MAP<STRING, STRING> COMMENT 'Task-level parameters.',
  setup_duration_seconds     BIGINT              COMMENT 'Setup phase duration in seconds.',
  cleanup_duration_seconds   BIGINT              COMMENT 'Cleanup phase duration in seconds.',
  execution_duration_seconds BIGINT              COMMENT 'Execution phase duration in seconds.'
) COMMENT 'Job task run timeline';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.pipelines (
  account_id   STRING    COMMENT 'ID of the account.',
  workspace_id STRING    COMMENT 'ID of the workspace.',
  pipeline_id  STRING    COMMENT 'ID of the pipeline.',
  name         STRING    COMMENT 'Name of the pipeline.',
  creator_id   STRING    COMMENT 'ID of the pipeline creator.',
  create_time  TIMESTAMP COMMENT 'Time the pipeline was created.',
  delete_time  TIMESTAMP COMMENT 'Time the pipeline was deleted.',
  change_time  TIMESTAMP COMMENT 'Time the pipeline was last modified.'
) COMMENT 'Pipeline definitions';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.pipeline_update_timeline (
  account_id   STRING    COMMENT 'ID of the account.',
  workspace_id STRING    COMMENT 'ID of the workspace.',
  pipeline_id  STRING    COMMENT 'ID of the pipeline.',
  update_id    STRING    COMMENT 'ID of the pipeline update.',
  state        STRING    COMMENT 'State of the pipeline update.',
  cause        STRING    COMMENT 'Cause of the update.',
  cluster_id   STRING    COMMENT 'ID of the cluster used.',
  start_time   TIMESTAMP COMMENT 'Start time of the update.',
  end_time     TIMESTAMP COMMENT 'End time of the update.',
  update_type  STRING    COMMENT 'Type of update: TRIGGERED, CONTINUOUS, FULL_REFRESH.'
) COMMENT 'Pipeline update timeline';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.zerobus_ingest (
  account_id   STRING    COMMENT 'ID of the account.',
  workspace_id STRING    COMMENT 'ID of the workspace.',
  pipeline_id  STRING    COMMENT 'ID of the pipeline.',
  event_time   TIMESTAMP COMMENT 'Timestamp of the event.',
  event_type   STRING    COMMENT 'Type of the event.',
  event_id     STRING    COMMENT 'ID of the event.'
) COMMENT 'Lakeflow ingest events';

CREATE TABLE IF NOT EXISTS system_demo.lakeflow.zerobus_stream (
  account_id   STRING    COMMENT 'ID of the account.',
  workspace_id STRING    COMMENT 'ID of the workspace.',
  pipeline_id  STRING    COMMENT 'ID of the pipeline.',
  event_time   TIMESTAMP COMMENT 'Timestamp of the event.',
  event_type   STRING    COMMENT 'Type of the event.',
  event_id     STRING    COMMENT 'ID of the event.'
) COMMENT 'Lakeflow stream events';

-- ============================================================
-- SCHEMA : mlflow
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.mlflow;

CREATE TABLE IF NOT EXISTS system_demo.mlflow.experiments_latest (
  account_id    STRING    COMMENT 'The ID of the account.',
  update_time   TIMESTAMP COMMENT 'Time when the experiment was last updated.',
  delete_time   TIMESTAMP COMMENT 'Time when the experiment was soft-deleted.',
  workspace_id  STRING    COMMENT 'The ID of the workspace.',
  experiment_id STRING    COMMENT 'The ID of the MLflow experiment.',
  name          STRING    COMMENT 'User-provided name of the experiment.',
  create_time   TIMESTAMP COMMENT 'Time when the experiment was created.'
) COMMENT 'Latest MLflow experiments';

CREATE TABLE IF NOT EXISTS system_demo.mlflow.run_metrics_history (
  account_id    STRING    COMMENT 'The ID of the account.',
  insert_time   TIMESTAMP COMMENT 'Time when the metric was inserted.',
  record_id     STRING    COMMENT 'Unique identifier of the metric.',
  workspace_id  STRING    COMMENT 'The ID of the workspace.',
  experiment_id STRING    COMMENT 'The ID of the MLflow experiment.',
  run_id        STRING    COMMENT 'The ID of the MLflow run.',
  metric_name   STRING    COMMENT 'The metric name.',
  metric_time   TIMESTAMP COMMENT 'User-specified time when the metric was computed.',
  metric_step   BIGINT    COMMENT 'Step (epoch) of model training.',
  metric_value  DOUBLE    COMMENT 'The metric value.'
) COMMENT 'MLflow run metrics history';

CREATE TABLE IF NOT EXISTS system_demo.mlflow.runs_latest (
  account_id         STRING              COMMENT 'The ID of the account.',
  update_time        TIMESTAMP           COMMENT 'Time when the run was last updated.',
  delete_time        TIMESTAMP           COMMENT 'Time when the run was soft-deleted.',
  workspace_id       STRING              COMMENT 'The ID of the workspace.',
  run_id             STRING              COMMENT 'The ID of the MLflow run.',
  experiment_id      STRING              COMMENT 'The ID of the MLflow experiment.',
  created_by         STRING              COMMENT 'Principal who created the run.',
  start_time         TIMESTAMP           COMMENT 'User-specified start time of the run.',
  end_time           TIMESTAMP           COMMENT 'User-specified end time of the run.',
  run_name           STRING              COMMENT 'Name of the MLflow run.',
  status             STRING              COMMENT 'RUNNING, FINISHED, FAILED, or KILLED.',
  params             MAP<STRING, STRING> COMMENT 'Key-value parameters of the run.',
  tags               MAP<STRING, STRING> COMMENT 'Key-value tags on the run.',
  aggregated_metrics STRING              COMMENT 'Aggregated metrics summary (serialized ARRAY).'
) COMMENT 'Latest MLflow runs';

-- ============================================================
-- SCHEMA : query
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.query;

CREATE TABLE IF NOT EXISTS system_demo.query.history (
  account_id                      STRING              COMMENT 'ID of the account.',
  workspace_id                    STRING              COMMENT 'The ID of the workspace.',
  statement_id                    STRING              COMMENT 'ID of the statement execution.',
  executed_by                     STRING              COMMENT 'Email/username of the user who ran the statement.',
  session_id                      STRING              COMMENT 'The Spark session ID.',
  execution_status                STRING              COMMENT 'FINISHED, FAILED, or CANCELED.',
  compute                         STRING              COMMENT 'Compute resource used (serialized STRUCT).',
  executed_by_user_id             STRING              COMMENT 'ID of the user who ran the statement.',
  statement_text                  STRING              COMMENT 'Text of the SQL statement.',
  statement_type                  STRING              COMMENT 'Statement type: ALTER, COPY, INSERT, SELECT, etc.',
  error_message                   STRING              COMMENT 'Error message if execution failed.',
  client_application              STRING              COMMENT 'Client application name.',
  client_driver                   STRING              COMMENT 'Connector used to connect.',
  total_duration_ms               BIGINT              COMMENT 'Total execution time in ms.',
  waiting_for_compute_duration_ms BIGINT              COMMENT 'Time waiting for compute resources in ms.',
  waiting_at_capacity_duration_ms BIGINT              COMMENT 'Time waiting in queue in ms.',
  execution_duration_ms           BIGINT              COMMENT 'Time executing the statement in ms.',
  compilation_duration_ms         BIGINT              COMMENT 'Time optimizing the statement in ms.',
  total_task_duration_ms          BIGINT              COMMENT 'Sum of all task durations in ms.',
  result_fetch_duration_ms        BIGINT              COMMENT 'Time fetching results in ms.',
  start_time                      TIMESTAMP           COMMENT 'Time Databricks received the request (UTC).',
  end_time                        TIMESTAMP           COMMENT 'Time the statement execution ended (UTC).',
  update_time                     TIMESTAMP           COMMENT 'Time of last progress update (UTC).',
  read_partitions                 BIGINT              COMMENT 'Number of table partitions read.',
  pruned_files                    BIGINT              COMMENT 'Number of pruned files.',
  read_files                      BIGINT              COMMENT 'Number of files read.',
  read_rows                       BIGINT              COMMENT 'Number of rows read.',
  produced_rows                   BIGINT              COMMENT 'Total rows returned.',
  read_bytes                      BIGINT              COMMENT 'Bytes of files read.',
  read_io_cache_percent           TINYINT             COMMENT 'Percentage of bytes read from IO cache.',
  from_result_cache               BOOLEAN             COMMENT 'TRUE if result was fetched from cache.',
  spilled_local_bytes             BIGINT              COMMENT 'Bytes written temporarily to disk.',
  written_bytes                   BIGINT              COMMENT 'Bytes of persistent data written.',
  shuffle_read_bytes              BIGINT              COMMENT 'Total bytes sent over the network.',
  query_source                    STRING              COMMENT 'Databricks entities involved (serialized STRUCT).',
  executed_as_user_id             STRING              COMMENT 'ID of the user whose privilege ran the statement.',
  executed_as                     STRING              COMMENT 'Name of the user whose privilege ran the statement.',
  written_rows                    BIGINT              COMMENT 'Rows of persistent data written.',
  written_files                   BIGINT              COMMENT 'Files of persistent data written.',
  cache_origin_statement_id       STRING              COMMENT 'Statement id of the cached result origin.',
  query_parameters                STRING              COMMENT 'Query parameter values (serialized STRUCT).',
  query_tags                      MAP<STRING, STRING> COMMENT 'Custom tags for this statement execution.',
  pruned_files_bytes              BIGINT              COMMENT 'Bytes of files pruned.',
  read_files_bytes                BIGINT              COMMENT 'Bytes of files read after pruning.'
) COMMENT 'Query execution history';

-- ============================================================
-- SCHEMA : serving
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.serving;

CREATE TABLE IF NOT EXISTS system_demo.serving.served_entities (
  served_entity_id        STRING    COMMENT 'Unique ID of the served entity.',
  account_id              STRING    COMMENT 'The Databricks account ID.',
  workspace_id            STRING    COMMENT 'The workspace ID.',
  created_by              STRING    COMMENT 'Name of the creator.',
  endpoint_name           STRING    COMMENT 'Name of the serving endpoint.',
  endpoint_id             STRING    COMMENT 'Unique ID of the serving endpoint.',
  served_entity_name      STRING    COMMENT 'Name of the served entity.',
  entity_type             STRING    COMMENT 'FEATURE_SPEC, EXTERNAL_MODEL, FOUNDATION_MODEL, or CUSTOM_MODEL.',
  entity_name             STRING    COMMENT 'Underlying name of the entity.',
  entity_version          STRING    COMMENT 'Version of the served entity.',
  endpoint_config_version INT       COMMENT 'Version of the endpoint configuration.',
  task                    STRING    COMMENT 'llm/v1/chat, llm/v1/completions, or llm/v1/embeddings.',
  external_model_config   STRING    COMMENT 'External model configurations (serialized STRUCT).',
  foundation_model_config STRING    COMMENT 'Foundation model configurations (serialized STRUCT).',
  custom_model_config     STRING    COMMENT 'Custom model configurations (serialized STRUCT).',
  feature_spec_config     STRING    COMMENT 'Feature specification configurations (serialized STRUCT).',
  change_time             TIMESTAMP COMMENT 'Timestamp of change.',
  endpoint_delete_time    TIMESTAMP COMMENT 'Timestamp of endpoint deletion.'
) COMMENT 'Serving endpoint entity definitions';

CREATE TABLE IF NOT EXISTS system_demo.serving.endpoint_usage (
  workspace_id            STRING              COMMENT 'The workspace ID.',
  account_id              STRING              COMMENT 'The Databricks account ID.',
  client_request_id       STRING              COMMENT 'User-provided request identifier.',
  databricks_request_id   STRING              COMMENT 'Databricks generated request identifier.',
  requester               STRING              COMMENT 'User or service principal name.',
  status_code             INT                 COMMENT 'HTTP status code returned from the model.',
  request_time            TIMESTAMP           COMMENT 'Timestamp at which the request was received.',
  input_token_count       BIGINT              COMMENT 'Token count of the input.',
  output_token_count      BIGINT              COMMENT 'Token count of the output.',
  input_character_count   BIGINT              COMMENT 'Character count of the input.',
  output_character_count  BIGINT              COMMENT 'Character count of the output.',
  usage_context           MAP<STRING, STRING> COMMENT 'User-provided map of usage context.',
  request_streaming       BOOLEAN             COMMENT 'Whether the request is in stream mode.',
  served_entity_id        STRING              COMMENT 'Unique ID to join with served_entities.'
) COMMENT 'Model serving endpoint usage';

-- ============================================================
-- SCHEMA : storage
-- ============================================================

CREATE SCHEMA IF NOT EXISTS system_demo.storage;

CREATE TABLE IF NOT EXISTS system_demo.storage.predictive_optimization_operations_history (
  account_id        STRING              COMMENT 'ID of the account.',
  workspace_id      STRING              COMMENT 'The ID of the workspace.',
  start_time        TIMESTAMP           COMMENT 'Time at which the operation started (UTC).',
  end_time          TIMESTAMP           COMMENT 'Time at which the operation ended (UTC).',
  metastore_name    STRING              COMMENT 'Name of the metastore.',
  metastore_id      STRING              COMMENT 'ID of the metastore.',
  catalog_name      STRING              COMMENT 'Name of the catalog.',
  schema_name       STRING              COMMENT 'Name of the schema.',
  table_name        STRING              COMMENT 'Name of the table.',
  table_id          STRING              COMMENT 'ID of the table.',
  operation_type    STRING              COMMENT 'Optimization operation performed.',
  operation_id      STRING              COMMENT 'ID for the optimization operation.',
  operation_status  STRING              COMMENT 'SUCCESSFUL or FAILED.',
  operation_metrics MAP<STRING, STRING> COMMENT 'Additional details about the optimization.',
  usage_unit        STRING              COMMENT 'Unit of usage.',
  usage_quantity    DECIMAL(38, 10)     COMMENT 'Amount of usage.'
) COMMENT 'Predictive optimization operations history';

CREATE TABLE IF NOT EXISTS system_demo.storage.table_metrics_history (
  account_id    STRING    COMMENT 'ID of the account.',
  workspace_id  STRING    COMMENT 'ID of the workspace.',
  metastore_id  STRING    COMMENT 'ID of the metastore.',
  catalog_name  STRING    COMMENT 'Name of the catalog.',
  schema_name   STRING    COMMENT 'Name of the schema.',
  table_name    STRING    COMMENT 'Name of the table.',
  table_id      STRING    COMMENT 'ID of the table.',
  snapshot_time TIMESTAMP COMMENT 'Time of the metrics snapshot.',
  num_files     BIGINT    COMMENT 'Number of files in the table.',
  size_bytes    BIGINT    COMMENT 'Total size of the table in bytes.'
) COMMENT 'Table metrics history';
