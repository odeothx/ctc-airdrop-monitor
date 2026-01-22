"""
Spacecoin Airdrop Monitor Settings

이 파일에서 네트워크 설정, 컨트랙트 주소, 토큰 주소 등을 관리합니다.
"""

# =============================================================================
# Default Settings
# =============================================================================

DEFAULT_WALLETS_FILE = "wallets.json"
DEFAULT_NETWORK = "mainnet"

# =============================================================================
# Network RPC URLs
# =============================================================================

RPC_URLS = {
    "mainnet": "https://mainnet3.creditcoin.network",
    "testnet": "https://rpc.cc3-testnet.creditcoin.network",
}

# =============================================================================
# Blockscout API URLs
# =============================================================================

BLOCKSCOUT_API_URLS = {
    "mainnet": "https://creditcoin.blockscout.com/api/v2",
    "testnet": "https://creditcoin-testnet.blockscout.com/api/v2",
}

# =============================================================================
# RedeemableAirdrop Contract Addresses
# =============================================================================

# These contracts will always be monitored in addition to auto-discovered ones
MAINNET_CONTRACTS = [
    # "0xe272c3fb6d4ccf5A8bca94465f58b9c09f497Cd6",
    "0xC1f68532EE64AF333C43dfb7b4Ad93034F136e22",
    # "0x44D61789e4e6d2e06be032bD63fB2E86503B53A1",
]

# Discovered RedeemableAirdrop contracts (17 contracts as of 2026-01-13)
TESTNET_CONTRACTS = [
    "0xdb648e6ffdd53e56fbf600196ebc645d49dda9ad",
    "0x5a07fbd0ff67d23aa3972f1f7b4f5b4263787ba7",
    "0x4aea34dbee8574505ccf0620cfda96e7a2a1945e",
    "0x44adf468a466438dc59b0df67356d3f934cf149b",
    "0x36cb9f680ab4ff9face7d55c3256804fa2e64293",
    "0xa8661dd04177c7ec78144776807192766a9769e3",
    "0x61b9e1e10e9329c69e06f4c90de8968bfeaae19e",
    "0xc40aebef78d042c82f20b8dcd2ed181f49f613b3",
    "0xc86cb334115d2d701a3a8a022d173c87280eb14d",
    "0x3815a51e9b77fa0dc5acef59eaa952aa434b7c85",
    "0x3ded4500e09c250bc21260eac87fd867b1c7eacc",
    "0xc12ab1faeb1b3af2fc44f9c5692b90e0b3bc31a9",
    "0xcc99690276912f7d965972d01e642dcce5d2b660",
    "0x17dc105055db3b8b80980106de7c4dd3bab4f7f3",
    "0x824c6a8fb6311379bf8ba10e90c1843b16e3a4ce",
    "0x89c5dca027e96f594a15d22bd492ef22dcdc45a3",
    "0xfb49e04e12fa09bfda530da73822fcdc5011740d",
]
CONTRACT_ADDRESSES = {
    "mainnet": MAINNET_CONTRACTS[0],
    "testnet": TESTNET_CONTRACTS[0],
}

# =============================================================================
# Token Addresses
# =============================================================================

KNOWN_TOKENS = {
    "spacecoin_mainnet": "0x7ab7C6A935Ab2D1437398790C9C0660af62A80b9",
    "spacecoin_testnet": "0xfaFAd008f017C326B62FbfddA7fb2335A5c82247",
}

# =============================================================================
# Known Campaign Names (for legacy lookup and hash matching)
# =============================================================================

# 캠페인 이름 목록 (새 캠페인 해시 발견 시 이름 매칭에 사용)
KNOWN_CAMPAIGN_NAMES = [
    "SpaceCoin Airdrop",
    "SpaceCoin Airdrop 2024",
    "Spacecoin Airdrop",
    "Spacecoin",
    "spacecoin",
    "SPACECOIN",
    "SpaceCoin",
    "Airdrop",
    "Test",
]

# =============================================================================
# Campaign Hash to Name Mapping (수동 관리)
# =============================================================================

