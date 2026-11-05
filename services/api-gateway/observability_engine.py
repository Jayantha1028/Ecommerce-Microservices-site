"""Centralized Observability, Structured Logging, and Anomaly Alarms Engine.

Provides enterprise-grade observability across all microservices:
1. Centralized in-memory ring buffer for structured logs across all tiers.
2. Real-time telemetry tracking (RPS/RPM, 4xx/5xx failure rates, P95/P99 latency).
3. Anomaly detection & alarm rules for:
   - 5XX Server Failure Rate Spikes
   - Latency Degradation Spikes (P95 > 400ms)
   - Traffic Surge Spikes
   - Service Throughput Drops / Outages
   - Microservice Health Drops
4. Developer simulation sandbox to trigger, test, and reset alarms.
"""
from __future__ import annotations

import collections
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    """Return current UTC timestamp formatted as ISO-8601."""
    return datetime.now(timezone.utc).isoformat()


class StructuredLogStore:
    """Thread-safe circular ring buffer storing up to `max_entries` structured logs."""

    def __init__(self, max_entries: int = 2000):
        self.max_entries = max_entries
        self._buffer: collections.deque = collections.deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self._seq = 0

    def add(
        self,
        service: str,
        level: str,
        category: str,
        message: str,
        path: Optional[str] = None,
        status_code: Optional[int] = None,
        latency_ms: Optional[float] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a new structured log entry."""
        with self._lock:
            self._seq += 1
            entry = {
                "id": f"log-{self._seq:06d}",
                "timestamp": _now_iso(),
                "service": service,
                "level": level.upper(),
                "category": category.upper(),
                "message": message,
                "path": path,
                "status_code": status_code,
                "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
                "correlation_id": correlation_id,
                "details": details or {},
            }
            self._buffer.append(entry)
            return entry

    def query(
        self,
        service: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 100,
        search: Optional[str] = None,
        since_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query recent logs with optional filtering and search."""
        with self._lock:
            entries = list(self._buffer)

        # Reverse so newest logs come first
        results = []
        search_lower = search.lower().strip() if search else None
        level_filter = level.upper().strip() if level else None
        service_filter = service.lower().strip() if service else None

        # Level hierarchy mapping
        levels_order = {"DEBUG": 0, "INFO": 1, "WARN": 2, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        min_level_val = levels_order.get(level_filter, 0) if level_filter else 0

        for entry in reversed(entries):
            if since_id and entry["id"] <= since_id:
                break
            if service_filter and service_filter != "all" and entry["service"].lower() != service_filter:
                continue
            entry_level_val = levels_order.get(entry["level"], 1)
            if entry_level_val < min_level_val:
                continue
            if search_lower:
                combined_text = f"{entry['service']} {entry['message']} {entry.get('path') or ''} {entry['category']}".lower()
                if search_lower not in combined_text:
                    continue
            results.append(entry)
            if len(results) >= limit:
                break

        return results

    def clear(self) -> None:
        """Clear all stored logs."""
        with self._lock:
            self._buffer.clear()


class MetricsTracker:
    """Sliding-window telemetry tracker measuring throughput, failure rates, and latency."""

    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        # List of records: (timestamp_float, status_code, latency_ms, service)
        self._requests: collections.deque = collections.deque()
        self._total_requests_all_time: int = 0
        self._total_5xx_all_time: int = 0
        self._per_service: Dict[str, Dict[str, Any]] = collections.defaultdict(
            lambda: {"requests": 0, "failures_5xx": 0, "errors_4xx": 0, "total_latency_ms": 0.0}
        )

    def record(self, method: str, path: str, status_code: int, latency_ms: float, service: str) -> None:
        """Record an incoming/completed request in the sliding metrics window."""
        now = time.time()
        with self._lock:
            self._requests.append((now, status_code, latency_ms, service))
            self._total_requests_all_time += 1
            if status_code >= 500:
                self._total_5xx_all_time += 1
            stats = self._per_service[service]
            stats["requests"] += 1
            stats["total_latency_ms"] += latency_ms
            if status_code >= 500:
                stats["failures_5xx"] += 1
            elif status_code >= 400:
                stats["errors_4xx"] += 1

            # Prune records older than sliding window
            cutoff = now - self.window_seconds
            while self._requests and self._requests[0][0] < cutoff:
                self._requests.popleft()

    def get_telemetry(self) -> Dict[str, Any]:
        """Compute aggregated telemetry metrics over the active sliding window."""
        now = time.time()
        cutoff = now - self.window_seconds

        with self._lock:
            # Clean up expired items
            while self._requests and self._requests[0][0] < cutoff:
                self._requests.popleft()
            records = list(self._requests)
            all_time_requests = self._total_requests_all_time
            all_time_5xx = self._total_5xx_all_time
            per_service_copy = {k: dict(v) for k, v in self._per_service.items()}

        total_in_window = len(records)
        rps = round(total_in_window / self.window_seconds, 2)
        rpm = round(rps * 60, 1)

        count_2xx_3xx = 0
        count_4xx = 0
        count_5xx = 0
        latencies: List[float] = []

        for _, code, lat, _ in records:
            latencies.append(lat)
            if code >= 500:
                count_5xx += 1
            elif code >= 400:
                count_4xx += 1
            else:
                count_2xx_3xx += 1

        failure_rate_pct = round((count_5xx / total_in_window * 100), 2) if total_in_window > 0 else 0.0
        client_error_rate_pct = round((count_4xx / total_in_window * 100), 2) if total_in_window > 0 else 0.0

        if latencies:
            latencies.sort()
            avg_lat = round(sum(latencies) / len(latencies), 2)
            p95_idx = int(len(latencies) * 0.95)
            p99_idx = int(len(latencies) * 0.99)
            p95_lat = round(latencies[min(p95_idx, len(latencies) - 1)], 2)
            p99_lat = round(latencies[min(p99_idx, len(latencies) - 1)], 2)
            min_lat = round(latencies[0], 2)
            max_lat = round(latencies[-1], 2)
        else:
            avg_lat = p95_lat = p99_lat = min_lat = max_lat = 0.0

        # Calculate per-service averages
        services_summary = {}
        for svc, s in per_service_copy.items():
            reqs = s["requests"]
            services_summary[svc] = {
                "total_requests": reqs,
                "failures_5xx": s["failures_5xx"],
                "errors_4xx": s["errors_4xx"],
                "avg_latency_ms": round(s["total_latency_ms"] / reqs, 2) if reqs > 0 else 0.0,
                "failure_rate_pct": round((s["failures_5xx"] / reqs) * 100, 2) if reqs > 0 else 0.0,
            }

        return {
            "window_seconds": self.window_seconds,
            "requests_in_window": total_in_window,
            "rpm": rpm,
            "rps": rps,
            "status_breakdown": {
                "2xx_3xx_success": count_2xx_3xx,
                "4xx_client_error": count_4xx,
                "5xx_server_failure": count_5xx,
            },
            "failure_rate_percent": failure_rate_pct,
            "client_error_rate_percent": client_error_rate_pct,
            "latency": {
                "min_ms": min_lat,
                "avg_ms": avg_lat,
                "p95_ms": p95_lat,
                "p99_ms": p99_lat,
                "max_ms": max_lat,
            },
            "all_time": {
                "total_requests": all_time_requests,
                "total_5xx_failures": all_time_5xx,
            },
            "services": services_summary,
        }


class AlarmManager:
    """Evaluates telemetry anomaly thresholds, manages active alarms, and handles simulations."""

    ALARM_DEFINITIONS = {
        "FAILURE_RATE_SPIKE": {
            "id": "ALARM_FAILURE_RATE_SPIKE",
            "name": "5XX Server Failure Rate Spike",
            "description": "Server failure rate (HTTP 500-599) exceeded critical threshold in active window.",
            "severity": "CRITICAL",
            "threshold": "5.0%",
            "category": "FAILURE_MEASUREMENT",
        },
        "LATENCY_SPIKE": {
            "id": "ALARM_LATENCY_SPIKE",
            "name": "P95 Latency Degradation Spike",
            "description": "95th percentile request latency exceeded performance threshold (>400ms).",
            "severity": "WARNING",
            "threshold": "400.0ms",
            "category": "LATENCY_SPIKE",
        },
        "TRAFFIC_SURGE_SPIKE": {
            "id": "ALARM_TRAFFIC_SURGE_SPIKE",
            "name": "Unusual Traffic Surge Spike",
            "description": "Throughput volume spiked significantly above baseline capacity (>300 req/min).",
            "severity": "WARNING",
            "threshold": "300 req/min",
            "category": "TRAFFIC_SPIKE",
        },
        "TRAFFIC_DROP_ANOMALY": {
            "id": "ALARM_TRAFFIC_DROP_ANOMALY",
            "name": "Service Throughput & Heartbeat Drop",
            "description": "Detected sudden drop in service throughput with upstream timeouts or failures.",
            "severity": "CRITICAL",
            "threshold": "Sudden drop to 0 req with degraded services",
            "category": "DROP_MEASUREMENT",
        },
        "SERVICE_HEALTH_DEGRADED": {
            "id": "ALARM_SERVICE_HEALTH_DEGRADED",
            "name": "Upstream Microservice Unhealthy",
            "description": "One or more core microservices failed periodic health/termination probes.",
            "severity": "CRITICAL",
            "threshold": "Health status != UP",
            "category": "HEALTH_DROP",
        },
        "CLIENT_ERROR_SPIKE": {
            "id": "ALARM_CLIENT_ERROR_SPIKE",
            "name": "4XX Client Error Surge",
            "description": "4XX error rate spiked (>25%), indicating potential brute-force or client breakage.",
            "severity": "WARNING",
            "threshold": "25.0%",
            "category": "ERROR_SPIKE",
        },
    }

    def __init__(self, log_store: StructuredLogStore):
        self.log_store = log_store
        self._simulated_alarms: Dict[str, Dict[str, Any]] = {}
        self._active_alarms: Dict[str, Dict[str, Any]] = {}
        self._history: collections.deque = collections.deque(maxlen=100)
        self._lock = threading.Lock()

    def evaluate(self, telemetry: Dict[str, Any], service_health: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Evaluate alarm conditions against current telemetry and active simulations."""
        now_iso = _now_iso()
        currently_firing: Dict[str, Dict[str, Any]] = {}

        # 1. Evaluate 5xx Failure Rate Spike
        req_count = telemetry["requests_in_window"]
        fail_pct = telemetry["failure_rate_percent"]
        if req_count >= 5 and fail_pct >= 5.0:
            currently_firing["FAILURE_RATE_SPIKE"] = {
                **self.ALARM_DEFINITIONS["FAILURE_RATE_SPIKE"],
                "current_value": f"{fail_pct}% (5xx: {telemetry['status_breakdown']['5xx_server_failure']}/{req_count})",
                "triggered_at": now_iso,
                "status": "FIRING",
            }

        # 2. Evaluate P95 Latency Spike
        p95 = telemetry["latency"]["p95_ms"]
        if req_count >= 3 and p95 >= 400.0:
            currently_firing["LATENCY_SPIKE"] = {
                **self.ALARM_DEFINITIONS["LATENCY_SPIKE"],
                "current_value": f"{p95}ms (P99: {telemetry['latency']['p99_ms']}ms)",
                "triggered_at": now_iso,
                "status": "FIRING",
            }

        # 3. Evaluate Traffic Surge Spike
        rpm = telemetry["rpm"]
        if rpm >= 300.0:
            currently_firing["TRAFFIC_SURGE_SPIKE"] = {
                **self.ALARM_DEFINITIONS["TRAFFIC_SURGE_SPIKE"],
                "current_value": f"{rpm} req/min (RPS: {telemetry['rps']})",
                "triggered_at": now_iso,
                "status": "FIRING",
            }

        # 4. Evaluate 4xx Client Error Spike
        c_err_pct = telemetry["client_error_rate_percent"]
        if req_count >= 10 and c_err_pct >= 25.0:
            currently_firing["CLIENT_ERROR_SPIKE"] = {
                **self.ALARM_DEFINITIONS["CLIENT_ERROR_SPIKE"],
                "current_value": f"{c_err_pct}% (4xx: {telemetry['status_breakdown']['4xx_client_error']}/{req_count})",
                "triggered_at": now_iso,
                "status": "FIRING",
            }

        # 5. Evaluate Service Health Degraded
        if service_health:
            unhealthy_services = [
                name for name, data in service_health.items()
                if isinstance(data, dict) and data.get("status") not in ("UP", "HEALTHY", "SYNCHRONIZED")
            ]
            if unhealthy_services:
                currently_firing["SERVICE_HEALTH_DEGRADED"] = {
                    **self.ALARM_DEFINITIONS["SERVICE_HEALTH_DEGRADED"],
                    "current_value": f"Degraded tiers: {', '.join(unhealthy_services)}",
                    "triggered_at": now_iso,
                    "status": "FIRING",
                }

        # 6. Merge Active Developer Simulations
        with self._lock:
            for sim_key, sim_data in self._simulated_alarms.items():
                currently_firing[sim_key] = sim_data

            # Track transitions (new triggers vs resolved)
            previous_keys = set(self._active_alarms.keys())
            current_keys = set(currently_firing.keys())

            new_triggers = current_keys - previous_keys
            resolved = previous_keys - current_keys

            for key in new_triggers:
                alarm = currently_firing[key]
                self._history.append({
                    "alarm_id": key,
                    "event": "TRIGGERED",
                    "timestamp": now_iso,
                    "severity": alarm["severity"],
                    "value": alarm.get("current_value"),
                })
                self.log_store.add(
                    service="api-gateway",
                    level="CRITICAL" if alarm["severity"] == "CRITICAL" else "WARN",
                    category="ALARM",
                    message=f"🚨 ALARM FIRED [{alarm['name']}]: {alarm.get('current_value')} (Threshold: {alarm['threshold']})",
                    details=alarm,
                )

            for key in resolved:
                old_alarm = self._active_alarms[key]
                self._history.append({
                    "alarm_id": key,
                    "event": "RESOLVED",
                    "timestamp": now_iso,
                    "severity": old_alarm["severity"],
                })
                self.log_store.add(
                    service="api-gateway",
                    level="INFO",
                    category="ALARM",
                    message=f"✅ ALARM RESOLVED [{old_alarm['name']}]: Conditions normalized to healthy baseline.",
                    details=old_alarm,
                )

            self._active_alarms = currently_firing
            return list(self._active_alarms.values())

    def simulate(self, alarm_type: str, action: str = "trigger") -> Dict[str, Any]:
        """Simulate an alarm trigger or resolution for observability testing."""
        alarm_type = alarm_type.upper().strip()
        action = action.lower().strip()

        with self._lock:
            if action == "reset":
                if alarm_type == "ALL":
                    cleared = list(self._simulated_alarms.keys())
                    self._simulated_alarms.clear()
                    return {"status": "SUCCESS", "message": f"Cleared all simulated alarms: {cleared}"}
                elif alarm_type in self._simulated_alarms:
                    del self._simulated_alarms[alarm_type]
                    return {"status": "SUCCESS", "message": f"Cleared simulated alarm: {alarm_type}"}
                return {"status": "NOOP", "message": f"Alarm {alarm_type} was not active in simulation."}

            # Trigger simulation
            definition = self.ALARM_DEFINITIONS.get(alarm_type)
            if not definition:
                raise ValueError(f"Unknown alarm type '{alarm_type}'. Valid types: {list(self.ALARM_DEFINITIONS.keys())}")

            mock_values = {
                "FAILURE_RATE_SPIKE": "32.4% (Simulated Spike: 18 failures / 55 reqs)",
                "LATENCY_SPIKE": "845.2ms (Simulated Spike: Upstream product-db query lag)",
                "TRAFFIC_SURGE_SPIKE": "420.0 req/min (Simulated Flash Sale Traffic Spike)",
                "TRAFFIC_DROP_ANOMALY": "0 req/sec (Simulated Network Partition Drop)",
                "SERVICE_HEALTH_DEGRADED": "payment-service (Simulated Port 8003 Unreachable)",
                "CLIENT_ERROR_SPIKE": "44.0% (Simulated 401 Unauthorized Surge)",
            }

            now_iso = _now_iso()
            sim_alarm = {
                **definition,
                "current_value": mock_values.get(alarm_type, "Simulated Threshold Breach"),
                "triggered_at": now_iso,
                "status": "FIRING",
                "simulated": True,
            }
            self._simulated_alarms[alarm_type] = sim_alarm
            return {"status": "SUCCESS", "message": f"Simulated alarm {alarm_type} is now FIRING", "alarm": sim_alarm}

    def get_summary(self) -> Dict[str, Any]:
        """Retrieve active alarms and configured alarm rules."""
        with self._lock:
            active = list(self._active_alarms.values())
            history = list(self._history)

        critical_count = sum(1 for a in active if a.get("severity") == "CRITICAL")
        warning_count = sum(1 for a in active if a.get("severity") == "WARNING")

        overall_status = "CRITICAL" if critical_count > 0 else ("WARNING" if warning_count > 0 else "HEALTHY")

        return {
            "overall_status": overall_status,
            "active_count": len(active),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "active_alarms": active,
            "recent_history": history[-20:],
            "configured_rules": list(self.ALARM_DEFINITIONS.values()),
        }


# ==============================================================================
# Global Engine Instances & Initial System Bootstrap
# ==============================================================================
log_store = StructuredLogStore(max_entries=2000)
metrics_tracker = MetricsTracker(window_seconds=60)
alarm_manager = AlarmManager(log_store=log_store)

# Seed initial baseline startup logs so developer console displays operational context immediately
log_store.add(
    service="api-gateway",
    level="INFO",
    category="SYSTEM",
    message="E-Commerce API Gateway initialized with full reverse proxy routing.",
    path="/",
    status_code=200,
)
log_store.add(
    service="api-gateway",
    level="INFO",
    category="SYSTEM",
    message="Observability & Telemetry Engine activated: tracking RPS, failure spikes, latency degradation, and traffic drops.",
)
log_store.add(
    service="api-gateway",
    level="INFO",
    category="SYSTEM",
    message="Crossplane continuous drift detection active for 12 containers: status SYNCHRONIZED.",
)
log_store.add(
    service="api-gateway",
    level="INFO",
    category="SYSTEM",
    message="Service Termination Protection Guard active across 6 microservices & 5 PostgreSQL databases.",
)
