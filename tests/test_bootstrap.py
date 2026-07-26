"""Unit tests for argus.bootstrap.bootstrap."""

import unittest

from argus.application import Application
from argus.bootstrap import bootstrap
from argus.capability import ICapabilityRegistry, CapabilityRegistry
from argus.connectors import ConnectorManager, IConnectorManager
from argus.knowledge_graph import IKnowledgeGraph, KnowledgeGraph
from argus.memory_integration import IMemoryIntegration, MemoryIntegration
from argus.reasoning import IReasoningEngine, ReasoningEngine
from argus.events import IEventBus, InMemoryEventBus
from argus.conversation import IConversationManager, ConversationManager
from argus.dispatcher import IIntentDispatcher, IntentDispatcher
from argus.intent import IIntentRouter, IntentRouter
from argus.knowledge import IKnowledgeService, KnowledgeService
from argus.lifecycle import LifecycleManager, LifecycleState
from argus.memory import IMemoryService, MemoryService
from argus.planner import IPlanner, Planner, PlanStatus
from argus.plugins import IPluginManager, PluginManager
from argus.runtime import AgentRuntime, ExecutionStatus, IAgentRuntime
from argus.scheduler import IScheduler, Scheduler
from argus.workflow import IWorkflowEngine, WorkflowEngine
from argus.services import IServiceRegistry, InMemoryServiceRegistry

CORE_SERVICE_NAMES = (
    "configuration",
    "logger",
    "event_bus",
    "service_registry",
    "lifecycle_manager",
    "knowledge_service",
    "memory_service",
    "scheduler",
    "intent_router",
    "workflow_engine",
    "conversation_manager",
    "capability_registry",
    "intent_dispatcher",
    "plugin_manager",
    "planner",
    "knowledge_graph",
    "memory_integration",
    "reasoning_engine",
    "agent_runtime",
    "connector_manager",
)


