from database.queries import list_available_bikes

async def get_available_bikes():
    return await list_available_bikes()
