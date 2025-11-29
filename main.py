"""
Spacecoin Airdrop Monitor for Creditcoin Chain

지갑 주소별 에어드랍 수량 조회 프로그램

Usage:
    python main.py                              # testnet, wallets.json 사용
    python main.py --network mainnet            # mainnet
    python main.py --wallets my_wallets.json    # 지갑 파일 지정
    python main.py --address 0x1234...          # 단일 주소 조회
    python main.py --address 0x1234... --name "my_wallet"  # 단일 주소 + 이름
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import httpx
from web3 import Web3

from settings import (
    BLOCKSCOUT_API_URLS,
    CAMPAIGN_HASH_TO_NAME,
    CONTRACT_ADDRESSES,
    DEFAULT_WALLETS_FILE,
    KNOWN_CAMPAIGN_NAMES,
    KNOWN_TOKENS,
    MAINNET_CONTRACTS,
    REDEEMABLE_AIRDROP_ABI,
    RPC_URLS,
    TESTNET_CONTRACTS,
)

# =============================================================================
# Wallet Loading Functions
# =============================================================================


def load_wallets_from_file(file_path: str) -> dict[str, str]:
    """JSON 파일에서 지갑 정보 로드"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Wallet file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        wallets = json.load(f)

    if not isinstance(wallets, dict):
        raise ValueError(f"Invalid wallet file format. Expected dict, got {type(wallets)}")

    return wallets


def get_wallets(args) -> dict[str, str]:
    """CLI 인자에서 지갑 정보 결정"""
    # 1. 단일 주소가 지정된 경우
    if args.address:
        name = args.name if args.name else args.address[:10] + "..."
        return {name: args.address}

    # 2. 지갑 파일이 지정된 경우
    wallet_file = args.wallets if args.wallets else DEFAULT_WALLETS_FILE

    # 파일이 존재하면 로드
    if Path(wallet_file).exists():
        return load_wallets_from_file(wallet_file)

    # 기본 파일도 없으면 에러
    raise FileNotFoundError(
        f"Wallet file not found: {wallet_file}\n"
        f"Create a wallets.json file or use --address to specify a single address."
    )


# =============================================================================
# Data Types
# =============================================================================


class RewardInfo(NamedTuple):
    """개별 리워드 정보"""

    total_reward: int  # 총 리워드 (wei)
    bonus_reward: int  # 보너스 리워드 (wei)
    claimed: bool  # 수령 완료 여부
    required_additional_verification: bool  # 추가 인증 필요 여부


class CampaignInfo(NamedTuple):
    """캠페인 정보"""

    token: str  # 토큰 주소
    start_date: int  # 시작 시간 (unix timestamp)
    deadline: int  # 마감 시간 (unix timestamp)
    reclaimed: bool  # 회수 완료 여부
    total_amount: int  # 총 수량 (wei)
    total_claimed: int  # 수령 완료 수량 (wei)


class WalletReward(NamedTuple):
    """지갑별 리워드 정보"""

    wallet_name: str
    wallet_address: str
    campaign_hash: str
    total_reward: int
    bonus_reward: int
    claimed: bool
    required_additional_verification: bool


# =============================================================================
# AirdropMonitor Class
# =============================================================================


