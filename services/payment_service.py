# Payment service stub
async def create_payment(amount: float, user_id: int):
    return {'status': 'created', 'amount': amount}
