from trading_platform.infrastructure.audit.audit_log import AuditLog

def test_audit_log_appends_records():
    log = AuditLog()
    log.append("started", {"profile": "test"})
    records = log.records()
    assert len(records) == 1
    assert records[0].event == "started"