class AirdropMonitor:
    """Spacecoin 에어드랍 모니터"""

    def __init__(self, network: str = "testnet"):
        """
        Args:
            network: 'mainnet', 'mainnet_remote', 또는 'testnet'
        """
        if network not in RPC_URLS:
            raise ValueError(f"Unknown network: {network}. Use: {list(RPC_URLS.keys())}")

        self.network = network
        self.rpc_url = RPC_URLS[network]
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        # 네트워크별 컨트랙트 주소 목록
        if network in ("mainnet", "mainnet_remote"):
            self.contract_addresses = [
                Web3.to_checksum_address(addr) for addr in MAINNET_CONTRACTS
            ]
        else:
            self.contract_addresses = [
                Web3.to_checksum_address(CONTRACT_ADDRESSES.get(network, CONTRACT_ADDRESSES["testnet"]))
            ]

        # 기본 컨트랙트 (첫 번째)
        self.contract_address = self.contract_addresses[0]
        self.contract = self.w3.eth.contract(
            address=self.contract_address, abi=REDEEMABLE_AIRDROP_ABI
        )

        # 모든 컨트랙트 인스턴스
        self.contracts = [
            self.w3.eth.contract(address=addr, abi=REDEEMABLE_AIRDROP_ABI)
            for addr in self.contract_addresses
        ]

        # Blockscout API URL
        self.blockscout_api_url = BLOCKSCOUT_API_URLS.get(network, BLOCKSCOUT_API_URLS["testnet"])

    def is_connected(self) -> bool:
        """RPC 연결 확인"""
        return self.w3.is_connected()

    # =========================================================================
    # Blockscout API Methods
    # =========================================================================

    def fetch_logs_from_blockscout(self, contract_address: str) -> list[dict]:
        """Blockscout API를 통해 컨트랙트의 이벤트 로그 조회"""
        logs = []
        next_page_params = None

        try:
            with httpx.Client(timeout=30.0) as client:
                while True:
                    url = f"{self.blockscout_api_url}/addresses/{contract_address}/logs"
                    params = next_page_params if next_page_params else {}

                    response = client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()

                    items = data.get("items", [])
                    logs.extend(items)

                    # 페이지네이션 처리
                    next_page_params = data.get("next_page_params")
                    if not next_page_params:
                        break

            return logs
        except Exception as e:
            print(f"Error fetching logs from Blockscout for {contract_address}: {e}")
            return []

    def discover_campaigns_from_blockscout(self) -> list[dict]:
        """Blockscout API를 통해 모든 컨트랙트에서 캠페인 발견"""
        all_campaigns = []

        for contract_addr in self.contract_addresses:
            print(f"  Fetching logs from Blockscout for {contract_addr}...")
            logs = self.fetch_logs_from_blockscout(contract_addr)

            for log in logs:
                decoded = log.get("decoded")
                if not decoded:
                    continue

                method_call = decoded.get("method_call", "")

                # RewardsAdded 이벤트 처리
                if "RewardsAdded" in method_call:
                    params = {p["name"]: p["value"] for p in decoded.get("parameters", [])}
                    campaign_hash = params.get("campaignNameHash", "")
                    token = params.get("token", "")
                    start_date = int(params.get("startDate", 0))
                    deadline = int(params.get("deadline", 0))

                    all_campaigns.append({
                        "contract_address": contract_addr,
                        "campaign_hash": campaign_hash,
                        "token": token,
                        "start_date": start_date,
                        "deadline": deadline,
                        "block_number": log.get("block_number", 0),
                        "tx_hash": log.get("transaction_hash", ""),
                    })

        # 중복 제거 (campaign_hash + contract_address 기준)
        seen = set()
        unique_campaigns = []
        for c in all_campaigns:
            key = (c["contract_address"], c["campaign_hash"])
            if key not in seen:
                seen.add(key)
                unique_campaigns.append(c)

        return unique_campaigns

    def get_claimed_events_from_blockscout(self, wallet_address: str | None = None) -> list[dict]:
        """Blockscout API를 통해 Claimed 이벤트 조회"""
        all_claims = []
        wallet_lower = wallet_address.lower() if wallet_address else None

        for contract_addr in self.contract_addresses:
            logs = self.fetch_logs_from_blockscout(contract_addr)

            for log in logs:
                decoded = log.get("decoded")
                if not decoded:
                    continue

                method_call = decoded.get("method_call", "")

                if "Claimed" in method_call:
                    params = {p["name"]: p["value"] for p in decoded.get("parameters", [])}
                    user = params.get("user", "")

                    # 특정 지갑 필터링
                    if wallet_lower and user.lower() != wallet_lower:
                        continue

                    all_claims.append({
                        "contract_address": contract_addr,
                        "user": user,
                        "campaign_hash": params.get("campaignNameHash", ""),
                        "total_reward": int(params.get("totalReward", 0)),
                        "fee": int(params.get("fee", 0)),
                        "block_number": log.get("block_number", 0),
                        "tx_hash": log.get("transaction_hash", ""),
                    })

        return all_claims

    def get_campaign_name_hash(self, campaign_name: str) -> bytes:
        """캠페인 이름의 keccak256 해시 생성"""
        return Web3.keccak(text=campaign_name)

    def get_reward_info_by_hash(
        self, campaign_hash: bytes, wallet_address: str
    ) -> RewardInfo:
        """특정 캠페인에서 지갑의 리워드 정보 조회"""
        wallet = Web3.to_checksum_address(wallet_address)
        result = self.contract.functions.rewardInfoByHash(campaign_hash, wallet).call()
        return RewardInfo(
            total_reward=result[0],
            bonus_reward=result[1],
            claimed=result[2],
            required_additional_verification=result[3],
        )

    def get_reward_info(self, campaign_name: str, wallet_address: str) -> RewardInfo:
        """캠페인 이름으로 지갑의 리워드 정보 조회"""
        wallet = Web3.to_checksum_address(wallet_address)
        result = self.contract.functions.rewardInfo(campaign_name, wallet).call()
        return RewardInfo(
            total_reward=result[0],
            bonus_reward=result[1],
            claimed=result[2],
            required_additional_verification=result[3],
        )

    def get_campaign_info_by_hash(self, campaign_hash: bytes) -> CampaignInfo:
        """캠페인 해시로 캠페인 정보 조회"""
        result = self.contract.functions.campaignInfoByHash(campaign_hash).call()
        return CampaignInfo(
            token=result[0],
            start_date=result[1],
            deadline=result[2],
            reclaimed=result[3],
            total_amount=result[4],
            total_claimed=result[5],
        )

    def get_campaign_info(self, campaign_name: str) -> CampaignInfo:
        """캠페인 이름으로 캠페인 정보 조회"""
        result = self.contract.functions.campaignInfo(campaign_name).call()
        return CampaignInfo(
            token=result[0],
            start_date=result[1],
            deadline=result[2],
            reclaimed=result[3],
            total_amount=result[4],
            total_claimed=result[5],
        )

    def get_token_campaigns(self, token_address: str) -> list[bytes]:
        """특정 토큰의 모든 캠페인 해시 목록 조회"""
        token = Web3.to_checksum_address(token_address)
        return self.contract.functions.tokenCampaigns(token).call()

    def get_all_reward_info(
        self, token_address: str, wallet_address: str
    ) -> list[tuple[bytes, RewardInfo]]:
        """특정 토큰의 모든 캠페인에서 지갑의 리워드 정보 조회"""
        token = Web3.to_checksum_address(token_address)
        wallet = Web3.to_checksum_address(wallet_address)
        result = self.contract.functions.allRewardInfo(token, wallet).call()

        campaign_hashes = result[0]
        total_rewards = result[1]
        bonus_rewards = result[2]
        claimed_list = result[3]
        verification_list = result[4]

        rewards = []
        for i in range(len(campaign_hashes)):
            reward_info = RewardInfo(
                total_reward=total_rewards[i],
                bonus_reward=bonus_rewards[i],
                claimed=claimed_list[i],
                required_additional_verification=verification_list[i],
            )
            rewards.append((campaign_hashes[i], reward_info))

        return rewards

    def check_wallets_for_campaign(
        self, campaign_name: str, wallets: dict[str, str]
    ) -> list[WalletReward]:
        """여러 지갑의 특정 캠페인 리워드 조회"""
        campaign_hash = self.get_campaign_name_hash(campaign_name)
        results = []

        for name, address in wallets.items():
            try:
                reward_info = self.get_reward_info_by_hash(campaign_hash, address)
                results.append(
                    WalletReward(
                        wallet_name=name,
                        wallet_address=address,
                        campaign_hash=campaign_hash.hex(),
                        total_reward=reward_info.total_reward,
                        bonus_reward=reward_info.bonus_reward,
                        claimed=reward_info.claimed,
                        required_additional_verification=reward_info.required_additional_verification,
                    )
                )
            except Exception as e:
                print(f"Error checking wallet {name} ({address}): {e}")

        return results

    def check_wallets_for_token(
        self, token_address: str, wallets: dict[str, str]
    ) -> dict[str, list[tuple[bytes, RewardInfo]]]:
        """여러 지갑의 특정 토큰 관련 모든 캠페인 리워드 조회"""
        results = {}

        for name, address in wallets.items():
            try:
                rewards = self.get_all_reward_info(token_address, address)
                results[name] = rewards
            except Exception as e:
                print(f"Error checking wallet {name} ({address}): {e}")
                results[name] = []

        return results

    def discover_campaigns_from_events(
        self, from_block: int | None = None, to_block: str | int = "latest", block_range: int = 100000
    ) -> list[dict]:
        """RewardsAdded 이벤트를 조회하여 캠페인 목록 발견

        Args:
            from_block: 시작 블록 (None이면 최근 block_range 블록부터)
            to_block: 끝 블록
            block_range: from_block이 None일 때 조회할 최근 블록 수
        """
        try:
            latest_block = self.w3.eth.block_number
            if from_block is None:
                from_block = max(0, latest_block - block_range)

            # web3.py 7.x에서는 from_block, to_block 파라미터 사용
            events = self.contract.events.RewardsAdded.get_logs(
                from_block=from_block,
                to_block=to_block,
            )

            campaigns = []
            for event in events:
                campaigns.append({
                    "campaign_hash": event["args"]["campaignNameHash"].hex(),
                    "token": event["args"]["token"],
                    "start_date": event["args"]["startDate"],
                    "deadline": event["args"]["deadline"],
                    "block_number": event["blockNumber"],
                    "tx_hash": event["transactionHash"].hex(),
                })
            return campaigns
        except Exception as e:
            print(f"Error discovering campaigns from events: {e}")
            return []

    def get_claimed_events_for_wallet(
        self, wallet_address: str, from_block: int = 0, to_block: str | int = "latest"
    ) -> list[dict]:
        """특정 지갑의 Claimed 이벤트 조회"""
        wallet = Web3.to_checksum_address(wallet_address)
        try:
            # web3.py 7.x에서는 from_block, to_block 파라미터 사용
            events = self.contract.events.Claimed.get_logs(
                from_block=from_block,
                to_block=to_block,
                argument_filters={"user": wallet},
            )

            claims = []
            for event in events:
                claims.append({
                    "campaign_hash": event["args"]["campaignNameHash"].hex(),
                    "total_reward": event["args"]["totalReward"],
                    "fee": event["args"]["fee"],
                    "block_number": event["blockNumber"],
                    "tx_hash": event["transactionHash"].hex(),
                })
            return claims
        except Exception as e:
            print(f"Error getting claimed events: {e}")
            return []

    def check_wallets_by_campaign_hash(
        self, campaign_hash: bytes, wallets: dict[str, str]
    ) -> list[WalletReward]:
        """캠페인 해시로 여러 지갑의 리워드 조회"""
        results = []

        for name, address in wallets.items():
            try:
                reward_info = self.get_reward_info_by_hash(campaign_hash, address)
                results.append(
                    WalletReward(
                        wallet_name=name,
                        wallet_address=address,
                        campaign_hash=campaign_hash.hex() if isinstance(campaign_hash, bytes) else campaign_hash,
                        total_reward=reward_info.total_reward,
                        bonus_reward=reward_info.bonus_reward,
                        claimed=reward_info.claimed,
                        required_additional_verification=reward_info.required_additional_verification,
                    )
                )
            except Exception as e:
                print(f"Error checking wallet {name} ({address}): {e}")

        return results

    def discover_all_campaigns(
        self, from_block: int | None = None, to_block: str | int = "latest", block_range: int = 100000
    ) -> list[dict]:
        """모든 컨트랙트에서 캠페인 발견"""
        all_campaigns = []

        for i, contract in enumerate(self.contracts):
            contract_addr = self.contract_addresses[i]
            try:
                latest_block = self.w3.eth.block_number
                start_block = from_block if from_block is not None else max(0, latest_block - block_range)

                events = contract.events.RewardsAdded.get_logs(
                    from_block=start_block,
                    to_block=to_block,
                )

                for event in events:
                    all_campaigns.append({
                        "contract_address": contract_addr,
                        "campaign_hash": event["args"]["campaignNameHash"].hex(),
                        "token": event["args"]["token"],
                        "start_date": event["args"]["startDate"],
                        "deadline": event["args"]["deadline"],
                        "block_number": event["blockNumber"],
                        "tx_hash": event["transactionHash"].hex(),
                    })
            except Exception as e:
                print(f"Error discovering campaigns from {contract_addr}: {e}")

        return all_campaigns

    def check_all_contracts_for_wallet(
        self, wallet_address: str
    ) -> list[dict]:
        """모든 컨트랙트에서 지갑의 리워드 조회"""
        wallet = Web3.to_checksum_address(wallet_address)
        all_rewards = []

        for i, contract in enumerate(self.contracts):
            contract_addr = self.contract_addresses[i]

            for campaign_name in KNOWN_CAMPAIGN_NAMES:
                try:
                    result = contract.functions.rewardInfo(campaign_name, wallet).call()
                    if result[0] > 0:  # total_reward > 0
                        all_rewards.append({
                            "contract_address": contract_addr,
                            "campaign_name": campaign_name,
                            "total_reward": result[0],
                            "bonus_reward": result[1],
                            "claimed": result[2],
                            "required_additional_verification": result[3],
                        })
                except Exception:
                    pass

        return all_rewards

    def get_reward_from_contract(
        self, contract_index: int, campaign_hash: bytes, wallet_address: str
    ) -> RewardInfo:
        """특정 컨트랙트에서 리워드 정보 조회"""
        wallet = Web3.to_checksum_address(wallet_address)
        contract = self.contracts[contract_index]
        result = contract.functions.rewardInfoByHash(campaign_hash, wallet).call()
        return RewardInfo(
            total_reward=result[0],
            bonus_reward=result[1],
            claimed=result[2],
            required_additional_verification=result[3],
        )

    def check_wallets_on_all_contracts(
        self, campaign_hash: bytes, wallets: dict[str, str]
    ) -> list[dict]:
        """모든 컨트랙트에서 캠페인 해시로 여러 지갑의 리워드 조회"""
        results = []

        for i, contract in enumerate(self.contracts):
            contract_addr = self.contract_addresses[i]

            for name, address in wallets.items():
                try:
                    reward_info = self.get_reward_from_contract(i, campaign_hash, address)
                    if reward_info.total_reward > 0:
                        results.append({
                            "contract_address": contract_addr,
                            "wallet_name": name,
                            "wallet_address": address,
                            "campaign_hash": campaign_hash.hex() if isinstance(campaign_hash, bytes) else campaign_hash,
                            "total_reward": reward_info.total_reward,
                            "bonus_reward": reward_info.bonus_reward,
                            "claimed": reward_info.claimed,
                            "required_additional_verification": reward_info.required_additional_verification,
                        })
                except Exception:
                    pass

        return results


