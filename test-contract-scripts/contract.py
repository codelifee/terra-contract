from terra_sdk.client.localterra import LocalTerra
from terra_sdk.util.contract import read_file_as_b64
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode

lt = LocalTerra()
deployer = lt.wallets["test1"]

def store_contract(contract_name: str) -> str:
    contract_bytes = read_file_as_b64(f"artifacts/{contract_name}.wasm")
    store_code = MsgStoreCode(
        deployer.key.acc_address,
        contract_bytes
    )

    tx = deployer.create_and_sign_tx(
        msgs = [store_code], fee=StdFee(4000000, "10000000uluna")
    )

    result = lt.tx.broadcast(tx)
    print(result)

store_contract("test_contract_e")