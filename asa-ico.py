from boa.interop.Neo.Runtime import GetTrigger, CheckWitness, Notify
from boa.interop.Neo.TriggerType import Application, Verification
from boa.interop.Neo.Storage import GetContext
from asa.utils.txio import get_asset_attachments
from asa.nep5 import NEP5_METHODS, handle_nep51
from asa.token import TOKEN_OWNER, deploy, get_circulation
from asa.kyc import kyc_register, kyc_unregister, kyc_status
from asa.sale import perform_exchange, crowdsale_available_amount

ctx = GetContext()

def Main(operation, args):

    trigger = GetTrigger()

    if trigger == Verification():

        if CheckWitness(TOKEN_OWNER):
            return True

        return calculate_exchange_amount(ctx, get_asset_attachments(), True) > 0

    elif trigger == Application():

        for op in NEP5_METHODS:
            if operation == op:
                return handle_nep51(ctx, operation, args)


        # TOKEN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        if operation == 'deploy':
            return deploy(ctx)

        elif operation == 'circulation':
            return get_circulation(ctx)

        elif operation == 'transfer_team_tokens':
            return transfer_team_tokens(ctx)


        # KYC ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        elif operation == 'crowdsale_register':
            return kyc_register(ctx, args)

        elif operation == 'crowdsale_unregister':
            return kyc_unregister(ctx, args)

        elif operation == 'crowdsale_status':
            return kyc_status(ctx, args)


        # CROWDSALE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        elif operation == 'mintTokens':
            return perform_exchange(ctx)

        elif operation == 'limitsale_available':
            return limitsale_available_amount(ctx)

        elif operation == 'crowdsale_available':
            return crowdsale_available_amount(ctx)

    return False
