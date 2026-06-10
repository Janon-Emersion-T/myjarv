# Event Contracts

Every important event must use:

```json
{
  "id": "uuid",
  "type": "task.created",
  "source_module": "task_manager",
  "actor": "janon",
  "subject": "task_id",
  "risk_level": "low|medium|high|critical",
  "created_at": "ISO-8601",
  "correlation_id": "uuid",
  "metadata": {}
}