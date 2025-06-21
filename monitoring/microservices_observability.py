from opentelemetry import trace

class MicroservicesObservability:
    def monitor_service(self, service_name):
        """
        Monitor microservices met OpenTelemetry.
        """
        tracer = trace.get_tracer(service_name)
        with tracer.start_as_current_span("monitoring"):
            return f"Monitoring {service_name}"
