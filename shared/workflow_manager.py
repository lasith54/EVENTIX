import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class WorkflowStatus(str, Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    TIMEOUT = "timeout"

class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"

class WorkflowStep:
    def __init__(self, name: str, service: str, event_type: str, timeout: int = 30):
        self.name = name
        self.service = service
        self.event_type = event_type
        self.timeout = timeout
        self.status = WorkflowStepStatus.PENDING
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None

class Workflow:
    def __init__(self, workflow_id: str, workflow_type: str, initiator_service: str):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.initiator_service = initiator_service
        self.status = WorkflowStatus.INITIATED
        self.steps: List[WorkflowStep] = []
        self.context: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.timeout_task = None

    def add_step(self, step: WorkflowStep):
        self.steps.append(step)

    def get_step(self, step_name: str) -> Optional[WorkflowStep]:
        return next((step for step in self.steps if step.name == step_name), None)

    def all_steps_completed(self) -> bool:
        return all(step.status == WorkflowStepStatus.COMPLETED for step in self.steps)

    def has_failed_steps(self) -> bool:
        return any(step.status == WorkflowStepStatus.FAILED for step in self.steps)

class WorkflowManager:
    def __init__(self, service_name: str, event_publisher):
        self.service_name = service_name
        self.event_publisher = event_publisher
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_definitions: Dict[str, List[WorkflowStep]] = {}

    def register_workflow_definition(self, workflow_type: str, steps: List[WorkflowStep]):
        """Register a workflow definition with its steps"""
        self.workflow_definitions[workflow_type] = steps

    async def start_workflow(self, workflow_type: str, context: Dict[str, Any]) -> str:
        """Start a new workflow instance"""
        workflow_id = str(uuid.uuid4())
        
        if workflow_type not in self.workflow_definitions:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        workflow = Workflow(workflow_id, workflow_type, self.service_name)
        workflow.context = context

        # Add steps from definition
        for step_def in self.workflow_definitions[workflow_type]:
            step = WorkflowStep(
                step_def.name, 
                step_def.service, 
                step_def.event_type, 
                step_def.timeout
            )
            workflow.add_step(step)

        self.active_workflows[workflow_id] = workflow

        # Set workflow timeout
        workflow.timeout_task = asyncio.create_task(
            self._handle_workflow_timeout(workflow_id, 300)  # 5 minutes default
        )

        # Start the workflow
        await self._execute_workflow(workflow_id)
        
        logger.info(f"Started workflow {workflow_type} with ID {workflow_id}")
        return workflow_id

    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow steps"""
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.IN_PROGRESS

        # Publish workflow initiation events
        for step in workflow.steps:
            step.status = WorkflowStepStatus.PENDING
            step.started_at = datetime.utcnow()
            
            event_data = {
                "workflow_id": workflow_id,
                "workflow_type": workflow.workflow_type,
                "step_name": step.name,
                "context": workflow.context,
                "timeout": step.timeout
            }

            # Publish event to specific service
            await self._publish_workflow_event(
                step.service, step.event_type, event_data
            )

        logger.info(f"Executed workflow steps for {workflow_id}")

    async def handle_workflow_response(self, workflow_id: str, step_name: str, 
                                     success: bool, result: Any = None, error: str = None):
        """Handle response from workflow step"""
        if workflow_id not in self.active_workflows:
            logger.warning(f"Received response for unknown workflow: {workflow_id}")
            return

        workflow = self.active_workflows[workflow_id]
        step = workflow.get_step(step_name)
        
        if not step:
            logger.warning(f"Unknown step {step_name} in workflow {workflow_id}")
            return

        # Update step status
        step.completed_at = datetime.utcnow()
        step.result = result
        step.error = error
        step.status = WorkflowStepStatus.COMPLETED if success else WorkflowStepStatus.FAILED

        workflow.updated_at = datetime.utcnow()

        # Check workflow completion
        if workflow.has_failed_steps():
            await self._handle_workflow_failure(workflow_id)
        elif workflow.all_steps_completed():
            await self._handle_workflow_completion(workflow_id)

        logger.info(f"Updated step {step_name} in workflow {workflow_id}: {'success' if success else 'failed'}")

    async def _handle_workflow_completion(self, workflow_id: str):
        """Handle successful workflow completion"""
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.COMPLETED

        # Cancel timeout task
        if workflow.timeout_task:
            workflow.timeout_task.cancel()

        # Publish completion event
        await self._publish_workflow_event(
            "all", f"{workflow.workflow_type}.completed",
            {
                "workflow_id": workflow_id,
                "workflow_type": workflow.workflow_type,
                "context": workflow.context,
                "completed_at": datetime.utcnow().isoformat()
            }
        )

        # Clean up
        del self.active_workflows[workflow_id]
        logger.info(f"Workflow {workflow_id} completed successfully")

    async def _handle_workflow_failure(self, workflow_id: str):
        """Handle workflow failure and start compensation"""
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.COMPENSATING

        # Start compensation for completed steps
        completed_steps = [step for step in workflow.steps 
                          if step.status == WorkflowStepStatus.COMPLETED]

        for step in reversed(completed_steps):
            compensation_event = f"{step.event_type}.compensate"
            event_data = {
                "workflow_id": workflow_id,
                "step_name": step.name,
                "original_result": step.result,
                "context": workflow.context
            }

            await self._publish_workflow_event(
                step.service, compensation_event, event_data
            )

        logger.info(f"Started compensation for workflow {workflow_id}")

    async def _handle_workflow_timeout(self, workflow_id: str, timeout_seconds: int):
        """Handle workflow timeout"""
        await asyncio.sleep(timeout_seconds)
        
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow.status == WorkflowStatus.IN_PROGRESS:
                workflow.status = WorkflowStatus.TIMEOUT
                await self._handle_workflow_failure(workflow_id)
                logger.warning(f"Workflow {workflow_id} timed out")

    async def _publish_workflow_event(self, target_service: str, event_type: str, data: Dict[str, Any]):
        """Publish workflow event to specific service or all services"""
        if target_service == "user-service" or target_service == "all":
            await self.event_publisher.publish_user_event(event_type, data)
        if target_service == "event-service" or target_service == "all":
            await self.event_publisher.publish_event_event(event_type, data)
        if target_service == "booking-service" or target_service == "all":
            await self.event_publisher.publish_booking_event(event_type, data)
        if target_service == "payment-service" or target_service == "all":
            await self.event_publisher.publish_payment_event(event_type, data)