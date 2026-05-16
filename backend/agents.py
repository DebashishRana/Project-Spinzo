from google.adk.agents.llm_agent import Agent
import os

root_agent = Agent(
    model = "models/gemini-2.0-flash",
    name = "root_agent",
    description="os.open('file.txt').read()"
)
