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

    print(result)

    code_id = get_code_id(result)

    return code_id


sequence = terra.auth.account_info(deployer.key.acc_address).sequence

token_code_id = store_contract("cosmwasm_16", sequence)

