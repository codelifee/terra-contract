from re import S
from typing import Sequence
from attr import Factory
from terra_sdk.client.lcd.api.tx import BroadcastOptions

from terra_sdk.client.localterra import LCDClient, LocalTerra
from terra_sdk.util.contract import read_file_as_b64, get_code_id, get_contract_address
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd import LCDClient
from datetime import date, datetime, timedelta;
import time;

terra = LocalTerra()
deployer = terra.wallets["test1"]

# terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")
# mk = MnemonicKey(mnemonic = "nut mouse enlist brief spin empower coin brother actual unveil ticket diesel traffic quiz useless oil swing artefact tomato tennis topple betray banana gate")
# deployer = terra.wallet(mk)

def store_contract(contract_name : str, sequence) -> str :
    """Uploads contract, returns code ID"""
    contract_bytes = read_file_as_b64(f"artifacts/{contract_name}.wasm")
    storre_code = MsgStoreCode(
        deployer.key.acc_address,
        contract_bytes
    )
    tx = deployer.create_and_sign_tx(
        msgs=[storre_code], fee=StdFee(40000000, "10000000uluna"), sequence=sequence
    )
    # tx = deployer.create_and_sign_tx(
    #     msgs=[storre_code], sequence=sequence
    # )

    result = terra.tx.broadcast(tx)
    code_id = get_code_id(result)
    return code_id

def instanticate_contract(code_id: str, init_msg, sequence) -> str :
    """Instantiates a new contract with code_id and init_msg, returns address"""
    instantiate = MsgInstantiateContract(
        admin=deployer.key.acc_address, sender=deployer.key.acc_address , code_id=code_id, init_msg=init_msg
    )

    tx = deployer.create_and_sign_tx(
        msgs=[instantiate], fee=StdFee(400000000, "10000000uluna"), sequence=sequence
    )
    # tx = deployer.create_and_sign_tx(
    #     msgs=[instantiate], sequence=sequence
    # )

    result = terra.tx.broadcast(tx)

    contract_address = get_contract_address(result)
    return contract_address

def execute_contract(sender: str, contract_addr : str, execute_msg, sequence=None, coins=None):
    execute = MsgExecuteContract(
        sender = sender.key.acc_address,
        contract = contract_addr,
        execute_msg = execute_msg,
        coins=coins
    )
    tx = deployer.create_and_sign_tx(
        msgs=[execute],  fee=StdFee(40000000, "10000000uluna"), sequence = sequence
    )
    # tx = deployer.create_and_sign_tx(
    #     msgs=[execute], sequence = sequence
    # )
    result = terra.tx.broadcast(tx)

    print(result)

    return result

sequence = terra.auth.account_info(deployer.key.acc_address).sequence
# sequence = 0


token_code_id = store_contract("astroport_lbp_token", sequence)
pair_code_id = store_contract("astroport_lbp_pair", sequence+1)
factory_code_id = store_contract("astroport_lbp_factory", sequence+2)


# create ts factory
print("create ts factory")
factory = instanticate_contract(
    factory_code_id,
    {"token_code_id":int(token_code_id), "pair_code_id":int(pair_code_id), "owner":deployer.key.acc_address},
    sequence+3
)

# create cw20 token
print("create cw20 token")
normal_token = instanticate_contract(
    token_code_id,
    {
        "name": "boomco_test_astroport",
        "symbol": "boomcoAstro",
        "decimals": 6,
        "initial_balances": [
            {
                "address": deployer.key.acc_address,
                "amount": "500000000000000"
            }
        ],
    },
    sequence+4
)

print(terra.wasm.contract_query(normal_token, {"token_info": {}}))
print(terra.wasm.contract_query(factory, {"config": {}}))
print( factory, normal_token, '\n')

start_timestamp = int( time.mktime(datetime.today().timetuple() ) ) 
end_timestamp = int( time.mktime(datetime.today().timetuple() ) + 60 * 60 )

# create cw20 - luna pair
print("create cw20 - luna pair")
print(start_timestamp, end_timestamp)
result = execute_contract(
    deployer,
    factory,
    {
        "create_pair": {
            "asset_infos": [
                {
                    "info": {
                        "token": {
                            "contract_addr" : normal_token
                        }
                    },
                    "start_weight":'5000',
                    "end_weight":'5000'
                },
                {
                    "info": {
                        "native_token" : {
                            "denom":"uluna"
                        }
                    },
                    "start_weight":'1',
                    "end_weight":'5'
                },
            ],
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "description": "this pair description is optional"
        }
    },
    sequence+5
)

normal_pair = result.logs[0].events_by_type["from_contract"]["pair_contract_addr"][0]
print(f"pair contract is : {normal_pair} ")

# provide liquidity -- cw20 token
# 1. increase_allowance
print("provide liquidity : 1. increase_allowance")
execute_contract(
    deployer,
    normal_token,
    {"increase_allowance":{"spender":normal_pair, "amount" : "5000000000000000"}},
    sequence+6
)
# 2. provide_liquidity
print("provide liquidity : 2. provide_liquidity")
execute_contract(
    deployer,
    normal_pair,
    {
        "provide_liquidity": {
            "assets": [
                {
                    "info" : {"token": {"contract_addr": normal_token}},
                    "amount": "500000000000000"
                },
                {
                    "info" : {"native_token": {"denom": "uluna"}},
                    "amount": "100000000000"
                }
            ]
        }
    },
    sequence+7,
    "100000000000uluna",
)

# compare balance
print(
    "pair's balance of CW20 is : ",
    terra.wasm.contract_query(normal_token, {"balance":{"address":deployer.key.acc_address}})["balance"],
)

print("pair", normal_pair)
print("token", normal_token)

# # swap cw20
# print("swap cw20 - LUNA")
# execute_contract(
#     deployer,
#     normal_pair,
#     {
#         "swap": {
#             "offer_asset": {
#                 "info" : {"native_token": {"denom": "uluna"}},
#                 "amount": "1000000"
#             },
#         }
#     },
#     sequence+8,
#     "1000000uluna",
# )
#
# # # compare balances
# print(
#     "Trader swapped 1 LUNA for",
#     terra.wasm.contract_query(
#         normal_token, {"balance" : {"address" : deployer.key.acc_address}})["balance"],
#         "cw20 tokens",
# )
