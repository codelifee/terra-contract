from datetime import datetime

from terra_sdk.client.localterra import LCDClient, LocalTerra
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgExecuteContract

terra = LocalTerra()
deployer = terra.wallets["test1"]

def remove_decimal_point(src:str) -> str:
    return src.replace(".","")

def add_decimal_point(src:str, decimal = 6) -> str:
    tmp_int = int(src)
    return "%d.%d" % ( tmp_int/ (10**decimal) , tmp_int % (10**decimal) )

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

normal_pair = "terra17w33zet2jmze0hsjg7vufhx64jelcalzudzn7r"
normal_token = "terra1etj3lxvz899ryu5y9rtj0hxtftpcjmpxf4rulh"

print("swap cw20 - LUNA")
execute_contract(
    deployer,
    normal_pair,
    {
        "swap": {
            "offer_asset": {
                "info" : {"native_token": {"denom": "uluna"}},
                "amount": "1000000"
            },
        }
    },
    sequence,
    "1000000uluna",
    )



# compare balances
print(
    "Trader swapped 1 LUNA for",
    terra.wasm.contract_query(
        normal_token, {"balance" : {"address" : deployer.key.acc_address}})["balance"],
    "cw20 tokens",
)

contract_start_time = 1641980088
contract_end_time = 1641983688

print("simulation")
print(f"contract_start_time: {datetime.fromtimestamp(contract_start_time)}")
print(f"contract_end_time: {datetime.fromtimestamp(contract_end_time)}")
print("blockTime,return_amount,spread_amount,commission_amount,total_amount,ask_weight,offer_weight")
for i in range( int( (contract_end_time - contract_start_time ) / 600 )+1 ):
    block_time = contract_start_time + 600 * i

    if block_time == contract_end_time:
        block_time -= 1

    queryMgs = {
        "simulation":{
            "offer_asset":{
                "info" : {"native_token": {"denom": "uluna"}},
                "amount":remove_decimal_point("1.000000")
            },
            "block_time" : block_time
        }
    }

    res = terra.wasm.contract_query(normal_pair,queryMgs)
    return_amount = int(res['return_amount'])
    spread_amount = int(res['spread_amount'])
    commission_amount = int(res['commission_amount'])
    total_amount = return_amount + spread_amount + commission_amount
    print("%s\t%s\t%s\t%s\t%s\t%.3f\t%.3f" %(
        datetime.fromtimestamp(block_time),
        add_decimal_point(return_amount),
        add_decimal_point(spread_amount),
        add_decimal_point(commission_amount),
        add_decimal_point(total_amount),
        float(res['ask_weight']),float(res['offer_weight'])) )