# =============================================================================
# Utility Functions
# =============================================================================


def wei_to_ether(wei: int) -> float:
    """Wei를 Ether로 변환"""
    return wei / 10**18


def format_timestamp(timestamp: int) -> str:
    """Unix timestamp를 읽기 쉬운 형식으로 변환"""
    if timestamp == 0:
        return "Not set"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def get_campaign_name(campaign_hash: str) -> str:
    """캠페인 해시에서 이름 조회

    1. CAMPAIGN_HASH_TO_NAME 매핑에서 먼저 찾기
    2. KNOWN_CAMPAIGN_NAMES의 해시와 비교
    3. 없으면 해시 축약형 반환
    """
    # 해시 정규화 (0x 접두사 포함)
    if not campaign_hash.startswith("0x"):
        campaign_hash = "0x" + campaign_hash
    campaign_hash = campaign_hash.lower()

    # 1. 수동 매핑에서 찾기
    for h, name in CAMPAIGN_HASH_TO_NAME.items():
        if h.lower() == campaign_hash:
            return name

    # 2. 알려진 이름들의 해시와 비교
    for name in KNOWN_CAMPAIGN_NAMES:
        name_hash = Web3.keccak(text=name).hex()
        if name_hash.lower() == campaign_hash:
            return name

    # 3. 알 수 없는 캠페인 - 해시 축약형 반환
    return f"Unknown ({campaign_hash[:14]}...)"