# 온체인에서 캠페인 이름을 얻을 수 없으므로, 알려진 캠페인은 여기에 매핑
# 형식: "campaign_hash": "campaign_name"
CAMPAIGN_HASH_TO_NAME = {
    # Mainnet campaigns
    "0x2cfc0ae0a0e97a34c4941dd0b5065df935ef8ef3c7b5ddad455c7858a3f7867b": "Mainnet Campaign #1",
    # Testnet campaigns (보상이 있는 캠페인)
    "0x2499af02d29716ec568358aac3c95698feff985f7e2a614ac6c2fddbd6e9a103": "Testnet SpaceCoin Airdrop",
}

# =============================================================================
# Contract ABI
# =============================================================================

REDEEMABLE_AIRDROP_ABI = [
    # rewardInfoByHash(bytes32 campaignNameHash, address wallet) -> (uint120, uint120, bool, bool)
    {
        "inputs": [
            {"internalType": "bytes32", "name": "campaignNameHash", "type": "bytes32"},
            {"internalType": "address", "name": "wallet", "type": "address"},
        ],
        "name": "rewardInfoByHash",
        "outputs": [
            {"internalType": "uint120", "name": "", "type": "uint120"},
            {"internalType": "uint120", "name": "", "type": "uint120"},
            {"internalType": "bool", "name": "", "type": "bool"},
            {"internalType": "bool", "name": "", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # allRewardInfo(address token, address wallet) -> (bytes32[], uint120[], uint120[], bool[], bool[])
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "address", "name": "wallet", "type": "address"},
        ],
        "name": "allRewardInfo",
        "outputs": [
            {"internalType": "bytes32[]", "name": "", "type": "bytes32[]"},
            {"internalType": "uint120[]", "name": "", "type": "uint120[]"},
            {"internalType": "uint120[]", "name": "", "type": "uint120[]"},
            {"internalType": "bool[]", "name": "", "type": "bool[]"},
            {"internalType": "bool[]", "name": "", "type": "bool[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # campaignInfoByHash(bytes32 campaignNameHash) -> (address, uint64, uint64, bool, uint256, uint256)
    {
        "inputs": [
            {"internalType": "bytes32", "name": "campaignNameHash", "type": "bytes32"},
        ],
        "name": "campaignInfoByHash",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "uint64", "name": "", "type": "uint64"},
            {"internalType": "uint64", "name": "", "type": "uint64"},
            {"internalType": "bool", "name": "", "type": "bool"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # campaignInfo(string campaignName) -> (address, uint64, uint64, bool, uint256, uint256)
    {
        "inputs": [
            {"internalType": "string", "name": "campaignName", "type": "string"},
        ],
        "name": "campaignInfo",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"},
            {"internalType": "uint64", "name": "", "type": "uint64"},
            {"internalType": "uint64", "name": "", "type": "uint64"},
            {"internalType": "bool", "name": "", "type": "bool"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
            {"internalType": "uint256", "name": "", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # tokenCampaigns(address token) -> bytes32[]
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
        ],
        "name": "tokenCampaigns",
        "outputs": [
            {"internalType": "bytes32[]", "name": "", "type": "bytes32[]"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # rewardInfo(string campaignName, address wallet) -> (uint120, uint120, bool, bool)
    {
        "inputs": [
            {"internalType": "string", "name": "campaignName", "type": "string"},
            {"internalType": "address", "name": "wallet", "type": "address"},
        ],
        "name": "rewardInfo",
        "outputs": [
            {"internalType": "uint120", "name": "", "type": "uint120"},
            {"internalType": "uint120", "name": "", "type": "uint120"},
            {"internalType": "bool", "name": "", "type": "bool"},
            {"internalType": "bool", "name": "", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    # Events
    # RewardsAdded(bytes32 indexed campaignNameHash, address indexed token, uint64 startDate, uint64 deadline)
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "campaignNameHash", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "token", "type": "address"},
            {"indexed": False, "internalType": "uint64", "name": "startDate", "type": "uint64"},
            {"indexed": False, "internalType": "uint64", "name": "deadline", "type": "uint64"},
        ],
        "name": "RewardsAdded",
        "type": "event",
    },
    # Claimed(address indexed user, bytes32 indexed campaignNameHash, uint120 totalReward, uint256 fee)
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": True, "internalType": "bytes32", "name": "campaignNameHash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint120", "name": "totalReward", "type": "uint120"},
            {"indexed": False, "internalType": "uint256", "name": "fee", "type": "uint256"},
        ],
        "name": "Claimed",
        "type": "event",
    },
]
