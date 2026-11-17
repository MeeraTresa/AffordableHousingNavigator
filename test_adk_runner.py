import os
import asyncio

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent.navigator.agent import root_agent

async def main():
    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, session_service=session_service)
    session = await session_service.create_session(app_name="navigator", user_id="user1")
    print("Session created:", session.id)

    response = await runner.run_turn(
        session_id=session.id,
        user_id="user1",
        user_message="Hello, I am a paralegal intake worker. I have a tenant facing eviction on 1000 Block St Nicholas Avenue. Hearing date is 2026-11-23T09:30. Conditions are freezing cold, no heat and mold around bathtub. Can you open the case and check for evidence?",
    )
    print("Response text:\n", response.text if hasattr(response, "text") else response)

if __name__ == "__main__":
    asyncio.run(main())
