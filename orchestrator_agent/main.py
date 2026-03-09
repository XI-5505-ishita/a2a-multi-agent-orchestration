import asyncio
from orchestrator_agent.core import plan_execution, call_agent, AGENTS


async def main():
    user_query = input("Enter your query: ")

    execution_plan = plan_execution(user_query)

    if not execution_plan:
        print("Could not determine execution plan.")
        return

    print("Execution Plan:", execution_plan)

    current_input = user_query

    for agent_name in execution_plan:

        selected_agent = next(
            (agent for agent in AGENTS if agent["name"] == agent_name),
            None
        )

        if not selected_agent:
            print(f"Agent {agent_name} not found.")
            return

        current_input = await call_agent(
            selected_agent["url"],
            current_input
        )

    print("\nFinal Output:\n", current_input)


if __name__ == "__main__":
    asyncio.run(main())