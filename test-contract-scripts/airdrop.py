from terra_sdk.client.localterra import LocalTerra
from terra_sdk.util.contract import read_file_as_b64, get_code_id, get_contract_address
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract


terra = LocalTerra()
deployer = terra.wallets["test2"]
customer = terra.wallets["test3"]

# print("deployer", deployer.key.acc_address)
# print("customer", customer.key.acc_address)

def remove_decimal_point(src:str) -> str:
    return src.replace(".","")

# contract libraries
def store_contract(contract_name: str, sequence) -> str:
    contract_bytes = read_file_as_b64(f"artifacts/{contract_name}.wasm")
    store_code = MsgStoreCode(
        deployer.key.acc_address,
        contract_bytes
    )

    tx = deployer.create_and_sign_tx(
        msgs = [store_code], fee=StdFee(400000000, "10000000uluna"), sequence=sequence
    )

    result = terra.tx.broadcast(tx)

    code_id = get_code_id(result)

    return code_id

def instantiate_contract(code_id: str, init_msg, sequence) -> str:
    instantiate = MsgInstantiateContract(
        admin=deployer.key.acc_address, sender=deployer.key.acc_address , code_id=code_id, init_msg=init_msg
    )
    tx = deployer.create_and_sign_tx(
        msgs=[instantiate], fee=StdFee(400000000, "10000000uluna"), sequence=sequence
    )

    result = terra.tx.broadcast(tx)

    contract_address = get_contract_address(result)

    return contract_address


def execute_contract(
        sender, contract_addr: str, execute_msg, sequence, coins=None, account_number=None
):
    execuete = MsgExecuteContract(
        sender=sender.key.acc_address,
        contract=contract_addr,
        execute_msg=execute_msg,
        coins=coins
    )

    tx = sender.create_and_sign_tx(
        msgs=[execuete], fee=StdFee(400000000, "10000000uluna"), sequence=sequence, account_number=account_number
    )

    result = terra.tx.broadcast(tx)

    print(result)

    return result

sequence = terra.auth.account_info(deployer.key.acc_address).sequence

token_code_id = store_contract("astroport_lbp_token", sequence)
airdrop_code_id = store_contract("cw20_merkle_airdrop", sequence + 1)

# create aurora token
boomco_token = instantiate_contract(
    token_code_id,
    {
        "name": "Boomco Token",
        "symbol": "Boomco",
        "decimals": 6,
        "initial_balances": [
            {"address": deployer.key.acc_address, "amount": remove_decimal_point("100.000000")}
        ]
    },
    sequence+2
)

print("token", boomco_token)

airdrop_contract = instantiate_contract(
    airdrop_code_id,
    {
        "owner": deployer.key.acc_address,
        "cw20_token_address": boomco_token,
    },
    sequence+3
)

# Register root
execute_contract(
    deployer,
    airdrop_contract,
    {
        "register_merkle_root": {
            "merkle_root": "951339dd60914ab440c9438f560a0d2b02396cdeb05d859d34c216be97aa439e"
        }
     },
    sequence+4
)

# Claim the coin
execute_contract(
    deployer,
    airdrop_contract,
    {
        "claim": {
            "stage": 1,
            "amount": "0",
            "proof": [
                "815539860becd80f5ba019096c9e48d5e246dee81f54eeecfa0fae59a0855f81",
            ]
        }
    },
    sequence+5
)

