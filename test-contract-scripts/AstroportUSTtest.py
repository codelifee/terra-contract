from os import access
from re import S
from attr import Factory
from terra_sdk.client.lcd.api.tx import BroadcastOptions
from terra_sdk.client.lcd.api.bank import BankAPI

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
# deployer_mnemonic = "pink exist response monster hedgehog boss help tumble uniform flight alpha slogan news faith vital together hurdle divide orchard wine timber rail deal test"
# deployer_key = MnemonicKey(mnemonic = deployer_mnemonic)
# deployer = terra.wallet(deployer_key)

# 변수 초기화
global sequence
now_timestamp = int( time.mktime(datetime.today().timetuple() ) )
start_timestamp =  now_timestamp + (30) # 지금으로부터 30초 뒤
end_timestamp = now_timestamp + 24 * 60 * 60 + (30) # 지금으로부터 24시간 30초 뒤
sequence = terra.auth.account_info(deployer.key.acc_address).sequence

SHOW_TX_RESULT = False
IS_NEW_CONTRACTS = True

# IS_NEW_CONTRACTS 가 False일 때 아래 값을 사용
SAVED_FACTORY_CODE = str(16)
SAVED_TOKEN_CODE = str(17)
SAVED_PAIR_CODE = str(18)
SAVED_FACTORY_CONTRACT = "terra12538ynwk23jwx3yqueuvpsz3etu5ad794snvm2"
SAVED_TOKEN_CONTRACT = "terra150cq7rskhcxdvn9f3hqugfh0gwsk4mdzh6hv37"
SAVED_PAIR_CONTRACT = "terra165xlmr8edk5kvq8qq2pp08ltx6q6758lgh2fv6"


print(f"deployer: {deployer.key.acc_address}\nseq: {sequence}\
\nSHOW_TX_RESULT: {SHOW_TX_RESULT}\nIS_NEW_CONTRACTS: {IS_NEW_CONTRACTS}\n")

# Uploads contract, returns code ID
def store_contract(contract_name : str) -> str :
    global sequence

    contract_bytes = read_file_as_b64(f"artifacts/{contract_name}.wasm")
    storre_code = MsgStoreCode(
        deployer.key.acc_address,
        contract_bytes
    )
    tx = deployer.create_and_sign_tx(
        msgs=[storre_code], fee=StdFee(40000000, "10000000uluna"), sequence=sequence
    )
    sequence += 1

    result = terra.tx.broadcast(tx)
    if SHOW_TX_RESULT : print( "seq", sequence, " : ", result, '\n')

    return get_code_id(result)

# Instantiates a new contract with code_id and init_msg, returns address
def instanticate_contract(code_id: str, init_msg) -> str :
    global sequence
    
    instantiate = MsgInstantiateContract(
        admin=deployer.key.acc_address, sender=deployer.key.acc_address , code_id=code_id, init_msg=init_msg
    )

    tx = deployer.create_and_sign_tx(
        msgs=[instantiate], fee=StdFee(400000000, "10000000uluna"), sequence=sequence
    )
    sequence += 1

    result = terra.tx.broadcast(tx)
    if SHOW_TX_RESULT : print( "seq", sequence, " : ", result, '\n')

    return get_contract_address(result)

def execute_contract(sender: str, contract_addr : str, execute_msg, coins=None):
    global sequence

    execute = MsgExecuteContract(
        sender = sender.key.acc_address,
        contract = contract_addr,
        execute_msg = execute_msg,
        coins = coins
    )
    tx = deployer.create_and_sign_tx(
        msgs=[execute],  fee=StdFee(40000000, "10000000uluna"), sequence = sequence
    )
    sequence = sequence+1

    result = terra.tx.broadcast(tx)
    if SHOW_TX_RESULT : print( "seq", sequence, " : ", result, '\n')

    return result

def add_decimal_point(src:str, decimal = 6) -> str:
    tmp_int = int(src)
    return "%d.%d" % ( tmp_int/ (10**decimal) , tmp_int % (10**decimal) )

def remove_decimal_point(src:str) -> str:
    return src.replace(".","")

################## 계약서를 체인에 업로드 및 저장 
print("store 3 contracts")
factory_code_id = store_contract("astroport_lbp_factory") if IS_NEW_CONTRACTS else SAVED_FACTORY_CODE
token_code_id = store_contract("astroport_lbp_token") if IS_NEW_CONTRACTS else SAVED_TOKEN_CODE
pair_code_id = store_contract("astroport_lbp_pair") if IS_NEW_CONTRACTS else SAVED_PAIR_CODE
print(f"factory_code_id:{factory_code_id}\ntoken_code_id:{token_code_id}\npair_code_id:{pair_code_id}\n")

