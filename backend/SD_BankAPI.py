from datetime import datetime
from email.policy import default
import json
from fastapi import FastAPI, Response
import secrets
import databases
import sqlalchemy
import uuid
from pydantic import BaseModel, confloat, constr
from fastapi.middleware.cors import CORSMiddleware

## TODO
## SISTEMARE SOVRAPPOSIZIONE DI NOMI, LA CRONOLOGIA TRANSAZIONI
## Dipendenze
## Dipendenze da installare: databases, sqlalchemy, secrets (?) 

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///./banca.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("accountId", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String),
    sqlalchemy.Column("surname", sqlalchemy.String),
    sqlalchemy.Column("balance", sqlalchemy.Float),
    sqlalchemy.Column("accountDate", sqlalchemy.DateTime),
)

transactions = sqlalchemy.Table(
    "transactions",
    metadata,
    sqlalchemy.Column("sender", sqlalchemy.String,),
    sqlalchemy.Column("receiver", sqlalchemy.String),
    sqlalchemy.Column("transactionId", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("amount", sqlalchemy.Float),
    sqlalchemy.Column("transactionDate", sqlalchemy.DateTime),
)

withdraws = sqlalchemy.Table(
    "withdraws",
    metadata,
    sqlalchemy.Column("IDaccount", sqlalchemy.String,),
    sqlalchemy.Column("quantity", sqlalchemy.Float),
    sqlalchemy.Column("withdrawId", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("operationType", sqlalchemy.String),
    sqlalchemy.Column("operationDate", sqlalchemy.DateTime),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

metadata.create_all(engine)

class User(BaseModel):
    accountId: str
    name: str
    surname: str
    balance: float
    accountDate: datetime
    
class UserIn(BaseModel):
    name: constr(min_length=2, max_length=10)
    surname: constr(min_length=2, max_length=10)
    balance: confloat(multiple_of=0.5)
    ##accountDate: datetime

class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: float
    transactionId: float
    transactionDate: datetime

class TransactionIn(BaseModel):
    sender: str
    receiver: str
    amount: float

class DivertIn(BaseModel):
    transactionId : str

def random_hex():
    res = secrets.token_hex(10)
    return res

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/api/account")
async def read_users():
    query = users.select()

    return await database.fetch_all(query)

@app.post("/api/account")
async def insert_user(user: UserIn = None):
    id = random_hex()
    query = users.insert().values(accountId=id, name=user.name, surname=user.surname, balance=user.balance, accountDate= datetime.now())
    await database.execute(query)

    return {"id": id}

@app.delete("/api/account")
async def remove_user(id: str):
    query = users.delete().where(users.c.accountId == id)
    last_record_id = await database.execute(query)

    return (last_record_id)

@app.get("/api/account/{accountId}")
async def return_user_info(accountId: str, response: Response):
    list = []
    query = users.select().where(users.c.accountId == accountId)
    user_info = await database.fetch_one(query)
    list.append({"user_info" : user_info})
    query = transactions.select().where(transactions.c.sender == accountId) 
    user_transactions = await database.fetch_all(query)
    list.append({"transactions" : user_transactions})
    query = withdraws.select().where(withdraws.c.IDaccount == accountId) ##DA SISTEMARE IN CASO
    user_withdraw = await database.fetch_all(query)
    list.append({"withdraws" : user_withdraw})
    response.headers["X-Sistema-Bancario"] = user_info[1]+";"+user_info[2]
    return (list)

@app.post("/api/account/{accountId}")
async def deposit_user(accountId: str, amount: float):
    uuidStr = uuid.uuid4()
    if (amount > 0):
        operation = "versamento"
    else:
        operation = "prelievo"
    ## Il controllo si può anche fare da front-end (fetchando il balance a inizio caricamento pagina) ma vabbè
    balance_query = users.select().where(users.c.accountId == accountId) 
    Balance = await database.fetch_one(balance_query)
    insert_withdraw = withdraws.insert().values(
        IDaccount = accountId,
        quantity = abs(amount),
        withdrawId = str(uuidStr),
        operationType = operation,
        operationDate = datetime.now(),
    ) 
    if (amount < 0 and Balance[3] < abs(amount)):
        print("Not enough credit!")
        return ({"success": "FALSE", "error_description" : "You are too poor for this!"})
    else:
        await update_balance(accountId, amount, False)
        await database.execute(insert_withdraw)
    return ({"withdrawId": uuidStr, "newBalance": amount+Balance[3], "oldBalance": Balance[3]})

@app.put("/api/account/{accountId}")
async def update_user(accountId: str, name: str, surname: str):
    query = users.update().where(users.c.accountId == accountId).values(
        name = name,
        surname = surname, 
    )
    await database.execute(query)

@app.patch("/api/account/{accountId}")
async def update_user(accountId: str, name: str, surname: str):
    query = users.update().where(users.c.accountId == accountId).values(
        name = name,
        surname = surname, 
    )
    await database.execute(query)

@app.head("/api/account/{accountId}")
async def head_user(accountId: str, response: Response):
    query = users.select().where(users.c.accountId == accountId)
    user_info = await database.fetch_one(query)
    print(user_info)
    response.headers["X-Sistema-Bancario"] = user_info[1]+";"+user_info[2]

@app.post("/api/transfer")
async def transfer_money(transfer: TransactionIn):
    return await transaction(transfer.sender, transfer.receiver, transfer.amount)

@app.post("/api/divert")
async def divert_transaction(Divert: DivertIn):
    query = transactions.select().where(
        transactions.c.transactionId == Divert.transactionId
    )
    res = await database.fetch_one(query)

    sender = res[1]
    receiver = res[0]
    amount = res[3]

    if(await check_sender_balance(sender, amount)):
        await update_balance(sender, amount, True)
        await update_balance(receiver, amount, False)
        uuid = await insert_transaction(sender, receiver, amount)
    else:
        return{"Error": "Sender has not enough money!"}

    return uuid


async def check_sender_balance(sender: str, amount):
    balance_query = users.select().where(users.c.accountId == sender) 
    Balance = await database.fetch_one(balance_query)
    if (amount <= 0 or Balance[3] < amount):
        return False
    else:
        return True

async def update_balance(accountId: str, amount: float, sender: bool):
    if (sender):
        amount = (amount * -1)

    balance_query = users.select().where(users.c.accountId == accountId) 
    Balance = await database.fetch_one(balance_query)    
    balance_update_query = users.update().where(users.c.accountId == accountId).values(
        balance = Balance[3] + amount
    )
    await database.execute(balance_update_query)
    return Balance[3] + amount

async def transaction(sender: str, receiver: str, amount: float):
    if (not await check_sender_balance(sender, amount)):
        return ({"success": "FALSE", "error_description" : "not enough credit or negative number"})
    sender_balance = await update_balance(sender, amount, True) ##Sender amount updated
    receiver_balance = await update_balance(receiver, amount, False) ##Receiver amount updated
    await insert_transaction(sender, receiver, amount)
    return {"sender_balance": sender_balance, "receiver_balance": receiver_balance}

async def insert_transaction(sender: str, receiver: str, amount: float):
    uuidStr = str(uuid.uuid4())
    insert_transaction = transactions.insert().values(
        sender = sender,
        receiver = receiver,
        amount = amount,
        transactionId = uuidStr,
        transactionDate = datetime.now(),
    ) 
    ok = await database.execute(insert_transaction)
    print(ok)
    return uuidStr
