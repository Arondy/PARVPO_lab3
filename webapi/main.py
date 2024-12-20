import aio_pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Конфигурация RabbitMQ и FastAPI
RABBITMQ_URL = "amqp://guest:guest@rabbitmq/"
app = FastAPI()

# Модель данных для запроса
class OrderRequest(BaseModel):
    product_id: str

# Функция для отправки сообщений в RabbitMQ
async def send_to_queue(message: dict):
    connection = await aio_pika.connect_robust(RABBITMQ_URL)

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("orders")
        await channel.default_exchange.publish(
            aio_pika.Message(body=str(message).encode()),
            routing_key=queue.name,
        )

# Эндпоинт для добавления заказа
@app.post("/order")
async def create_order(order: OrderRequest):
    message = {"product_id": order.product_id, "status": "waiting_for_processing"}

    try:
        await send_to_queue(message)
        print("Отправил сообщение в очередь!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send to queue: {e}")

    return {"product_id": order.product_id, "status": "pending"}

print("WebApi is ready!")