################## 체인에 저장된 계약서 실행
print("create ts factory")
factory = instanticate_contract(
    factory_code_id,
    {"token_code_id":int(token_code_id), "pair_code_id":int(pair_code_id), "owner":deployer.key.acc_address}
) if IS_NEW_CONTRACTS else SAVED_FACTORY_CONTRACT
print(f"factory contract is : {factory} \n")

print("create cw20 token")
token = instanticate_contract(
    token_code_id,
    {
        "name": "boomco_test_astroport",
        "symbol": "boomcoAstro",
        "decimals": 6,
        "initial_balances": [
            {
                "address": deployer.key.acc_address,
                "amount": remove_decimal_point("500000000.000000")
            }
        ],
         "mint" : { "minter" : deployer.key.acc_address}
    }
) if IS_NEW_CONTRACTS else SAVED_TOKEN_CONTRACT
print(f"token contract is : {token} ", '\n')

print("create cw20 - luna pair")
pair = execute_contract(
    deployer,
    factory,
    {
        "create_pair": {
            "asset_infos": [
                {
                    "info": {
                        "token": {
                            "contract_addr" : token
                        }
                    },
                    "start_weight":'50000',
                    "end_weight":'50000'
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
    }
).logs[0].events_by_type["from_contract"]["pair_contract_addr"][0] \
    if IS_NEW_CONTRACTS else SAVED_PAIR_CONTRACT
print(f"pair contract is : {pair} ", "\n")

total_share = terra.wasm.contract_query(pair, {"pool":{}})['total_share']
if int(total_share) == 0 :
    ####################### 유동성 풀 생성
    print("1. increase_allowance to 500000000.000000")
    execute_contract(
        deployer,
        token,
        {"increase_allowance":{"spender":pair, "amount" : remove_decimal_point("500000000.000000")}},
        None,
    )
    print("2. provide_liquidity")
    execute_contract(
        deployer,
        pair,
        {
            "provide_liquidity": {
                "assets": [
                    {
                        "info" : {"token": {"contract_addr": token}},
                        "amount": remove_decimal_point("500000000.000000")
                    },
                    {
                        "info" : {"native_token": {"denom": "uluna"}},
                        "amount": remove_decimal_point("10000.000000")
                    }
                ],
            }
        },
        remove_decimal_point("10000.000000")+"uluna"
    )
else:
    print("already paired\n")
    
pair_info = terra.wasm.contract_query(pair, {"pair":{}})
contract_start_time = pair_info['start_time']
contract_end_time = pair_info['end_time']

# print("mint 100.000000 tokens")
# cw20_balance = terra.wasm.contract_query(token, {"balance":{"address":deployer.key.acc_address}})['balance']
# print(f"cw20_balance before mint: { add_decimal_point(cw20_balance)}\n")
# execute_contract(
#     deployer,
#     token, 
#     {
#         "mint" : {
#             "recipient" : deployer.key.acc_address,
#             "amount" : remove_decimal_point("100.000000")
#         }
#     }
# )
# cw20_balance = terra.wasm.contract_query(token, {"balance":{"address":deployer.key.acc_address}})['balance']
# print(f"cw20_balance after mint: { add_decimal_point(cw20_balance)}\n")



# 거래 가능시간까지 대기
# while True:
#     if int( time.mktime(datetime.today().timetuple() ) ) > contract_start_time:
#         break
#     print("sleep for 10 seconds")
#     time.sleep(10)

# print("\nswap 10.000000LUNA to token")
# before_swap_balance = terra.wasm.contract_query(token, {"balance":{"address":deployer.key.acc_address}})['balance']
# swap_time = int( time.mktime(datetime.today().timetuple() ) )
# execute_contract(
#     deployer,
#     pair,
#     {
#         "swap": {
#             "offer_asset": {
#                 "info" : {"native_token": {"denom": "uluna"}},
#                 "amount": remove_decimal_point("10.000000")
#             },
#         }
#     },
#     remove_decimal_point("10.000000")+"uluna"
# )
# after_swap_balance = terra.wasm.contract_query(token, {"balance":{"address":deployer.key.acc_address}})['balance']

# print(f"swap time : {swap_time}")
# print(f"cw20_balance before swap : {add_decimal_point( before_swap_balance )}")
# print(f"cw20_balance after swap : {add_decimal_point( after_swap_balance )}")
# print(f"swaped token : {add_decimal_point( str(int(after_swap_balance)-int(before_swap_balance)) )}")
# print()

# 시뮬레이팅
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

    res = terra.wasm.contract_query(pair,queryMgs)
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