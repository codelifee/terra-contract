from dis import code_info
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd import LCDClient

terra = LCDClient("https://bombay-lcd.terra.dev", "bombay-12")

mk = MnemonicKey(mnemonic = "quality vacuum heart guard buzz spike sight swarm shove special gym robust assume sudden deposit grid alcohol choice devote leader tilt noodle tide penalty")

# admin
deployer = terra.wallet(mk)

# aurora token address & pair contract address
print(
    "Token pair's balance of astroport: ",
    terra.wasm.contract_query("terra10tundj5757wtjzvs3g4h48kcvvpw59s6jsyvet", {"balance": {"address": "terra1yknkheg3daqs3ugfppcsprsl09shxgju2rajw3"}})[
        "balance"
    ]
)
