from terra_sdk.client.localterra import LocalTerra
from terra_sdk.util.contract import read_file_as_b64, get_code_id
from terra_sdk.core.auth import StdFee
from terra_sdk.core.wasm import MsgStoreCode

from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd import LCDClient

terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")

mk = MnemonicKey(mnemonic = "nut mouse enlist brief spin empower coin brother actual unveil ticket diesel traffic quiz useless oil swing artefact tomato tennis topple betray banana gate")

# deployer = lt.wallets["test1"]
deployer = terra.wallet(mk)

def store_contract(contract_name: str) -> str:
    contract_bytes = read_file_as_b64(f"artifacts/{contract_name}.wasm")
    store_code = MsgStoreCode(
        deployer.key.acc_address,
        contract_bytes
    )

    tx = deployer.create_and_sign_tx(
        msgs = [store_code], fee=StdFee(4000000, "10000000uluna")
    )

    result = terra.tx.broadcast(tx)
    code_id = get_code_id(result)
    return code_id

print(store_contract("cw20_base"))