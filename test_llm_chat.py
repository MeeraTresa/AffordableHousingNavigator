import asyncio
from google.genai import Client
from agent.navigator.agent import root_agent

async def main():
    print("Agent model:", root_agent.model)
    print("Tools:", [t.__name__ if hasattr(t, '__name__') else str(t) for t in root_agent.tools])
    client = Client()
    # Let's see how ADK agent runs
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    runner = Runner(agent=root_agent, session_service=session_service)
    
    session = await session_service.create_session(app_name="navigator", user_id="user1")
    print("Created session:", session.id)

    response = await runner.run_turn(
        session_id=session.id,
        user_id="user1",
        user_message="Hello! I am a paralegal doing intake for a new tenant facing eviction on 1000 Block St Nicholas Avenue. Hearing is next Monday Nov 23 at 9:30 AM. Conditions are no heat and black mold.",
    )
    print("Response type:", type(response))
    print("Response text:", response)

if __name__ == "__main__":
    asyncio.run(main())
