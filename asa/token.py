from boa.interop.Neo.Storage import *

TOKEN_NAME = 'Asura World Coin'

TOKEN_SYMBOL = 'ASA'

TOKEN_DECIMALS = 8

# This is the script hash of the address for the owner of the token
# This can be found in ``neo-python`` with the walet open, use ``wallet`` command
TOKEN_OWNER = b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9'

TOKEN_CIRC_KEY = b'in_circulation'

TOKEN_TOTAL_SUPPLY = 1_000_000_000 * 100_000_000  # 1b total supply * 10^8 ( decimals)

TOKEN_INITIAL_AMOUNT = 250_000_000 * 100_000_000  # 250m to owners * 10^8

# for now assume 1 dollar per token, and one neo = 40 dollars * 10^8
TOKENS_PER_NEO = 500 * 100_000_000

# maximum amount you can mint in the limited round ( 500 neo/person * 40 Tokens/NEO * 10^8 )
MAX_EXCHANGE_LIMITED_ROUND = 500 * 500 * 100_000_000

# when to start the crowdsale
BLOCK_SALE_START = 10

# when to end the initial limited round
LIMITED_ROUND_END = 999_999_999_999

KYC_KEY = b'kyc_ok'

LIMITED_ROUND_KEY = b'r1'


def crowdsale_available_amount(ctx):

    in_circ = Get(ctx, TOKEN_CIRC_KEY)

    available = TOKEN_TOTAL_SUPPLY - in_circ

    return available


def add_to_circulation(ctx, amount):

    current_supply = Get(ctx, TOKEN_CIRC_KEY)

    current_supply += amount
    Put(ctx, TOKEN_CIRC_KEY, current_supply)
    return True


def get_circulation(ctx):
    return Get(ctx, TOKEN_CIRC_KEY)
