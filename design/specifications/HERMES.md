# Hermes Specification

## Purpose

Hermes is Argus's communication engine.

Its purpose is to connect Argus with people, applications, services, and external systems by managing all inbound and outbound communication.

Hermes translates requests into a format the system can understand and delivers responses back to their destination. It does not make decisions or store knowledge.

## Responsibilities

- Receive user requests
- Deliver responses
- Manage conversations
- Interface with external APIs
- Handle notifications
- Normalize incoming data
- Format outgoing data
- Manage communication channels

## Inputs

- User messages
- API requests
- System events
- Notifications
- External webhooks
- Commands from Cortex

## Outputs

- Responses to users
- API calls
- Notifications
- Messages to other systems
- Structured requests for Cortex

## Public Interfaces

- Send Message
- Receive Message
- Call API
- Receive Webhook
- Notify
- Broadcast Event

## Internal Components

- Conversation Manager
- API Gateway
- Message Router
- Notification Manager
- Channel Adapters
- Format Translator

## Data Ownership

Hermes owns:

- Active conversations
- Message history
- Communication sessions
- API request state
- Notification queue

## Dependencies

Required:

- Cortex
- Event Bus
- Logging
- Configuration

Optional:

- Third-party APIs
- Email providers
- Messaging platforms

## Failure Modes

- Failed API call
- Lost connection
- Invalid message format
- Authentication failure
- Notification failure

## Non-Goals

Hermes does not:

- Store long-term knowledge
- Make decisions
- Execute business workflows
- Manage persistent memory

## Future Enhancements

- Voice interaction
- Multi-language translation
- Streaming responses
- Real-time collaboration
- Multi-channel synchronization