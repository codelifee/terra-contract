from dis import code_info

from terra_sdk.client.localterra import LocalTerra
from terra_sdk.util.contract import read_file_as_b64, get_code_id, get_contract_address
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd import LCDClient

terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")

mk = MnemonicKey(mnemonic = "nut mouse enlist brief spin empower coin brother actual unveil ticket diesel traffic quiz useless oil swing artefact tomato tennis topple betray banana gate")

# deployer = lt.wallets["test1"]
deployer = terra.wallet(mk)

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
    # contract_address = result.logs[0].events_by_type[
    #     "instantiate_contract"
    # ]["contract_address"][0]

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

    print(f"sequence {sequence}")
    print(f"coins {coins}")

    result = terra.tx.broadcast(tx)

    print(f"tx {tx}")
    print(f"result {result}")

    return result

# we need to increase the sequence cuz it runs too fast. the sequence overlaps
sequence = terra.auth.account_info(deployer.key.acc_address).sequence

token_code_id = store_contract("terraswap_token", sequence)
# contract_address =instantiate_contract(token_code_id, {"name":"aurora","symbol":"SYMBOL","decimals": 3,"initial_balances":[{"address":"terra1x46rqay4d3cssq8gxxvqz8xt6nwlz4td20k38v","amount":"10000"},{"address":"terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp","amount":"10000"}]}, sequence+1)
# print(terra.wasm.contract_query(contract_address, {"balance":{"address": "terra17lmam6zguazs5q5u6z5mmx76uj63gldnse2pdp"}}))
pair_code_id = store_contract("terraswap_pair", sequence+1)
factory_code_id = store_contract("terraswap_factory", sequence+2)

# create normal ts factory
factory = instantiate_contract(
    factory_code_id,
    {"token_code_id": int(token_code_id), "pair_code_id": int(pair_code_id)},
    sequence+3
)

# create aurora token
aurora_token = instantiate_contract(
    token_code_id,
    {
        "name": "Aurora Token",
        "symbol": "NORM",
        "decimals": 6,
        "initial_balances": [
            {"address": deployer.key.acc_address, "amount": "10000000"}
        ]
    },
    sequence+4
)

# create aurora-LUNA pair
result = execute_contract(
    deployer,
    factory,
    {
        "create_pair": {
            "asset_infos": [
                {"token": {"contract_addr": aurora_token}},
                {"native_token": {"denom": "uluna"}},
            ]
        }
    },
    sequence+5
)

token_pair = result.logs[0].events_by_type["from_contract"]["pair_contract_addr"][0]
print(f"token pair contract: {token_pair}")

# provide liquidity
execute_contract(
    deployer,
    aurora_token,
    {"increase_allowance": {"spender": token_pair, "amount": "10000000"}},
    sequence+6
)

execute_contract(
    deployer,
    token_pair,
    {
     "provide_liquidity": {
         "assets": [
             {
                 "info": {
                     "token": {
                         "contract_addr": aurora_token
                     }
                 },
                 "amount": "1000000"
             },
             {"info": {"native_token": {"denom": "uluna"}}, "amount": "1000000"},
         ]
     },
    },
    sequence+7,
    "1000000uluna",
)

print(
    "Token pair's balance of aurora_token: ",
    terra.wasm.contract_query(aurora_token, {"balance": {"address": token_pair}})[
        "balance"
    ]
)