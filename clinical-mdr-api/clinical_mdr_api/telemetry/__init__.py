# Keep this imported so that we don't have to update our logging-azure.yaml in deployment
from clinical_mdr_api.telemetry.logging_filter import TracingContextFilter
from clinical_mdr_api.telemetry.tracing import *
