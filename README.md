# trade-dex
Python script to trade on DEX. This one is tailored to use sushiswap API to trade on gnosis chain

You need to put encrypted versions of your wallet private key and wallet address to file trust_wallet_codes.py. Encrypt with encrypt-string.py

Examples:

exchange 1 GNO for unknown amount of USDC:

```
python3 trade-dex.py 1 GNO "?" USDC
```

exchange 1 GNO for unknown amount of USDC:

```
python3 trade-dex.py 1 GNO "?" USDC
```

You can also add parameter how many times the trade should repeat. If there are pools with low liquidity and buying or selling large amount would disbalance the pool too much, You can buy/sell repeatedly in smaller chunks

```
python3 trade-dex.py "?" USDC 10 GNO --repeat_times=5
```

You can also add third another parameter that will check if price is above or below certain rate and if it is, the trade is skipped. The script takes into account fee on sushiswap which is 0.25%
