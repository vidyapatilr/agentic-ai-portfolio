import phoenix as px
from openinference.instrumentation.openai import OpenAIInstrumentor


def setup_tracing():
    px.launch_app()
    OpenAIInstrumentor().instrument()
