import httpx
import asyncio


async def call_agent(base_url, text):
    async with httpx.AsyncClient() as client:

        create_resp = await client.post(
            f"{base_url}/create-task",
            json={"input_text": text}
        )

        task_id = create_resp.json()["task_id"]

        while True:
            status_resp = await client.get(f"{base_url}/task/{task_id}")
            data = status_resp.json()

            if data["status"] == "completed":
                return data["result"]

            await asyncio.sleep(1)