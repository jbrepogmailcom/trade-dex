#!/usr/bin/env python3
import sys
import logging
from web3 import Web3

############################################################
# USER CONFIG
############################################################

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1) RPC setup
GNOSIS_RPC_URL = "https://rpc.gnosischain.com"
web3 = Web3(Web3.HTTPProvider(GNOSIS_RPC_URL))

if not web3.is_connected():
    raise Exception("Could not connect to Gnosis Chain RPC.")

# 2) Wallet details
#    You must define `wallet_address` and `private_key`
#    in `trust_wallet_codes.py`, or just paste them here.
from wallet_codes import wallet_address, private_key

# 3) SushiSwap Router & tokens
SUSHISWAP_ROUTER = Web3.to_checksum_address("0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506")

# Known tokens on Gnosis (add your own, like MPS)
TOKENS = {
    "USDC":  Web3.to_checksum_address("0xDDAfbb505ad214D7b80b1f830fcCc89B60fb7A83"),  # 6 decimals
    "WXDAI": Web3.to_checksum_address("0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d"),  # 18 decimals
    "WETH":  Web3.to_checksum_address("0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1"),   # 18 decimals
    "GNO":   Web3.to_checksum_address("0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"),  # 18 decimals
}

# 4) Decimals for each token (override as needed)
TOKEN_DECIMALS = {
    "USDC": 6,
    "WXDAI": 18,
    "WETH": 18,
    "GNO": 18,
}

# 5) Slippage
SLIPPAGE = 0.10  # 10%

############################################################
# ABIs
############################################################

ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount",  "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner",   "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
]

