from dis import code_info
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd import LCDClient

terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")

mk = MnemonicKey(mnemonic = "nut mouse enlist brief spin empower coin brother actual unveil ticket diesel traffic quiz useless oil swing artefact tomato tennis topple betray banana gate")

# admin
deployer = terra.wallet(mk)

# aurora token address & pair contract address
print(
    "Token pair's balance of aurora_token: ",
    terra.wasm.contract_query("terra1xpz9mlf04c0q3xy9fzgjvmdgwk5e8kageja3mu", {"balance": {"address": "terra1tua2wayppm7j76rm2zjk2wg4yy40zfa67cvrmf"}})[
        "balance"
    ]
)