def print_reward_info(reward: WalletReward) -> None:
    """리워드 정보 출력"""
    print(f"\n  [{reward.wallet_name}]")
    print(f"  Address: {reward.wallet_address}")
    print(f"  Total Reward: {wei_to_ether(reward.total_reward):.4f}")
    print(f"  Bonus Reward: {wei_to_ether(reward.bonus_reward):.4f}")
    print(f"  Claimed: {'Yes' if reward.claimed else 'No'}")
    print(
        f"  Additional Verification: {'Required' if reward.required_additional_verification else 'Not Required'}"
    )


def print_campaign_info(campaign: CampaignInfo, campaign_hash: bytes | None = None) -> None:
    """캠페인 정보 출력"""
    print("\n=== Campaign Info ===")
    if campaign_hash:
        print(f"Campaign Hash: {campaign_hash.hex()}")
    print(f"Token Address: {campaign.token}")
    print(f"Start Date: {format_timestamp(campaign.start_date)}")
    print(f"Deadline: {format_timestamp(campaign.deadline)}")
    print(f"Reclaimed: {'Yes' if campaign.reclaimed else 'No'}")
    print(f"Total Amount: {wei_to_ether(campaign.total_amount):.4f}")
    print(f"Total Claimed: {wei_to_ether(campaign.total_claimed):.4f}")
    if campaign.total_amount > 0:
        claim_rate = (campaign.total_claimed / campaign.total_amount) * 100
        print(f"Claim Rate: {claim_rate:.2f}%")


