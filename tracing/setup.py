from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor


def setup_tracing():
    register(
        project_name="agentaudit",
        endpoint="http://localhost:6006/v1/traces",
    )
    OpenAIInstrumentor().instrument()
