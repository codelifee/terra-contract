from terra_sdk.client.localterra import LocalTerra
from terra_sdk.util.contract import read_file_as_b64, get_code_id, get_contract_address
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract


terra = LocalTerra()
deployer = terra.wallets["test2"]

# libraries
def add_decimal_point(src:str, decimal = 6) -> str:
    tmp_int = int(src)
    return "%d.%d" % ( tmp_int/ (10**decimal) , tmp_int % (10**decimal) )

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
        sender, contract_addr: str, execute_msg, sequence, coins=None
):
    execuete = MsgExecuteContract(
        sender=sender.key.acc_address,
        contract=contract_addr,
        execute_msg=execute_msg,
        coins=coins
    )

    tx = sender.create_and_sign_tx(
        msgs=[execuete], fee=StdFee(400000000, "10000000uluna"), sequence=sequence
    )

    result = terra.tx.broadcast(tx)

    print(result)

    return result


sequence = terra.auth.account_info(deployer.key.acc_address).sequence

token_code_id = store_contract("astroport_lbp_token", sequence)
sale_code_id = store_contract("cosmwasm_16", sequence+1)

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

sale_contract = instantiate_contract(
    sale_code_id,
    {
        "cw20_address": boomco_token,
        "denom": "uusd",
        "price": "1"
    },
    sequence+3
)

# Deposit cw20 Tokens
execute_contract(
    deployer,
    boomco_token,
    {"send":
         {"amount":"100",
          "contract":sale_contract,
          "msg":""}
     },
    sequence+4
)

# Set Price
execute_contract(
    deployer,
    sale_contract,
    {"set_price":
         {"price":"1",
          "denom":"uusd"}
     },
    sequence+5
)

# Buy cw20 coin
execute_contract(
    deployer,
    sale_contract,
    {
        "buy":{
            "denom": "uusd",
            "price": "1",
        }
    },
    sequence+6,
    "2uusd"
)