class BootstrapTests(unittest.TestCase):
    def test_bootstrap_returns_running_application(self):
        application = bootstrap()

        try:
            self.assertIsInstance(application, Application)
            self.assertTrue(application.is_running)
            self.assertTrue(application.container.has("configuration"))
            self.assertTrue(application.container.has("logger"))
        finally:
            application.shutdown()

    def test_bootstrap_application_shuts_down_cleanly(self):
        application = bootstrap()

        application.shutdown()

        self.assertFalse(application.is_running)

    def test_bootstrap_registers_event_bus_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("event_bus"))
            event_bus = application.container.resolve("event_bus")
            self.assertIsInstance(event_bus, IEventBus)
            self.assertIsInstance(event_bus, InMemoryEventBus)
        finally:
            application.shutdown()

    def test_bootstrap_registers_service_registry_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("service_registry"))
            service_registry = application.container.resolve("service_registry")
            self.assertIsInstance(service_registry, IServiceRegistry)
            self.assertIsInstance(service_registry, InMemoryServiceRegistry)
        finally:
            application.shutdown()

    def test_bootstrap_registers_lifecycle_manager_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("lifecycle_manager"))
            lifecycle_manager = application.container.resolve("lifecycle_manager")
            self.assertIsInstance(lifecycle_manager, LifecycleManager)
        finally:
            application.shutdown()

    def test_bootstrap_registers_knowledge_service_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("knowledge_service"))
            knowledge_service = application.container.resolve("knowledge_service")
            self.assertIsInstance(knowledge_service, IKnowledgeService)
            self.assertIsInstance(knowledge_service, KnowledgeService)
        finally:
            application.shutdown()

    def test_bootstrap_registers_memory_service_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("memory_service"))
            memory_service = application.container.resolve("memory_service")
            self.assertIsInstance(memory_service, IMemoryService)
            self.assertIsInstance(memory_service, MemoryService)
        finally:
            application.shutdown()

    def test_bootstrap_registers_scheduler_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("scheduler"))
            scheduler = application.container.resolve("scheduler")
            self.assertIsInstance(scheduler, IScheduler)
            self.assertIsInstance(scheduler, Scheduler)
        finally:
            application.shutdown()

    def test_bootstrap_registers_intent_router_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("intent_router"))
            intent_router = application.container.resolve("intent_router")
            self.assertIsInstance(intent_router, IIntentRouter)
            self.assertIsInstance(intent_router, IntentRouter)
        finally:
            application.shutdown()

    def test_bootstrap_registers_workflow_engine_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("workflow_engine"))
            workflow_engine = application.container.resolve("workflow_engine")
            self.assertIsInstance(workflow_engine, IWorkflowEngine)
            self.assertIsInstance(workflow_engine, WorkflowEngine)
        finally:
            application.shutdown()

    def test_bootstrap_registers_conversation_manager_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("conversation_manager"))
            conversation_manager = application.container.resolve("conversation_manager")
            self.assertIsInstance(conversation_manager, IConversationManager)
            self.assertIsInstance(conversation_manager, ConversationManager)
        finally:
            application.shutdown()

    def test_bootstrap_registers_intent_dispatcher_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("intent_dispatcher"))
            intent_dispatcher = application.container.resolve("intent_dispatcher")
            self.assertIsInstance(intent_dispatcher, IIntentDispatcher)
            self.assertIsInstance(intent_dispatcher, IntentDispatcher)
        finally:
            application.shutdown()

    def test_bootstrap_registers_capability_registry_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("capability_registry"))
            capability_registry = application.container.resolve("capability_registry")
            self.assertIsInstance(capability_registry, ICapabilityRegistry)
            self.assertIsInstance(capability_registry, CapabilityRegistry)
        finally:
            application.shutdown()

    def test_bootstrap_capability_registry_has_initial_capabilities(self):
        from argus.intent import IntentType

        application = bootstrap()

        try:
            capability_registry = application.container.resolve("capability_registry")
            for intent_type in IntentType:
                matches = capability_registry.find_by_intent_type(intent_type)
                self.assertTrue(
                    any(capability.enabled for capability in matches),
                    msg=f"{intent_type.name} has no initial enabled capability registered",
                )
        finally:
            application.shutdown()

    def test_bootstrap_intent_dispatcher_resolves_every_intent_type(self):
        from argus.intent import Intent, IntentType

        application = bootstrap()

        try:
            intent_dispatcher = application.container.resolve("intent_dispatcher")
            for intent_type in IntentType:
                capability = intent_dispatcher.resolve(
                    Intent(name=intent_type, confidence=1.0)
                )
                self.assertTrue(capability.enabled)
                self.assertIn(intent_type, capability.intent_types)
        finally:
            application.shutdown()

    def test_bootstrap_registers_plugin_manager_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("plugin_manager"))
            plugin_manager = application.container.resolve("plugin_manager")
            self.assertIsInstance(plugin_manager, IPluginManager)
            self.assertIsInstance(plugin_manager, PluginManager)
        finally:
            application.shutdown()

    def test_bootstrap_plugin_manager_has_builtin_plugin(self):
        application = bootstrap()

        try:
            plugin_manager = application.container.resolve("plugin_manager")
            plugins = plugin_manager.list_plugins()
            self.assertEqual(len(plugins), 1)
            self.assertTrue(plugins[0].enabled)
            self.assertTrue(plugins[0].exported_capabilities)
        finally:
            application.shutdown()

    def test_bootstrap_plugin_manager_exports_same_capabilities_as_registry(self):
        application = bootstrap()

        try:
            capability_registry = application.container.resolve("capability_registry")
            plugin_manager = application.container.resolve("plugin_manager")
            registry_capabilities = capability_registry.list_capabilities()
            exported_capabilities = plugin_manager.list_exported_capabilities()
            self.assertEqual(set(c.id for c in registry_capabilities), set(c.id for c in exported_capabilities))
            for capability in exported_capabilities:
                self.assertIs(capability_registry.get(capability.id), capability)
        finally:
            application.shutdown()

    def test_bootstrap_registers_planner_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("planner"))
            planner = application.container.resolve("planner")
            self.assertIsInstance(planner, IPlanner)
            self.assertIsInstance(planner, Planner)
        finally:
            application.shutdown()

    def test_bootstrap_planner_has_no_plans_initially(self):
        application = bootstrap()

        try:
            planner = application.container.resolve("planner")
            self.assertEqual(planner.list_plans(), ())
        finally:
            application.shutdown()

    def test_bootstrap_planner_validates_plan_against_capability_registry(self):
        from argus.intent import Intent, IntentType

        application = bootstrap()

        try:
            planner = application.container.resolve("planner")
            capability_registry = application.container.resolve("capability_registry")
            existing_capability = capability_registry.list_capabilities()[0]

            plan = planner.create_plan(Intent(name=IntentType.QUESTION, confidence=1.0))
            plan = planner.add_step(
                plan.id,
                description="Use an existing capability",
                required_capability=existing_capability.id,
            )

            validated = planner.validate_plan(plan.id)

            self.assertEqual(validated.status, PlanStatus.VALIDATED)
        finally:
            application.shutdown()

    def test_bootstrap_registers_knowledge_graph_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("knowledge_graph"))
            knowledge_graph = application.container.resolve("knowledge_graph")
            self.assertIsInstance(knowledge_graph, IKnowledgeGraph)
            self.assertIsInstance(knowledge_graph, KnowledgeGraph)
        finally:
            application.shutdown()

    def test_bootstrap_knowledge_graph_is_not_started(self):
        application = bootstrap()

        try:
            knowledge_graph = application.container.resolve("knowledge_graph")
            self.assertEqual(knowledge_graph.status(), LifecycleState.CREATED)
            self.assertEqual(
                application.container.resolve("lifecycle_manager").status("knowledge_graph"),
                LifecycleState.REGISTERED,
            )
        finally:
            application.shutdown()

    def test_bootstrap_knowledge_graph_supports_entities_and_relationships(self):
        from argus.knowledge_graph import Entity, Relationship

        application = bootstrap()

        try:
            knowledge_graph = application.container.resolve("knowledge_graph")
            alice = Entity(entity_type="person", name="Alice")
            bob = Entity(entity_type="person", name="Bob")
            knowledge_graph.add_entity(alice)
            knowledge_graph.add_entity(bob)
            knowledge_graph.add_relationship(
                Relationship(source_entity_id=alice.id, target_entity_id=bob.id, relationship_type="knows")
            )

            self.assertEqual(knowledge_graph.neighbors(alice.id), (bob,))
        finally:
            application.shutdown()

    def test_bootstrap_registers_memory_integration_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("memory_integration"))
            memory_integration = application.container.resolve("memory_integration")
            self.assertIsInstance(memory_integration, IMemoryIntegration)
            self.assertIsInstance(memory_integration, MemoryIntegration)
        finally:
            application.shutdown()

    def test_bootstrap_memory_integration_is_not_started(self):
        application = bootstrap()

        try:
            memory_integration = application.container.resolve("memory_integration")
            self.assertEqual(memory_integration.status(), LifecycleState.CREATED)
            self.assertEqual(
                application.container.resolve("lifecycle_manager").status("memory_integration"),
                LifecycleState.REGISTERED,
            )
        finally:
            application.shutdown()

    def test_bootstrap_memory_integration_synchronizes_a_memory_record_end_to_end(self):
        # bootstrap() constructs a real, disk-backed JSONMemoryStorage
        # (per Package 007) - this test writes and then explicitly
        # removes its own memory record in a finally block, so it
        # leaves memory_store.json exactly as it found it regardless
        # of outcome, and is safe to re-run.
        from argus.memory import MemoryRecord

        test_key = "bootstrap-test-key"
        application = bootstrap()

        try:
            memory_service = application.container.resolve("memory_service")
            knowledge_graph = application.container.resolve("knowledge_graph")
            memory_integration = application.container.resolve("memory_integration")

            if memory_service.exists(test_key):
                memory_service.delete(test_key)
            memory_service.put(MemoryRecord(key=test_key, value={"hello": "world"}))

            try:
                memory_integration.initialize()
                memory_integration.start()
                try:
                    entity_id = memory_integration.synchronize_memory(test_key)
                finally:
                    memory_integration.stop()

                self.assertEqual(knowledge_graph.get_entity(entity_id).name, test_key)
            finally:
                memory_service.delete(test_key)
        finally:
            application.shutdown()

    def test_bootstrap_registers_reasoning_engine_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("reasoning_engine"))
            reasoning_engine = application.container.resolve("reasoning_engine")
            self.assertIsInstance(reasoning_engine, IReasoningEngine)
            self.assertIsInstance(reasoning_engine, ReasoningEngine)
        finally:
            application.shutdown()

    def test_bootstrap_reasoning_engine_is_not_started(self):
        application = bootstrap()

        try:
            reasoning_engine = application.container.resolve("reasoning_engine")
            self.assertEqual(reasoning_engine.status(), LifecycleState.CREATED)
            self.assertEqual(
                application.container.resolve("lifecycle_manager").status("reasoning_engine"),
                LifecycleState.REGISTERED,
            )
        finally:
            application.shutdown()

    def test_bootstrap_reasoning_engine_queries_knowledge_graph_end_to_end(self):
        # Unlike the Memory Integration end-to-end test above,
        # ReasoningEngine and KnowledgeGraph are both purely in-memory
        # (see Package 018's and this package's own Objective) - no
        # disk-backed resource is touched, so no cleanup is required.
        from argus.knowledge_graph import Entity, Relationship
        from argus.reasoning import ReasoningQuery

        application = bootstrap()

        try:
            knowledge_graph = application.container.resolve("knowledge_graph")
            reasoning_engine = application.container.resolve("reasoning_engine")

            alice = Entity(entity_type="person", name="Alice")
            bob = Entity(entity_type="person", name="Bob")
            knowledge_graph.add_entity(alice)
            knowledge_graph.add_entity(bob)
            knowledge_graph.add_relationship(
                Relationship(source_entity_id=alice.id, target_entity_id=bob.id, relationship_type="knows")
            )

            result = reasoning_engine.query(ReasoningQuery(entity_id=alice.id))
            self.assertEqual(result.matched_entities, (alice, bob))

            neighbors_result = reasoning_engine.neighbors(alice.id)
            self.assertEqual(neighbors_result.matched_entities, (bob,))
        finally:
            application.shutdown()

    def test_bootstrap_registers_agent_runtime_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("agent_runtime"))
            agent_runtime = application.container.resolve("agent_runtime")
            self.assertIsInstance(agent_runtime, IAgentRuntime)
            self.assertIsInstance(agent_runtime, AgentRuntime)
        finally:
            application.shutdown()

    def test_bootstrap_agent_runtime_is_not_started(self):
        application = bootstrap()

        try:
            agent_runtime = application.container.resolve("agent_runtime")
            self.assertEqual(agent_runtime.status(), LifecycleState.CREATED)
            self.assertEqual(application.container.resolve("lifecycle_manager").status("agent_runtime"), LifecycleState.REGISTERED)
        finally:
            application.shutdown()

    def test_bootstrap_agent_runtime_executes_validated_plan_end_to_end(self):
        from argus.intent import Intent, IntentType
        from argus.runtime import StepExecutionError

        application = bootstrap()

        try:
            planner = application.container.resolve("planner")
            agent_runtime = application.container.resolve("agent_runtime")
            capability_registry = application.container.resolve("capability_registry")
            existing_capability = capability_registry.list_capabilities()[0]

            plan = planner.create_plan(Intent(name=IntentType.QUESTION, confidence=1.0))
            plan = planner.add_step(
                plan.id,
                description="Use an existing capability",
                required_capability=existing_capability.id,
            )
            plan = planner.validate_plan(plan.id)

            agent_runtime.initialize()
            agent_runtime.start()
            try:
                # bootstrap.py registers every core service but starts
                # none of them except Application itself (per
                # ADR-0002's divergence-avoidance policy) - so the
                # underlying WorkflowEngine is never started, and
                # dispatch() fails with "WorkflowEngine is CREATED,
                # expected RUNNING", wrapped as ActionExecutionError
                # and then StepExecutionError. This test confirms the
                # full Planner -> AgentRuntime -> IntentDispatcher call
                # chain wires together correctly and fails for that
                # expected, already-documented Version 1 reason
                # (Packages 012-015's own Known Limitations), not a
                # wiring bug introduced by this package.
                with self.assertRaises(StepExecutionError):
                    agent_runtime.start_execution(plan)
            finally:
                agent_runtime.stop()

            executions = agent_runtime.list_executions()
            self.assertEqual(len(executions), 1)
            self.assertEqual(executions[0].status, ExecutionStatus.FAILED)
        finally:
            application.shutdown()

    def test_bootstrap_registers_connector_manager_in_container(self):
        application = bootstrap()

        try:
            self.assertTrue(application.container.has("connector_manager"))
            connector_manager = application.container.resolve("connector_manager")
            self.assertIsInstance(connector_manager, IConnectorManager)
            self.assertIsInstance(connector_manager, ConnectorManager)
        finally:
            application.shutdown()

    def test_bootstrap_connector_manager_is_not_started(self):
        application = bootstrap()

        try:
            connector_manager = application.container.resolve("connector_manager")
            self.assertEqual(connector_manager.status(), LifecycleState.CREATED)
            self.assertEqual(
                application.container.resolve("lifecycle_manager").status("connector_manager"),
                LifecycleState.REGISTERED,
            )
        finally:
            application.shutdown()

    def test_bootstrap_registers_one_built_in_mock_connector(self):
        application = bootstrap()

        try:
            connector_manager = application.container.resolve("connector_manager")
            connectors = connector_manager.list_connectors()
            self.assertEqual(len(connectors), 1)
            self.assertEqual(connectors[0].name, "Mock External System")
            self.assertTrue(connectors[0].enabled)

            connector_manager.initialize()
            connector_manager.start()
            try:
                result = connector_manager.invoke(
                    connectors[0].id, "mock_operation", payload={"k": "v"}
                )
                self.assertEqual(result["operation"], "mock_operation")
                self.assertEqual(result["payload"], {"k": "v"})
            finally:
                connector_manager.stop()
        finally:
            application.shutdown()

    def test_bootstrap_registers_core_services_in_service_registry(self):
        application = bootstrap()

        try:
            service_registry = application.container.resolve("service_registry")
            for name in CORE_SERVICE_NAMES:
                self.assertTrue(
                    service_registry.contains(name),
                    msg=f"{name!r} was not registered in the Service Registry",
                )
            self.assertEqual(len(service_registry.list_services()), len(CORE_SERVICE_NAMES))
        finally:
            application.shutdown()

    def test_core_services_report_registered_lifecycle_state(self):
        application = bootstrap()

        try:
            lifecycle_manager = application.container.resolve("lifecycle_manager")
            for name in CORE_SERVICE_NAMES:
                self.assertEqual(
                    lifecycle_manager.status(name),
                    LifecycleState.REGISTERED,
                    msg=f"{name!r} was not LifecycleState.REGISTERED",
                )
        finally:
            application.shutdown()


if __name__ == "__main__":
    unittest.main()
