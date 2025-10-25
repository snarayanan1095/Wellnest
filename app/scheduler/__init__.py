# Scheduler package
from .routine_learner import start_scheduler as start_routine_scheduler, shutdown_scheduler as shutdown_routine_scheduler
from .anomaly_scheduler import start_scheduler as start_anomaly_scheduler, shutdown_scheduler as shutdown_anomaly_scheduler

def start_scheduler():
    """Start all schedulers"""
    start_routine_scheduler()
    start_anomaly_scheduler()

def shutdown_scheduler():
    """Shutdown all schedulers"""
    shutdown_routine_scheduler()
    shutdown_anomaly_scheduler()

__all__ = ["start_scheduler", "shutdown_scheduler"]
