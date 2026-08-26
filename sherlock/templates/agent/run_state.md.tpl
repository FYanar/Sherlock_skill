# {{PROJECT_NAME}} — Run State Checkpoint

Schema-Version: 3.0
Updated-At: {{TIMESTAMP}}
Writer: AUTONOMOUS (Sherlock Inception Engine)

## lease

lease_id: null
owner: null
phase: INITIAL_INCEPTION_READY
heartbeat_at: null

## plan_binding

plan_id: PLAN-{{DATE_SLUG}}-INITIAL
plan_revision: 1.0
plan_state: READY_FOR_EXECUTION
wp_cursor: WP-01
active_scope: {{PROJECT_SCOPE}}
active_cases: []

## status

status: READY
reason: >
  Proje anayasası ve Agent hafıza altyapısı Sherlock tarafından başarıyla kuruldu.
  İlk iş paketleri için yürütme hazırdır.

## bootstrap_snapshot

code_md_sha256: null
test_suite_status: PENDING_INITIAL_RUN
total_scripts_count: 0
average_lines_per_module: 0
sherlock_verdict: INITIAL_SYSTEM_PROVISIONED

## next_action

Sistem tümüyle hatasız, modüler ve ilk iş paketini çalıştırmaya hazırdır.
