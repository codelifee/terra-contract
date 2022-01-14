from terra_sdk.client.localterra import LocalTerra
from terra_sdk.util.contract import read_file_as_b64, get_code_id, get_contract_address
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract
from terra_sdk.core.bank.msgs import MsgSend
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd import LCDClient

# terra = LocalTerra()
# deployer = terra.wallets["test2"]

terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")

mk = MnemonicKey(mnemonic = "nut mouse enlist brief spin empower coin brother actual unveil ticket diesel traffic quiz useless oil swing artefact tomato tennis topple betray banana gate")

mk2 = MnemonicKey(mnemonic = "trumpet vessel funny corn fetch science artefact spin range suspect always injury online nature magnet message replace strategy legal shock idle omit layer traffic")

deployer = terra.wallet(mk)
recipient = terra.wallet(mk2)

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

    # print(result)

    return result

def bank_execute_contract(
        sender, recipient, amount, sequence
):
    execuete = MsgSend(
        from_address= sender.key.acc_address,
        to_address= recipient.key.acc_address,
        amount= amount
    )

    print(sequence)

    tx = sender.create_and_sign_tx(
        msgs=[execuete], fee=StdFee(400000000, "10000000uluna")
    )

    print(tx)

    result = terra.tx.broadcast(tx)

    print(result)

    return result

sequence = terra.auth.account_info(deployer.key.acc_address).sequence

token_code_id = store_contract("astroport_lbp_token", sequence)
# sale_code_id = store_contract("sale", sequence+1)

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
    sequence+1
)

# transfer money (cw20)
result = execute_contract(
    deployer,
    boomco_token,
    {
        "transfer": {
            "amount": remove_decimal_point("1.000000"),
            "recipient": recipient.key.acc_address
        }
    },
    sequence+2
)

# send money (bank)
result = bank_execute_contract(
    recipient,
    deployer,
    "1000000uluna",
    sequence+3
)