# =============================================================================
# Main
# =============================================================================


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Spacecoin Airdrop Monitor for Creditcoin Chain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # testnet, wallets.json 사용
  %(prog)s --network mainnet                  # mainnet
  %(prog)s --wallets my_wallets.json          # 지갑 파일 지정
  %(prog)s --address 0x1234...                # 단일 주소 조회
  %(prog)s --address 0x1234... --name "alice" # 단일 주소 + 이름
        """,
    )
    parser.add_argument(
        "--network",
        choices=["mainnet", "mainnet_remote", "testnet"],
        default="testnet",
        help="Network to connect to (default: testnet)",
    )
    parser.add_argument(
        "--block-range",
        type=int,
        default=50000,
        help="Number of recent blocks to scan for events (default: 50000)",
    )
    parser.add_argument(
        "--wallets",
        type=str,
        help=f"Path to wallets JSON file (default: {DEFAULT_WALLETS_FILE})",
    )
    parser.add_argument(
        "--address",
        type=str,
        help="Single wallet address to check (overrides --wallets)",
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Name for the single address (used with --address)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("Spacecoin Airdrop Monitor for Creditcoin Chain")
    print("=" * 60)

    # 지갑 정보 로드
    try:
        wallets = get_wallets(args)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        return

    network = args.network
    print(f"\nNetwork: {network}")
    print(f"Wallets ({len(wallets)}):")
    for name, addr in wallets.items():
        print(f"  - {name}: {addr}")

    # 모니터 초기화
    try:
        monitor = AirdropMonitor(network=network)
    except Exception as e:
        print(f"Failed to initialize monitor: {e}")
        return

    # 컨트랙트 주소 표시
    print(f"\nContracts ({len(monitor.contract_addresses)}):")
    for addr in monitor.contract_addresses:
        print(f"  - {addr}")

    # 연결 확인
    if not monitor.is_connected():
        print(f"Failed to connect to {network} RPC")
        return
    print(f"\nConnected to {network}")
    print(f"Latest block: {monitor.w3.eth.block_number}")

    # 1. Blockscout API를 통해 캠페인 발견 (RPC보다 안정적)
    print("\n" + "=" * 60)
    print("Discovering Campaigns via Blockscout API...")
    print("=" * 60)
    print(f"Blockscout API: {monitor.blockscout_api_url}")

    discovered_campaigns = monitor.discover_campaigns_from_blockscout()

    if discovered_campaigns:
        print(f"\nFound {len(discovered_campaigns)} campaign(s). Checking for rewards...")

        # 먼저 모든 캠페인에서 보상 확인
        campaigns_with_rewards = []
        campaigns_without_rewards = []

        for campaign in discovered_campaigns:
            campaign_hash_hex = campaign['campaign_hash']
            if campaign_hash_hex.startswith("0x"):
                campaign_hash_hex = campaign_hash_hex[2:]
            campaign_hash_bytes = bytes.fromhex(campaign_hash_hex)

            rewards = monitor.check_wallets_on_all_contracts(campaign_hash_bytes, wallets)
            rewards_with_value = [r for r in rewards if r["total_reward"] > 0]

            if rewards_with_value:
                campaigns_with_rewards.append((campaign, rewards_with_value))
            else:
                campaigns_without_rewards.append(campaign)

        # 보상이 있는 캠페인 먼저 출력
        if campaigns_with_rewards:
            print("\n" + "=" * 60)
            print(f"CAMPAIGNS WITH REWARDS ({len(campaigns_with_rewards)})")
            print("=" * 60)

            for campaign, rewards in campaigns_with_rewards:
                campaign_name = get_campaign_name(campaign['campaign_hash'])
                print(f"\n--- Campaign: {campaign_name} ---")
                print(f"Hash: {campaign['campaign_hash']}")
                print(f"Contract: {campaign['contract_address']}")
                print(f"Token: {campaign['token']}")
                print(f"Deadline: {format_timestamp(campaign['deadline'])}")

                total_all_wallets = 0
                for reward in rewards:
                    total_all_wallets += reward["total_reward"]
                    print(f"\n  [{reward['wallet_name']}]")
                    print(f"  Address: {reward['wallet_address']}")
                    print(f"  Total Reward: {wei_to_ether(reward['total_reward']):.4f}")
                    print(f"  Bonus Reward: {wei_to_ether(reward['bonus_reward']):.4f}")
                    print(f"  Claimed: {'Yes' if reward['claimed'] else 'No'}")

                print(f"\n  >>> Total across all wallets: {wei_to_ether(total_all_wallets):.4f}")
        else:
            print("\n>>> No rewards found for any monitored wallet in any campaign.")

        # 보상 없는 캠페인 요약
        if campaigns_without_rewards:
            print(f"\n--- {len(campaigns_without_rewards)} campaign(s) with no rewards for monitored wallets ---")
    else:
        print("\nNo campaigns discovered yet.")

    # 2. 모든 컨트랙트에서 알려진 캠페인 이름들 확인
    print("\n" + "=" * 60)
    print("Checking Known Campaign Names (All Contracts)...")
    print("=" * 60)

    found_any = False
    for i, contract in enumerate(monitor.contracts):
        contract_addr = monitor.contract_addresses[i]

        for campaign_name in KNOWN_CAMPAIGN_NAMES:
            campaign_hash = monitor.get_campaign_name_hash(campaign_name)

            try:
                campaign_info_result = contract.functions.campaignInfo(campaign_name).call()
                token_addr = campaign_info_result[0]

                if token_addr == "0x0000000000000000000000000000000000000000":
                    continue

                found_any = True
                print(f"\n--- Campaign: {campaign_name} ---")
                print(f"Contract: {contract_addr}")
                print(f"Token: {token_addr}")
                print(f"Start Date: {format_timestamp(campaign_info_result[1])}")
                print(f"Deadline: {format_timestamp(campaign_info_result[2])}")
                print(f"Total Amount: {wei_to_ether(campaign_info_result[4]):.4f}")
                print(f"Total Claimed: {wei_to_ether(campaign_info_result[5]):.4f}")

                # 각 지갑 확인
                print("\n--- Wallet Rewards ---")
                for wallet_name, wallet_addr in wallets.items():
                    try:
                        wallet_checksum = Web3.to_checksum_address(wallet_addr)
                        reward_result = contract.functions.rewardInfo(campaign_name, wallet_checksum).call()
                        if reward_result[0] > 0:
                            print(f"\n  [{wallet_name}]")
                            print(f"  Address: {wallet_addr}")
                            print(f"  Total Reward: {wei_to_ether(reward_result[0]):.4f}")
                            print(f"  Bonus Reward: {wei_to_ether(reward_result[1]):.4f}")
                            print(f"  Claimed: {'Yes' if reward_result[2] else 'No'}")
                    except Exception:
                        pass

            except Exception:
                pass

    if not found_any:
        print("\nNo active campaigns found with known names.")

    # 3. 요약
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    # 지갑별 총 보상 요약 계산
    wallet_totals: dict[str, dict] = {}
    for name in wallets:
        wallet_totals[name] = {
            "total_reward": 0,
            "bonus_reward": 0,
            "unclaimed": 0,
            "claimed": 0,
            "campaign_count": 0,
        }

    if campaigns_with_rewards:
        for campaign, rewards in campaigns_with_rewards:
            for reward in rewards:
                name = reward["wallet_name"]
                wallet_totals[name]["total_reward"] += reward["total_reward"]
                wallet_totals[name]["bonus_reward"] += reward["bonus_reward"]
                wallet_totals[name]["campaign_count"] += 1
                if reward["claimed"]:
                    wallet_totals[name]["claimed"] += reward["total_reward"]
                else:
                    wallet_totals[name]["unclaimed"] += reward["total_reward"]

    # 보상 요약 출력
    print("\nWallet Rewards Summary:")
    print("-" * 60)
    grand_total = 0
    grand_unclaimed = 0
    for name, address in wallets.items():
        totals = wallet_totals[name]
        if totals["total_reward"] > 0:
            grand_total += totals["total_reward"]
            grand_unclaimed += totals["unclaimed"]
            status = "Claimed" if totals["unclaimed"] == 0 else "Unclaimed"
            print(f"  {name}: {wei_to_ether(totals['total_reward']):,.4f} ({status})")
        else:
            print(f"  {name}: 0.0000")

    if grand_total > 0:
        print("-" * 60)
        print(f"  TOTAL: {wei_to_ether(grand_total):,.4f}")
        print(f"  Unclaimed: {wei_to_ether(grand_unclaimed):,.4f}")

    print("\nMonitored Contracts:")
    # 네트워크별 Blockscout URL 사용
    blockscout_base = monitor.blockscout_api_url.replace("/api/v2", "")
    for addr in monitor.contract_addresses:
        print(f"  {blockscout_base}/address/{addr}")


if __name__ == "__main__":
    main()
