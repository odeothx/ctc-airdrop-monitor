# Creditcoin Airdrop Monitor

Creditcoin Chain의 에어드롭 보상을 모니터링하는 CLI 도구입니다.

## 기능

- 여러 지갑의 에어드롭 보상 조회
- Mainnet 및 Testnet 지원
- Blockscout API를 통한 캠페인 자동 탐색
- 지갑별 보상 요약 제공
- 단일 지갑 조회 지원

## 설치

### 필수 요건

- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) (권장) 또는 pip

### uv 사용 (권장)

```bash
# 의존성 설치
uv sync

# 실행
uv run python main.py
```

### pip 사용

```bash
# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 의존성 설치
pip install -e .

# 실행
python main.py
```

## 사용법

### 기본 사용

```bash
# testnet에서 wallets.json 지갑들 조회 (기본값)
uv run python main.py

# mainnet에서 조회
uv run python main.py --network mainnet

# 원격 mainnet RPC 사용
uv run python main.py --network mainnet_remote
```

### 지갑 파일 지정

```bash
# 사용자 정의 지갑 파일 사용
uv run python main.py --wallets my_wallets.json
```

### 단일 지갑 조회

```bash
# 단일 지갑 조회
uv run python main.py --address 0x1234567890abcdef...

# 단일 지갑에 이름 부여
uv run python main.py --address 0x1234567890abcdef... --name "my_wallet"
```

### CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--network` | 네트워크 선택 (mainnet, mainnet_remote, testnet) | testnet |
| `--wallets` | 지갑 JSON 파일 경로 | wallets.json |
| `--address` | 단일 지갑 주소 (--wallets 대신 사용) | - |
| `--name` | 단일 지갑의 이름 (--address와 함께 사용) | - |
| `--block-range` | 이벤트 조회 블록 범위 | 50000 |

## 설정

### wallets.json

조회할 지갑 목록을 JSON 형식으로 지정합니다.

```json
{
  "wallet1": "0x1234567890abcdef...",
  "wallet2": "0xabcdef1234567890...",
  "my_main_wallet": "0x..."
}
```

**주의**: `wallets.json`은 `.gitignore`에 포함되어 있어 git에 커밋되지 않습니다.

### settings.py

네트워크 설정 및 컨트랙트 주소를 관리합니다.

#### 네트워크 설정

| 네트워크 | RPC URL | 설명 |
|----------|---------|------|
| mainnet | http://127.0.0.1:9944 | 로컬 노드 필요 |
| mainnet_remote | https://rpc.mainnet.creditcoin.network | 원격 노드 RPC |
| testnet | https://rpc.cc3-testnet.creditcoin.network | 테스트넷 RPC |

#### Blockscout API URLs

| 네트워크 | API URL |
|----------|---------|
| mainnet | https://creditcoin.blockscout.com/api/v2 |
| testnet | https://creditcoin-testnet.blockscout.com/api/v2 |

#### RedeemableAirdrop 컨트랙트

**Mainnet:**
- 0xe272c3fb6d4ccf5A8bca94465f58b9c09f497Cd6
- 0x44D61789e4e6d2e06be032bD63fB2E86503B53A1
- 0xC1f68532EE64AF333C43dfb7b4Ad93034F136e22

**Testnet:**
- 0x824c6A8FB6311379bf8Ba10e90C1843B16E3A4cE

#### 토큰 주소

| 토큰 | 네트워크 | 주소 |
|------|----------|------|
| Spacecoin | Mainnet | 0x7ab7C6A935Ab2D1437398790C9C0660af62A80b9 |
| Spacecoin | Testnet | 0xfaFAd008f017C326B62FbfddA7fb2335A5c82247 |

#### 캠페인 이름 매핑

캠페인 해시에서 이름을 복원할 수 없으므로 `CAMPAIGN_HASH_TO_NAME`에 수동으로 매핑을 추가할 수 있습니다:

```python
CAMPAIGN_HASH_TO_NAME = {
    "0x2cfc0ae0...": "Mainnet Campaign #1",
    "0x2499af02...": "Testnet SpaceCoin Airdrop",
}
```

## 출력 예시

```
============================================================
Spacecoin Airdrop Monitor for Creditcoin Chain
============================================================

Network: testnet
Wallets (3):
  - wallet1: 0x1234...
  - wallet2: 0xabcd...
  - wallet3: 0xefgh...

Contracts (1):
  - 0x824c6A8FB6311379bf8Ba10e90C1843B16E3A4cE

Connected to testnet
Latest block: 12345678

============================================================
Discovering Campaigns via Blockscout API...
============================================================

Found 5 campaign(s). Checking for rewards...

============================================================
CAMPAIGNS WITH REWARDS (1)
============================================================

--- Campaign: Testnet SpaceCoin Airdrop ---
Hash: 0x2499af02d29716ec568358aac3c95698feff985f7e2a614ac6c2fddbd6e9a103
Contract: 0x824c6A8FB6311379bf8Ba10e90C1843B16E3A4cE
Token: 0xfaFAd008f017C326B62FbfddA7fb2335A5c82247
Deadline: 2025-12-31 23:59:59

  [wallet1]
  Address: 0x1234...
  Total Reward: 1000000.0000
  Bonus Reward: 0.0000
  Claimed: No

  >>> Total across all wallets: 1000000.0000

============================================================
Summary
============================================================

Wallet Rewards Summary:
------------------------------------------------------------
  wallet1: 1,000,000.0000 (Unclaimed)
  wallet2: 0.0000
  wallet3: 0.0000
------------------------------------------------------------
  TOTAL: 1,000,000.0000
  Unclaimed: 1,000,000.0000

Monitored Contracts:
  https://creditcoin-testnet.blockscout.com/address/0x824c6A8FB6311379bf8Ba10e90C1843B16E3A4cE
```

## 의존성

- [web3.py](https://web3py.readthedocs.io/) >= 6.0.0 - Ethereum/EVM 상호작용
- [httpx](https://www.python-httpx.org/) >= 0.25.0 - HTTP 클라이언트 (Blockscout API)

## 라이선스

MIT
