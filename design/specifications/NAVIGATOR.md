# Navigator Specification

## Purpose

Navigator is Argus's execution engine.

Its purpose is to transform approved plans into completed work by coordinating tasks, invoking tools, monitoring execution, and reporting results.

Navigator does not make strategic decisions or own knowledge. It executes the plans produced by Cortex.

## Responsibilities

- Execute plans
- Manage task lifecycles
- Invoke tools and services
- Monitor task progress
- Handle retries and recovery
- Track execution status
- Report results
- Coordinate multi-step workflows

## Inputs

- Execution plans from Cortex
- User-approved actions
- Scheduled jobs
- System events
- Tool requests

## Outputs

- Completed tasks
- Execution results
- Status updates
- Errors
- Events
- Requests for additional reasoning

## Public Interfaces

- Execute Plan
- Execute Task
- Cancel Task
- Pause Task
- Resume Task
- Get Status

## Internal Components

- Task Manager
- Workflow Engine
- Tool Runner
- Queue Manager
- Retry Manager
- Progress Monitor

## Data Ownership

Navigator owns:

- Active tasks
- Execution state
- Workflow progress
- Job queues
- Execution history

## Dependencies

Required:

- Cortex
- Hermes
- Event Bus
- Scheduler
- Logging
- Configuration

## Failure Modes

- Task failure
- Tool unavailable
- Timeout
- Partial execution
- Retry exhausted
- Dependency unavailable

## Non-Goals

Navigator does not:

- Make strategic decisions
- Store long-term knowledge
- Communicate directly with users
- Analyze information

## Future Enhancements

- Parallel execution
- Distributed workers
- Resource optimization
- Dynamic workflow adaptation
- Autonomous recovery