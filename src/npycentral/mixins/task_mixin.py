"""Task execution and monitoring methods."""
import logging
import time
from typing import Any, Dict, List, Optional

from ..exceptions import TaskError

logger = logging.getLogger(__name__)


class TaskMixin:
    """Task execution and monitoring methods."""

    def run_task(
        self,
        repo_id: int,
        task_name: str,
        customer_id: int,
        device_id: int,
        task_type: str = "Automation Policy",
        parameters: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Run a script or Automation Policy on a device.

        Args:
            repo_id: Repository/item ID of the task
            task_name: Name of the task to run
            customer_id: Customer ID
            device_id: Device ID to run the task on
            task_type: Type of task (default: "Automation Policy")
            parameters: Optional list of task parameters

        Returns:
            dict: API response containing task details

        Raises:
            APIError: If the API request fails
        """
        payload = {
            "name": task_name,
            "itemId": repo_id,
            "taskType": task_type,
            "customerId": customer_id,
            "deviceId": device_id,
            "credential": {
                "type": "LocalSystem",
                "username": None,
                "password": None
            },
            "parameters": parameters or []
        }
        logger.info(f"Running task '{task_name}' on device {device_id}")
        return self.post("scheduled-tasks/direct", data=payload)

    def check_task_status(self, task_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve detailed status information for a task.

        Args:
            task_id: Task ID to check

        Returns:
            list: List of task detail dictionaries

        Raises:
            APIError: If the API request fails
        """
        task_details = self.get(f"scheduled-tasks/{task_id}/status/details").get("data", [])
        return task_details if task_details else []

    def monitor_task(
        self,
        task_id: int,
        interval: int = 15,
        timeout: int = 60 * 10
    ) -> Dict[str, Any]:
        """
        Monitor a task until completion or timeout.

        Args:
            task_id: Task ID to monitor
            interval: Polling interval in seconds (default: 15)
            timeout: Maximum wait time in seconds (default: 600)

        Returns:
            dict: Dictionary with 'status' and 'task' keys

        Raises:
            APIError: If the API request fails
        """
        END_STATUSES = ["Failed", "Success"]
        start_time = time.monotonic()
        logger.info(f"Monitoring task {task_id} (timeout: {timeout}s, interval: {interval}s)")

        while True:
            task_details = self.check_task_status(task_id)
            if not task_details:
                status = "Unknown"
                task = {}
                logger.warning(f"Task {task_id} returned no details")
            else:
                task = task_details[0]
                status = task.get("status")

            if status in END_STATUSES:
                logger.info(f"Task {task_id} completed with status: {status}")
                return {"status": status, "task": task}

            elapsed = time.monotonic() - start_time
            if elapsed >= timeout:
                logger.warning(f"Task {task_id} timed out after {elapsed:.1f}s")
                return {"status": "Timeout", "task": task}

            time.sleep(interval)

    def run_and_monitor_task(
        self,
        repo_id: int,
        task_name: str,
        customer_id: int,
        device_id: int,
        task_type: str = "AutomationPolicy",
        parameters: Optional[List[Dict[str, str]]] = None,
        interval: int = 15,
        timeout: int = 60 * 10,
    ) -> Dict[str, Any]:
        """
        Run a task and block until completion.

        Args:
            repo_id: Repository/item ID of the task
            task_name: Name of the task to run
            customer_id: Customer ID
            device_id: Device ID to run the task on
            task_type: Type of task (default: "AutomationPolicy")
            parameters: Optional list of task parameters
            interval: Polling interval in seconds (default: 15)
            timeout: Maximum wait time in seconds (default: 600)

        Returns:
            dict: Dictionary containing task_id, status, and full_response

        Raises:
            TaskError: If task creation fails
            APIError: If the API request fails
        """
        response = self.run_task(
            repo_id=repo_id,
            task_name=task_name,
            customer_id=customer_id,
            device_id=device_id,
            task_type=task_type,
            parameters=parameters,
        )

        task_id = response.get("data", {}).get("taskId")
        if not task_id:
            error_msg = "Failed to create task - no taskId in response"
            logger.error(error_msg)
            raise TaskError(error_msg)

        final_status = self.monitor_task(
            task_id=task_id,
            interval=interval,
            timeout=timeout,
        )

        return {
            "task_id": task_id,
            "status": final_status,
            "full_response": final_status,
            "device_id": device_id,
            "customer_id": customer_id,
        }