ROUTER_ABI = [
    # Exact SELL (token -> token)
    {
        "constant": False,
        "inputs": [
            {"name": "amountIn",      "type": "uint256"},
            {"name": "amountOutMin",  "type": "uint256"},
            {"name": "path",          "type": "address[]"},
            {"name": "to",            "type": "address"},
            {"name": "deadline",      "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function",
    },
    # Exact BUY (token -> token)
    {
        "constant": False,
        "inputs": [
            {"name": "amountOut",     "type": "uint256"},
            {"name": "amountInMax",   "type": "uint256"},
            {"name": "path",          "type": "address[]"},
            {"name": "to",            "type": "address"},
            {"name": "deadline",      "type": "uint256"},
        ],
        "name": "swapTokensForExactTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function",
    },
    # Exact SELL token -> xDAI
    {
        "constant": False,
        "inputs": [
            {"name": "amountIn",      "type": "uint256"},
            {"name": "amountOutMin",  "type": "uint256"},
            {"name": "path",          "type": "address[]"},
            {"name": "to",            "type": "address"},
            {"name": "deadline",      "type": "uint256"},
        ],
        "name": "swapExactTokensForETH",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function",
    },
    # Exact BUY xDAI (token -> xDAI)
    {
        "constant": False,
        "inputs": [
            {"name": "amountOut",     "type": "uint256"},
            {"name": "amountInMax",   "type": "uint256"},
            {"name": "path",          "type": "address[]"},
            {"name": "to",            "type": "address"},
            {"name": "deadline",      "type": "uint256"},
        ],
        "name": "swapTokensForExactETH",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function",
    },
    # Exact SELL xDAI -> token
    {
        "constant": False,
        "inputs": [
            {"name": "amountOutMin",  "type": "uint256"},
            {"name": "path",          "type": "address[]"},
            {"name": "to",            "type": "address"},
            {"name": "deadline",      "type": "uint256"},
        ],
        "name": "swapExactETHForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "payable": True,
        "type": "function",
    },
    # Exact BUY xDAI -> token
    {
        "constant": False,
        "inputs": [
            {"name": "amountOut",     "type": "uint256"},
            {"name": "path",          "type": "address[]"},
            {"name": "to",            "type": "address"},
            {"name": "deadline",      "type": "uint256"},
        ],
        "name": "swapETHForExactTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "payable": True,
        "type": "function",
    },
    # getAmountsOut, getAmountsIn
    {
        "constant": True,
        "inputs": [
            {"name": "amountIn",  "type": "uint256"},
            {"name": "path",      "type": "address[]"},
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "path",      "type": "address[]"},
        ],
        "name": "getAmountsIn",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "type": "function",
    },
]

############################################################
# Setup Router Contract
############################################################

router = web3.eth.contract(
    address=SUSHISWAP_ROUTER,
    abi=ROUTER_ABI
)

############################################################
# Helpers
############################################################

def get_token_contract(name):
    if name not in TOKENS:
        raise ValueError(f"Token {name} not recognized. Known: {list(TOKENS.keys())}")
    return web3.eth.contract(address=TOKENS[name], abi=ERC20_ABI)

def decimals_for(name):
    """Return how many decimal places for the given token name."""
    if name == "XDAI":
        # native xDAI => 18 decimals conceptually
        return 18
    if name in TOKEN_DECIMALS:
        return TOKEN_DECIMALS[name]
    return 18  # fallback

def human_to_raw(token_name, amount_float):
    """Convert a float amount into its raw integer representation."""
    dec = decimals_for(token_name)
    return int(amount_float * 10**dec)

def raw_to_human(token_name, amount_int):
    """Convert a raw integer on-chain amount into a float for logging."""
    dec = decimals_for(token_name)
    return float(amount_int) / 10**dec

def check_approval_if_needed(token_name, needed_amount):
    """Checks allowance for SELL token_name, approves if insufficient."""
    if token_name == "XDAI":
        # No approval for native xDAI
        return

    token_contract = get_token_contract(token_name)
    current_allowance = token_contract.functions.allowance(wallet_address, SUSHISWAP_ROUTER).call()

    if current_allowance < needed_amount:
        logger.info(f"Current allowance {raw_to_human(token_name, current_allowance)} {token_name} < needed {raw_to_human(token_name, needed_amount)}. Approving...")
        nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
        tx = token_contract.functions.approve(SUSHISWAP_ROUTER, needed_amount).build_transaction({
            "from": wallet_address,
            "gas": 200000,
            "gasPrice": web3.to_wei("1", "gwei"),
            "nonce": nonce,
        })
        signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise RuntimeError("Approval failed or reverted.")
        logger.info(f"Approved. Tx: {tx_hash.hex()}")

############################################################
# Trade Functions
############################################################

def exact_sell(sell_amount_raw, sell_token, buy_token, last_purchase_price=None):
    """
    Sell EXACTLY sell_amount_raw of 'sell_token'.
    Before executing, if last_purchase_price is provided then the estimated
    xDAI value of the trade is compared to last_purchase_price*1.0025.
    If the estimate is too low, the sale is skipped.
    """
    # Case 1: selling native xDAI
    if sell_token == "XDAI":
        bal = web3.eth.get_balance(wallet_address)
        logger.info(f"xDAI balance: {raw_to_human('XDAI', bal)}; need {raw_to_human('XDAI', sell_amount_raw)}")
        if bal < sell_amount_raw:
            raise ValueError("Insufficient xDAI.")
        if buy_token == "XDAI":
            raise ValueError("Can't swap xDAI->xDAI. Same token.")
        path = [TOKENS["WXDAI"], TOKENS[buy_token]]
        amounts_out = router.functions.getAmountsOut(sell_amount_raw, path).call()
        out_est = amounts_out[-1]
        # Convert the estimated output into xDAI (via buy_token conversion)
        if last_purchase_price is not None:
            conversion = router.functions.getAmountsOut(out_est, [TOKENS[buy_token], TOKENS["WXDAI"]]).call()
            x_estimate = raw_to_human("XDAI", conversion[-1])
            threshold = last_purchase_price * 1.0025
            if x_estimate < threshold:
                logger.info(f"Skipping sale: estimated xDAI value {x_estimate} is below threshold {threshold}")
                return
        logger.info(f"Exact SELL xDAI => {buy_token} estimate: ~{raw_to_human(buy_token, out_est)}")
        nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
        deadline = web3.eth.get_block("latest")["timestamp"] + 600
        tx = router.functions.swapExactETHForTokens(
            int(out_est * (1 - SLIPPAGE)),
            path,
            wallet_address,
            deadline
        ).build_transaction({
            "from": wallet_address,
            "value": sell_amount_raw,
            "gas": 300000,
            "gasPrice": web3.to_wei("1", "gwei"),
            "nonce": nonce,
        })
        signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"Swap TX: {tx_hash.hex()}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            logger.info("Swap success!")
        else:
            logger.error("Swap failed or reverted.")
        return
    else:
        # SELL token is ERC20; check balance and approval
        contract = get_token_contract(sell_token)
        bal = contract.functions.balanceOf(wallet_address).call()
        if bal < sell_amount_raw:
            raise ValueError(f"Insufficient {sell_token} balance.")
        check_approval_if_needed(sell_token, sell_amount_raw)
        # Case 2a: Buying native xDAI
        if buy_token == "XDAI":
            path = [TOKENS[sell_token], TOKENS["WXDAI"]]
            amounts_out = router.functions.getAmountsOut(sell_amount_raw, path).call()
            out_est = amounts_out[-1]
            if last_purchase_price is not None:
                x_estimate = raw_to_human("XDAI", out_est)
                threshold = last_purchase_price * 1.0025
                if x_estimate < threshold:
                    logger.info(f"Skipping sale: estimated xDAI value {x_estimate} is below threshold {threshold}")
                    return
            logger.info(f"Exact SELL {sell_token} => xDAI estimate: ~{raw_to_human('WXDAI', out_est)}")
            nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
            deadline = web3.eth.get_block("latest")["timestamp"] + 600
            tx = router.functions.swapExactTokensForETH(
                sell_amount_raw,
                int(out_est * (1 - SLIPPAGE)),
                path,
                wallet_address,
                deadline
            ).build_transaction({
                "from": wallet_address,
                "gas": 300000,
                "gasPrice": web3.to_wei("1", "gwei"),
                "nonce": nonce,
            })
            signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            logger.info(f"Swap TX: {tx_hash.hex()}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.info("Swap success!")
            else:
                logger.error("Swap failed or reverted.")
        else:
            # Case 2b: Token -> token swap
            if buy_token not in TOKENS:
                raise ValueError(f"Unknown buy token {buy_token}.")
            path = [TOKENS[sell_token], TOKENS[buy_token]]
            amounts_out = router.functions.getAmountsOut(sell_amount_raw, path).call()
            out_est = amounts_out[-1]
            if last_purchase_price is not None:
                conversion = router.functions.getAmountsOut(out_est, [TOKENS[buy_token], TOKENS["WXDAI"]]).call()
                x_estimate = raw_to_human("XDAI", conversion[-1])
                threshold = last_purchase_price * 1.0025
                if x_estimate < threshold:
                    logger.info(f"Skipping sale: estimated xDAI value {x_estimate} is below threshold {threshold}")
                    return
            logger.info(f"Exact SELL {sell_token} => {buy_token} estimate: ~{raw_to_human(buy_token, out_est)}")
            nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
            deadline = web3.eth.get_block("latest")["timestamp"] + 600
            tx = router.functions.swapExactTokensForTokens(
                sell_amount_raw,
                int(out_est * (1 - SLIPPAGE)),
                path,
                wallet_address,
                deadline
            ).build_transaction({
                "from": wallet_address,
                "gas": 300000,
                "gasPrice": web3.to_wei("1", "gwei"),
                "nonce": nonce,
            })
            signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            logger.info(f"Swap TX: {tx_hash.hex()}")
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.info("Swap success!")
            else:
                logger.error("Swap failed or reverted.")

def exact_buy(buy_amount_raw, sell_token, buy_token, last_purchase_price=None):
    """
    Buy EXACTLY buy_amount_raw of 'buy_token'.
    Before executing, if last_purchase_price is provided then the estimated
    xDAI cost of the trade is compared to last_purchase_price/1.0025.
    If the cost is too high, the purchase is skipped.
    """
    # Case A: Buying xDAI (i.e. token->xDAI swap)
    if buy_token == "XDAI":
        if sell_token == "XDAI":
            raise ValueError("Exact buy xDAI with xDAI is meaningless (same token).")
        path = [TOKENS[sell_token], TOKENS["WXDAI"]]
        needed = router.functions.getAmountsIn(buy_amount_raw, path).call()
        sell_required = needed[0]
        if last_purchase_price is not None:
            conversion = router.functions.getAmountsOut(sell_required, [TOKENS[sell_token], TOKENS["WXDAI"]]).call()
            x_cost = raw_to_human("XDAI", conversion[-1])
            threshold = last_purchase_price / 1.0025
            if x_cost > threshold:
                logger.info(f"Skipping purchase: estimated xDAI cost {x_cost} is above threshold {threshold}")
                return
        amount_in_max = int(sell_required * (1 + SLIPPAGE))
        logger.info(f"Exact BUY {raw_to_human('WXDAI', buy_amount_raw)} xDAI => need ~{raw_to_human(sell_token, sell_required)} {sell_token}; +slippage => {raw_to_human(sell_token, amount_in_max)} max.")
        # Check balance and approve
        contract = get_token_contract(sell_token)
        balance = contract.functions.balanceOf(wallet_address).call()
        if balance < amount_in_max:
            raise ValueError("Not enough SELL tokens to cover 'amountInMax'.")
        check_approval_if_needed(sell_token, amount_in_max)
        nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
        deadline = web3.eth.get_block("latest")["timestamp"] + 600
        tx = router.functions.swapTokensForExactETH(
            buy_amount_raw,
            amount_in_max,
            path,
            wallet_address,
            deadline
        ).build_transaction({
            "from": wallet_address,
            "gas": 300000,
            "gasPrice": web3.to_wei("1", "gwei"),
            "nonce": nonce,
        })
        signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"Swap TX: {tx_hash.hex()}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            logger.info("Swap success!")
        else:
            logger.error("Swap failed or reverted.")
        return

    # Case B: Buying with xDAI (xDAI -> token)
    if sell_token == "XDAI":
        path = [TOKENS["WXDAI"], TOKENS[buy_token]]
        needed = router.functions.getAmountsIn(buy_amount_raw, path).call()
        xdaineeded = needed[0]
        if last_purchase_price is not None:
            x_cost = raw_to_human("XDAI", xdaineeded)
            threshold = last_purchase_price / 1.0025
            if x_cost > threshold:
                logger.info(f"Skipping purchase: estimated xDAI cost {x_cost} is above threshold {threshold}")
                return
        xdaineeded_max = int(xdaineeded * (1 + SLIPPAGE))
        logger.info(f"Exact BUY {raw_to_human(buy_token, buy_amount_raw)} {buy_token} => need ~{raw_to_human('XDAI', xdaineeded)} xDAI, max {raw_to_human('XDAI', xdaineeded_max)}.")
        bal = web3.eth.get_balance(wallet_address)
        if bal < xdaineeded_max:
            raise ValueError("Not enough xDAI to cover 'amountInMax'.")
        nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
        deadline = web3.eth.get_block("latest")["timestamp"] + 600
        tx = router.functions.swapETHForExactTokens(
            buy_amount_raw,
            path,
            wallet_address,
            deadline
        ).build_transaction({
            "from": wallet_address,
            "value": xdaineeded_max,
            "gas": 300000,
            "gasPrice": web3.to_wei("1", "gwei"),
            "nonce": nonce,
        })
        signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(f"Swap TX: {tx_hash.hex()}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            logger.info("Swap success!")
        else:
            logger.error("Swap failed or reverted.")
        return

    # Case C: Token -> token swap (neither token is xDAI)
    path = [TOKENS[sell_token], TOKENS[buy_token]]
    needed = router.functions.getAmountsIn(buy_amount_raw, path).call()
    sell_required = needed[0]
    if last_purchase_price is not None:
        conversion = router.functions.getAmountsOut(sell_required, [TOKENS[sell_token], TOKENS["WXDAI"]]).call()
        x_cost = raw_to_human("XDAI", conversion[-1])
        threshold = last_purchase_price / 1.0025
        if x_cost > threshold:
            logger.info(f"Skipping purchase: estimated xDAI cost {x_cost} is above threshold {threshold}")
            return
    amount_in_max = int(sell_required * (1 + SLIPPAGE))
    logger.info(f"Exact BUY {raw_to_human(buy_token, buy_amount_raw)} {buy_token}, need ~{raw_to_human(sell_token, sell_required)} {sell_token}, +slippage => max {raw_to_human(sell_token, amount_in_max)}.")
    contract = get_token_contract(sell_token)
    balance = contract.functions.balanceOf(wallet_address).call()
    if balance < amount_in_max:
        raise ValueError("Not enough SELL tokens to cover 'amountInMax'.")
    check_approval_if_needed(sell_token, amount_in_max)
    nonce = web3.eth.get_transaction_count(wallet_address, 'pending')
    deadline = web3.eth.get_block("latest")["timestamp"] + 600
    tx = router.functions.swapTokensForExactTokens(
        buy_amount_raw,
        amount_in_max,
        path,
        wallet_address,
        deadline
    ).build_transaction({
        "from": wallet_address,
        "gas": 300000,
        "gasPrice": web3.to_wei("1", "gwei"),
        "nonce": nonce,
    })
    signed = web3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    logger.info(f"Swap TX: {tx_hash.hex()}")
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        logger.info("Swap success!")
    else:
        logger.error("Swap failed or reverted.")

############################################################
# Main CLI
############################################################

def main():
    """
    Usage:
        python3 trade.py <SELL_AMOUNT_OR_?> <SELL_TOKEN> <BUY_AMOUNT_OR_?> <BUY_TOKEN> [last_purchase_price]

    Examples:
        # EXACT SELL: "I want to sell exactly 12 USDC"
        #   python3 trade.py 12 USDC ? MPS 0.98
        #   => If the estimated xDAI value is below 0.98*1.0025, the sale is skipped.
    
        # EXACT BUY: "I want to buy exactly 1 MPS"
        #   python3 trade.py ? USDC 1 MPS 1.05
        #   => If the estimated xDAI cost is above 1.05/1.0025, the purchase is skipped.
    """
    if len(sys.argv) not in [5, 6]:
        print("Usage: python3 trade.py <sell_amount_or_?> <sell_token> <buy_amount_or_?> <buy_token> [last_purchase_price]")
        print("Example exact-sell: python3 trade.py 12 USDC ? MPS 0.98")
        print("Example exact-buy:  python3 trade.py ? USDC 1 GNO 1.05")
        sys.exit(1)

    sell_amount_str = sys.argv[1]
    sell_token      = sys.argv[2].upper()
    buy_amount_str  = sys.argv[3]
    buy_token       = sys.argv[4].upper()
    last_purchase_price = float(sys.argv[5]) if len(sys.argv) == 6 else None

    if sell_amount_str == '?' and buy_amount_str == '?':
        raise ValueError("Cannot have both SELL and BUY amounts unknown ('?').")
    if sell_amount_str != '?' and buy_amount_str != '?':
        raise ValueError("Cannot have both SELL and BUY amounts specified. One must be '?'.")

    if sell_amount_str != '?':
        sell_amount_float = float(sell_amount_str)
        sell_amount_raw = human_to_raw(sell_token, sell_amount_float)
        exact_sell(sell_amount_raw, sell_token, buy_token, last_purchase_price)
    else:
        buy_amount_float = float(buy_amount_str)
        buy_amount_raw = human_to_raw(buy_token, buy_amount_float)
        exact_buy(buy_amount_raw, sell_token, buy_token, last_purchase_price)

if __name__ == "__main__":
    main()
