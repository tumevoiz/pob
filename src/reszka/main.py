from typing import Any

from fastapi import FastAPI

from reszka.crypto import Blockchain, POWMiner, Block, CreateBlockRequest

app = FastAPI()

miner = POWMiner(3)
blockchain = Blockchain(miner)


@app.get('/blocks', response_model=list[Block])
def get_blocks() -> Any:
    return blockchain.blocks


@app.post('/blocks')
def create_block(create_block_request: CreateBlockRequest) -> Any:
    blockchain.add_block(create_block_request)
    return {'status': 'adding'}