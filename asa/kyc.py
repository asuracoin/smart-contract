from boa.interop.Neo.Runtime import CheckWitness
from boa.interop.Neo.Action import RegisterAction
from boa.interop.Neo.Storage import Get, Put, Delete
from boa.builtins import concat
from asa.token import TOKEN_OWNER
from asa.utils.txio import get_asset_attachments

OnKYCRegister = RegisterAction('kycRegister', 'address')
OnKycDeregister = RegisterAction('kycDeregister', 'address')

KYC_KEY = b'kyc_ok'
KYC_ADMIN_KEY = b'kyc_admin'

def kyc_register(ctx, args):
    """
    Register a list of addresses for KYC

    :param ctx:GetContext() used to access contract storage
    :param args:list a list of addresses to register.
        If called by KYC admin that is not token owner,
        first address must be address of KYC admin.

    :return:int The number of addresses registered for KYC
    """

    ok_count = 0

    canRegister = CheckWitness(TOKEN_OWNER)

    if not canRegister and get_kyc_admin_status(ctx, args[0]) and CheckWitness(args[0]):
        canRegister = True
        args.remove(0)

    if canRegister:
        for address in args:
            # validate the address is 20 bytes
            if len(address) == 20:
                Put(ctx, concat(KYC_KEY, address), True)
                OnKYCRegister(address)
                ok_count += 1

    return ok_count


def kyc_deregister(ctx, args):
    """
    Deregister a list of addresses from KYC

    :param ctx:GetContext() used to access contract storage
    :param args:list a list of addresses to deregister

    :return:int The number of addresses deregistered from KYC
    """

    ok_count = 0

    canRegister = CheckWitness(TOKEN_OWNER)

    if not canRegister and get_kyc_admin_status(ctx, args[0]) and CheckWitness(args[0]):
        canRegister = True
        args.remove(0)

    if canRegister:
        for address in args:
            if len(address) == 20:
                Delete(ctx, concat(KYC_KEY, address))
                OnKycDeregister(address)
                ok_count += 1

    return ok_count


def kyc_status(ctx, args):
    """
    Gets the KYC Status of an address

    :param ctx:GetContext() used to access contract storage
    :param args:list contains address to lookup

    :return:bool Returns the kyc status of an address
    """

    if len(args) > 0:
        return get_kyc_status(ctx, args[0])

    return False


def get_kyc_status(ctx, address):
    """
    Looks up the KYC status of an address

    :param ctx:GetContext() used to access contract storage
    :param address:bytearray The address to lookup

    :return:bool KYC Status of address
    """

    return Get(ctx, concat(KYC_KEY, address))


def kyc_register_admin(ctx, args):
    """
    Register a list of addresses for KYC admin

    :param ctx:GetContext() used to access contract storage
    :param args:list a list of addresses to register as kyc admins

    :return:int The number of addresses registered for KYC
    """

    ok_count = 0

    if CheckWitness(TOKEN_OWNER):
        for address in args:
            # validate the address is 20 bytes
            if len(address) == 20:
                Put(ctx, concat(KYC_ADMIN_KEY, address), True)
                ok_count += 1

    return ok_count


def kyc_deregister_admin(ctx, args):
    """
    Deregister a list of addresses from KYC admin

    :param ctx:GetContext() used to access contract storage
    :param args:list a list of addresses to deregister as kyc admins

    :return:int The number of addresses deregistered from KYC
    """

    ok_count = 0

    if CheckWitness(TOKEN_OWNER):

        for address in args:
            if len(address) == 20:
                Delete(ctx, concat(KYC_ADMIN_KEY, address))
                ok_count += 1

    return ok_count


def kyc_admin_status(ctx, args):
    """
    Gets the KYC Status of an address

    :param ctx:GetContext() used to access contract storage
    :param args:list contains address to lookup

    :return:bool Returns the kyc status of an address
    """

    if len(args) > 0:
        return get_kyc_admin_status(ctx, args[0])

    return False


def get_kyc_admin_status(ctx, address):
    """
    Looks up the KYC admin status of an address

    :param ctx:GetContext() used to access contract storage
    :param address:bytearray The address to lookup

    :return:bool KYC admin status of address
    """

    return Get(ctx, concat(KYC_ADMIN_KEY, address))
