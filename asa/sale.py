from boa.interop.Neo.Blockchain import GetHeight
from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import Get, Put
from boa.builtins import concat
from asa.token import *
from asa.txio import get_asset_attachments

# OnTransfer = RegisterAction('transfer', 'addr_from', 'addr_to', 'amount')
# OnRefund = RegisterAction('refund', 'addr_to', 'amount')


PRESALE_LIMIT_ROUND_KEY = b'PRESALE'
PRESALE_START_TIMESTAMP = 1525824000     # GMT - May 9, 2018 12:00:00 AM
PRESALE_LIMIT_END_TIMESTAMP = 1525910400 # GMT - May 10, 2018 12:00:00 AM
PRESALE_END_TIMESTAMP = 1526860800       # GMT - May 21, 2018 12:00:00 AM
PRESALE_LIMIT_ROUND_NEO_MIN = 10 # NEO
PRESALE_LIMIT_ROUND_NEO_MAX = 50 # NEO
PRESALE_TOKENS_PER_NEO = 600 * 100_000_000 # 600 Tokens/NEO * 10^8 (500*1.2=600)


CROWDSALE_LIMIT_ROUND_KEY = b'CROWDSALE'
CROWDSALE_START_TIMESTAMP = 1528070400     # GMT - June 4, 2018 12:00:00 AM
CROWDSALE_LIMIT_END_TIMESTAMP = 1528156800 # GMT - June 5, 2018 12:00:00 AM
CROWDSALE_END_TIMESTAMP = 1529020800       # GMT - June 15, 2018 12:00:00 AM
CROWDSALE_LIMIT_ROUND_NEO_MIN = 10 # NEO
CROWDSALE_LIMIT_ROUND_NEO_MAX = 50 # NEO
CROWDSALE_TOKENS_PER_NEO = 500 * 100_000_000 # 600 Tokens/NEO * 10^8 (500*1.2=600)


def perform_exchange(ctx):

    attachments = get_asset_attachments()  # [receiver, sender, neo, gas]

    # this looks up whether the exchange can proceed
    exchange_ok = can_exchange(ctx, attachments, False)

    if not exchange_ok:
        # This should only happen in the case that there are a lot of TX on the final
        # block before the total amount is reached.  An amount of TX will get through
        # the verification phase because the total amount cannot be updated during that phase
        # because of this, there should be a process in place to manually refund tokens
        if attachments[2] > 0:
            OnRefund(attachments[1], attachments[2])
        # if you want to exchange gas instead of neo, use this
        # if attachments.gas_attached > 0:
        #    OnRefund(attachments.sender_addr, attachments.gas_attached)
        return False

    # lookup the current balance of the address
    current_balance = Get(ctx, attachments[1])

    # calculate the amount of tokens the attached neo will earn
    exchanged_tokens = attachments[2] * TOKENS_PER_NEO / 100000000

    # add it to the the exchanged tokens and persist in storage
    new_total = exchanged_tokens + current_balance
    Put(ctx, attachments[1], new_total)

    # update the in circulation amount
    result = add_to_circulation(ctx, exchanged_tokens)

    # dispatch transfer event
    # OnTransfer(attachments[0], attachments[1], exchanged_tokens)

    return True


def can_exchange(ctx, attachments, verify_only):

    # if you are accepting gas, use this
    if attachments[2] == 0:
       print("no neo attached")
       return False

    # the following looks up whether an address has been
    # registered with the contract for KYC regulations
    # this is not required for operation of the contract
    if not get_kyc_status(ctx, attachments[1]):
        return False

    # caluclate the amount requested
    amount_requested = attachments[2] * TOKENS_PER_NEO / 100000000

    return calculate_can_exchange(ctx, amount_requested, attachments[1], verify_only)


def calculate_can_exchange(ctx, amount, address, verify_only):

    height = GetHeight()

    current_in_circulation = Get(ctx, TOKEN_CIRC_KEY)

    new_amount = current_in_circulation + amount

    if new_amount > TOKEN_TOTAL_SUPPLY:
        return False

    # if we are in free round, any amount
    if height > LIMITED_ROUND_END:
        return True

    # check amount in limited round
    if amount <= MAX_EXCHANGE_LIMITED_ROUND:

        # check if they have already exchanged in the limited round
        r1key = concat(address, LIMITED_ROUND_KEY)
        amount_exchanged = Get(ctx, r1key)

        # updated to allow users to exchange as many times
        # as they want in the limit round up to their maximum
        new_exchanged_amount = amount + amount_exchanged

        # if not, then save the exchange for limited round
        if new_exchanged_amount <= MAX_EXCHANGE_LIMITED_ROUND:
            # note that this method can be invoked during the Verification trigger, so we have the
            # verify_only param to avoid the Storage.Put during the read-only Verification trigger.
            # this works around a "method Neo.Storage.Put not found in ->" error in InteropService.py
            # since Verification is read-only and thus uses a StateReader, not a StateMachine
            if not verify_only:
                Put(ctx, r1key, new_exchanged_amount)
            return True

        return False

    return False
