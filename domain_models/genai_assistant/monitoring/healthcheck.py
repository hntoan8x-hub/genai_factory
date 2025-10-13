from typing import Dict, Any

class HealthChecker:
    """
    Performs routine health checks on key services and dependencies.
    """

    def __init__(self, service_dependencies: Dict[str, Any]):
        """
        Initializes the health checker with its dependencies.
        
        Args:
            service_dependencies (Dict[str, Any]): A dictionary of services to check,
                                                   e.g., {"db_connection": db_conn}.
        """
        self.dependencies = service_dependencies

    def check_all(self) -> Dict[str, Any]:
        """
        Runs a health check on all registered services.
        
        Returns:
            Dict[str, Any]: A report of the health status of each service.
        """
        report = {"status": "ok", "checks": {}}
        
        # Check LLM connectivity
        try:
            # Placeholder: In a real app, this would ping the LLM provider
            is_llm_up = True 
            report["checks"]["llm_connectivity"] = {"status": "ok" if is_llm_up else "degraded"}
        except Exception as e:
            report["checks"]["llm_connectivity"] = {"status": "unhealthy", "error": str(e)}
            report["status"] = "degraded"

        # Check database connection
        db_conn = self.dependencies.get("db_connection")
        if db_conn:
            try:
                # Placeholder: In a real app, this would execute a simple query
                is_db_up = True
                report["checks"]["db_connection"] = {"status": "ok" if is_db_up else "degraded"}
            except Exception as e:
                report["checks"]["db_connection"] = {"status": "unhealthy", "error": str(e)}
                report["status"] = "degraded"
        
        # If any check is unhealthy, mark the overall status as unhealthy
        if any(c["status"] == "unhealthy" for c in report["checks"].values()):
            report["status"] = "unhealthy"
            
        return report
