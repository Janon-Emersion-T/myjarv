---
title: RabbitMQ Messaging Notes
summary: Broker guidance for queued work, retries, and durable asynchronous task delivery.
tags: ["rabbitmq", "queue", "async", "retries"]
sources: ["internal"]
confidence: 0.8
verified: true
version: 1.0
last_reviewed: 2026-06-07
approval_status: approved
trusted: true
domain: backend
department: development
frameworks: ["rabbitmq"]
languages: ["amqp"]
---
# RabbitMQ Messaging Notes

- Use durable queues for work that must survive restarts and maintenance windows.
- Make consumers idempotent before enabling retries or dead-letter flows.
- Capture correlation ids on publish and consume so failures remain traceable.
- Separate latency-sensitive events from slow batch workflows with distinct queues.
