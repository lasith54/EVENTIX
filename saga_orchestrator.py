from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import uuid
from kafka import KafkaProducer, KafkaConsumer

class SagaState(Enum):
    STARTED = "STARTED"
    USER_VALIDATED = "USER_VALIDATED"
    SEATS_RESERVED = "SEATS_RESERVED"
    BOOKING_CREATED = "BOOKING_CREATED"
    PAYMENT_PROCESSED = "PAYMENT_PROCESSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"

@dataclass
class SagaStep:
    step_id: str
    service: str
    command: str
    compensation_command: str
    status: str = "PENDING"
    retry_count: int = 0
    max_retries: int = 3

class BookingTicketSaga:
    def __init__(self, saga_id: str, user_id: str, event_id: str, 
                 seat_ids: List[str], payment_info: Dict):
        self.saga_id = saga_id
        self.user_id = user_id
        self.event_id = event_id
        self.seat_ids = seat_ids
        self.payment_info = payment_info
        self.state = SagaState.STARTED
        self.steps = self._initialize_steps()
        self.current_step = 0
        
    def _initialize_steps(self) -> List[SagaStep]:
        return [
            SagaStep("1", "user-service", "VALIDATE_USER", "NONE"),
            SagaStep("2", "event-service", "RESERVE_SEATS", "RELEASE_SEATS"),
            SagaStep("3", "booking-service", "CREATE_BOOKING", "CANCEL_BOOKING"),
            SagaStep("4", "payment-service", "PROCESS_PAYMENT", "REFUND_PAYMENT")
        ]

class SagaOrchestrator:
    def __init__(self, kafka_bootstrap_servers: str):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.consumer = KafkaConsumer(
            'saga-events',
            bootstrap_servers=kafka_bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        self.sagas: Dict[str, BookingTicketSaga] = {}
    
    def start_booking_saga(self, user_id: str, event_id: str, 
                          seat_ids: List[str], payment_info: Dict) -> str:
        saga_id = str(uuid.uuid4())
        saga = BookingTicketSaga(saga_id, user_id, event_id, seat_ids, payment_info)
        self.sagas[saga_id] = saga
        
        # Start the saga
        self._execute_next_step(saga)
        return saga_id
    
    def _execute_next_step(self, saga: BookingTicketSaga):
        if saga.current_step >= len(saga.steps):
            saga.state = SagaState.COMPLETED
            return
            
        step = saga.steps[saga.current_step]
        command = self._build_command(saga, step)
        
        # Send command to appropriate service
        self.producer.send(f"{step.service}-commands", command)
        step.status = "SENT"
    
    def _build_command(self, saga: BookingTicketSaga, step: SagaStep) -> Dict:
        base_command = {
            "saga_id": saga.saga_id,
            "step_id": step.step_id,
            "command": step.command,
            "timestamp": "2025-01-01T00:00:00Z"
        }
        
        if step.command == "VALIDATE_USER":
            base_command.update({"user_id": saga.user_id})
        elif step.command == "RESERVE_SEATS":
            base_command.update({
                "event_id": saga.event_id,
                "seat_ids": saga.seat_ids,
                "user_id": saga.user_id
            })
        elif step.command == "CREATE_BOOKING":
            base_command.update({
                "user_id": saga.user_id,
                "event_id": saga.event_id,
                "seat_ids": saga.seat_ids
            })
        elif step.command == "PROCESS_PAYMENT":
            base_command.update({
                "user_id": saga.user_id,
                "amount": saga.payment_info.get("amount"),
                "payment_method": saga.payment_info.get("method")
            })
            
        return base_command
    
    def handle_saga_event(self, event: Dict):
        saga_id = event.get("saga_id")
        saga = self.sagas.get(saga_id)
        
        if not saga:
            return
            
        step_id = event.get("step_id")
        status = event.get("status")
        
        if status == "SUCCESS":
            saga.current_step += 1
            self._execute_next_step(saga)
        elif status == "FAILED":
            saga.state = SagaState.COMPENSATING
            self._start_compensation(saga)
    
    def _start_compensation(self, saga: BookingTicketSaga):
        # Execute compensation commands in reverse order
        for i in range(saga.current_step - 1, -1, -1):
            step = saga.steps[i]
            if step.status == "SUCCESS" and step.compensation_command != "NONE":
                compensation_command = self._build_compensation_command(saga, step)
                self.producer.send(f"{step.service}-commands", compensation_command)
    
    def _build_compensation_command(self, saga: BookingTicketSaga, step: SagaStep) -> Dict:
        return {
            "saga_id": saga.saga_id,
            "step_id": step.step_id,
            "command": step.compensation_command,
            "timestamp": "2025-01-01T00:00:00Z"
        }
    
    def run(self):
        for message in self.consumer:
            self.handle_saga_event(message.value)