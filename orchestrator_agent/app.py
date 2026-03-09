from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator_agent.core import plan_execution, call_agent, AGENTS

app = FastAPI(title="Orchestrator Agent")


class ExecuteRequest(BaseModel):
    input_text: str


@app.post("/execute")
async def execute(request: ExecuteRequest):

    execution_plan = plan_execution(request.input_text)

    if not execution_plan:
        return {"error": "Could not determine execution plan"}

    current_input = request.input_text

    for agent_name in execution_plan:

        selected_agent = next(
            (agent for agent in AGENTS if agent["name"] == agent_name), None
        )

        if not selected_agent:
            return {"error": f"Agent {agent_name} not found"}

        current_input = await call_agent(selected_agent["url"], current_input)

    return {"execution_plan": execution_plan, "final_output": current_input}
