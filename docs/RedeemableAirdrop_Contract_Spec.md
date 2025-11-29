# RedeemableAirdrop Contract 명세서

## 1. Contract 개요

캠페인 기반 토큰 에어드랍 관리 스마트 컨트랙트입니다.

- 운영자가 캠페인을 생성하고 계정별 리워드 수량 등록
- 사용자가 등록된 리워드를 claim하여 수령
- 만료된 캠페인의 미수령 토큰은 관리자가 회수 가능

---

## 2. 핵심 데이터 구조

### 2-1. Reward (개별 리워드 정보)

```solidity
struct Reward {
    uint120 totalReward;                    // 총 리워드 수량
    uint120 bonusReward;                    // 보너스 수량 (totalReward에 포함됨, 표시용)
    bool claimed;                           // 수령 완료 여부
    bool requiredAdditionalVerification;    // 추가 인증 필요 여부
}
```

### 2-2. Campaign (캠페인 정보)

```solidity
struct Campaign {
    address token;                          // 에어드랍 토큰 주소
    uint64 startDate;                       // 시작 시간 (unix timestamp)
    uint64 deadline;                        // 마감 시간 (unix timestamp)
    bool reclaimed;                         // 회수 완료 여부
    uint256 totalAmount;                    // 캠페인 총 토큰 수량
    uint256 totalClaimed;                   // 수령 완료된 총 수량
    mapping(address => Reward) rewards;     // 계정별 리워드 매핑
}
```

---

## 3. View 함수 (조회용)

### 3-1. rewardInfoByHash

특정 캠페인에서 특정 지갑의 리워드 정보를 조회합니다.

```solidity
function rewardInfoByHash(
    bytes32 campaignNameHash,
    address wallet
) public view returns (uint120, uint120, bool, bool)
```

**입력:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignNameHash | bytes32 | 캠페인 이름의 keccak256 해시 |
| wallet | address | 조회할 지갑 주소 |

**출력 (순서대로):**

| 순서 | 타입 | 설명 |
|------|------|------|
| 1 | uint120 | totalReward - 받을 총 리워드 |
| 2 | uint120 | bonusReward - 보너스 리워드 |
| 3 | bool | claimed - 수령 완료 여부 |
| 4 | bool | requiredAdditionalVerification - 추가 인증 필요 여부 |

---

### 3-2. allRewardInfo

특정 토큰의 모든 캠페인에서 특정 지갑의 리워드 정보를 조회합니다.

```solidity
function allRewardInfo(
    address token,
    address wallet
) external view returns (
    bytes32[] memory,   // campaignNameHashes
    uint120[] memory,   // totalRewards
    uint120[] memory,   // bonusRewards
    bool[] memory,      // claimed
    bool[] memory       // requiredAdditionalVerification
)
```

**입력:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| token | address | 토큰 컨트랙트 주소 |
| wallet | address | 조회할 지갑 주소 |

**출력:** 5개의 배열 (모든 배열의 인덱스가 동일한 캠페인을 가리킴)

| 순서 | 타입 | 설명 |
|------|------|------|
| 1 | bytes32[] | campaignNameHashes - 캠페인 해시 목록 |
| 2 | uint120[] | totalRewards - 각 캠페인별 총 리워드 |
| 3 | uint120[] | bonusRewards - 각 캠페인별 보너스 |
| 4 | bool[] | claimed - 각 캠페인별 수령 여부 |
| 5 | bool[] | requiredAdditionalVerification - 각 캠페인별 추가 인증 필요 여부 |

---

### 3-3. campaignInfoByHash

캠페인의 전체 정보를 조회합니다.

```solidity
function campaignInfoByHash(
    bytes32 campaignNameHash
) public view returns (address, uint64, uint64, bool, uint256, uint256)
```

**입력:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignNameHash | bytes32 | 캠페인 이름의 keccak256 해시 |

**출력 (순서대로):**

| 순서 | 타입 | 설명 |
|------|------|------|
| 1 | address | token - 토큰 주소 |
| 2 | uint64 | startDate - 시작 시간 |
| 3 | uint64 | deadline - 마감 시간 |
| 4 | bool | reclaimed - 회수 완료 여부 |
| 5 | uint256 | totalAmount - 캠페인 총 수량 |
| 6 | uint256 | totalClaimed - 수령 완료 수량 |

---

### 3-4. tokenCampaigns

특정 토큰의 모든 캠페인 해시 목록을 조회합니다.

```solidity
function tokenCampaigns(
    address token
) external view returns (bytes32[] memory)
```

**입력:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| token | address | 토큰 컨트랙트 주소 |

**출력:**

| 타입 | 설명 |
|------|------|
| bytes32[] | 해당 토큰의 모든 캠페인 해시 목록 |

---

### 3-5. rewardInfo

캠페인 이름(문자열)으로 리워드 정보를 조회합니다.

```solidity
function rewardInfo(
    string calldata campaignName,
    address wallet
) external view returns (uint120, uint120, bool, bool)
```

**입력:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignName | string | 캠페인 이름 (문자열) |
| wallet | address | 조회할 지갑 주소 |

**출력:** rewardInfoByHash와 동일

---

### 3-6. campaignInfo

캠페인 이름(문자열)으로 캠페인 정보를 조회합니다.

```solidity
function campaignInfo(
    string calldata campaignName
) external view returns (address, uint64, uint64, bool, uint256, uint256)
```

**입력:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignName | string | 캠페인 이름 (문자열) |

**출력:** campaignInfoByHash와 동일

---

## 4. 이벤트

### 4-1. Claimed

리워드 수령 시 발생합니다.

```solidity
event Claimed(
    address indexed user,
    bytes32 indexed campaignNameHash,
    uint120 totalReward,
    uint256 fee
);
```

| 필드 | 타입 | 설명 |
|------|------|------|
| user | address | 수령자 주소 |
| campaignNameHash | bytes32 | 캠페인 해시 |
| totalReward | uint120 | 수령한 총 리워드 |
| fee | uint256 | 차감된 수수료 |

---

### 4-2. RewardsAdded

캠페인 생성 시 발생합니다.

```solidity
event RewardsAdded(
    bytes32 indexed campaignNameHash,
    address indexed token,
    uint64 startDate,
    uint64 deadline
);
```

| 필드 | 타입 | 설명 |
|------|------|------|
| campaignNameHash | bytes32 | 캠페인 해시 |
| token | address | 토큰 주소 |
| startDate | uint64 | 시작 시간 |
| deadline | uint64 | 마감 시간 |

---

### 4-3. RewardsUpdated

캠페인 수정 시 발생합니다.

```solidity
event RewardsUpdated(
    bytes32 indexed campaignNameHash,
    address indexed token
);
```

| 필드 | 타입 | 설명 |
|------|------|------|
| campaignNameHash | bytes32 | 캠페인 해시 |
| token | address | 토큰 주소 |

---

### 4-4. RewardsReclaimed

미수령 토큰 회수 시 발생합니다.

```solidity
event RewardsReclaimed(
    bytes32 indexed campaignNameHash,
    address indexed recipient
);
```

| 필드 | 타입 | 설명 |
|------|------|------|
| campaignNameHash | bytes32 | 캠페인 해시 |
| recipient | address | 회수 토큰 수령자 |

---

### 4-5. ClaimantAdditionalVerificationUpdated

추가 인증 설정 변경 시 발생합니다.

```solidity
event ClaimantAdditionalVerificationUpdated(
    bytes32 indexed campaignNameHash,
    address indexed account,
    bool required
);
```

| 필드 | 타입 | 설명 |
|------|------|------|
| campaignNameHash | bytes32 | 캠페인 해시 |
| account | address | 대상 계정 |
| required | bool | 추가 인증 필요 여부 |

---

### 4-6. ReclaimSkipped

회수할 토큰이 없을 때 발생합니다.

```solidity
event ReclaimSkipped(bytes32 indexed campaignNameHash);
```

---

## 5. 리워드 등록 함수 (관리자 전용)

### 5-1. addRewards

새 캠페인을 생성하고 초기 수령자를 등록합니다.

```solidity
function addRewards(
    bytes32 campaignNameHash,
    address token,
    uint64 startDate,
    uint64 deadline,
    address[] calldata accounts,
    uint120[] calldata totalRewards,
    uint120[] calldata bonusRewards,
    bool[] calldata requiredAdditionalVerification
) external
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignNameHash | bytes32 | 캠페인 이름의 keccak256 해시 |
| token | address | 에어드랍 토큰 주소 |
| startDate | uint64 | 시작 시간 |
| deadline | uint64 | 마감 시간 |
| accounts | address[] | 수령자 주소 배열 |
| totalRewards | uint120[] | 각 수령자별 총 리워드 |
| bonusRewards | uint120[] | 각 수령자별 보너스 |
| requiredAdditionalVerification | bool[] | 각 수령자별 추가 인증 필요 여부 |

---

### 5-2. addClaimants

기존 캠페인에 수령자를 추가합니다.

```solidity
function addClaimants(
    bytes32 campaignNameHash,
    address[] calldata accounts,
    uint120[] calldata totalRewards,
    uint120[] calldata bonusRewards,
    bool[] calldata requiredAdditionalVerification
) external
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignNameHash | bytes32 | 캠페인 해시 |
| accounts | address[] | 추가할 수령자 주소 배열 |
| totalRewards | uint120[] | 각 수령자별 총 리워드 |
| bonusRewards | uint120[] | 각 수령자별 보너스 |
| requiredAdditionalVerification | bool[] | 각 수령자별 추가 인증 필요 여부 |

---

### 5-3. updateRewards

기존 캠페인의 리워드 정보를 수정합니다. (기존 값을 덮어씀)

```solidity
function updateRewards(
    bytes32 campaignNameHash,
    address token,
    uint64 startDate,
    uint64 deadline,
    address[] calldata accounts,
    uint120[] calldata totalRewards,
    uint120[] calldata bonusRewards,
    bool[] calldata requiredAdditionalVerification
) external
```

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| campaignNameHash | bytes32 | 캠페인 해시 |
| token | address | 토큰 주소 |
| startDate | uint64 | 새 시작 시간 |
| deadline | uint64 | 새 마감 시간 |
| accounts | address[] | 수정할 수령자 주소 배열 |
| totalRewards | uint120[] | 각 수령자별 새 총 리워드 |
| bonusRewards | uint120[] | 각 수령자별 새 보너스 |
| requiredAdditionalVerification | bool[] | 각 수령자별 추가 인증 필요 여부 |

**주의:** 이미 `claimed: true`인 계정은 수정되지 않습니다.

---

## 6. Claim 함수 (사용자용)

### 6-1. claim

특정 캠페인의 리워드를 직접 청구합니다.

```solidity
function claim(bytes32 campaignNameHash) external returns (bool)
```

---

### 6-2. claimByToken

해당 토큰의 모든 캠페인 리워드를 한 번에 청구합니다.

```solidity
function claimByToken(address token) external returns (bool)
```

---

### 6-3. claimWithSignature

서명 기반 청구 (가스비 대납 시 사용, fee 공제 가능)

```solidity
function claimWithSignature(
    address owner,
    bytes32 campaignNameHash,
    uint256 fee,
    uint64 deadline,
    uint8 v,
    bytes32 r,
    bytes32 s
) external returns (bool)
```

---

### 6-4. claimFor

운영자가 특정 계정들을 대신해서 에어드랍 수령 처리 (OPERATOR_ROLE 필요)

```solidity
function claimFor(
    string calldata campaignName,
    address[] calldata accounts
) external returns (bool)
```

---

## 7. Python 개발 가이드

### 7-1. campaignNameHash 생성 방법

```python
from web3 import Web3

campaign_name = "SpaceCoin Airdrop 2024"
campaign_name_hash = Web3.keccak(text=campaign_name)
```

### 7-2. 필요한 ABI 함수 목록

```python
required_functions = [
    "rewardInfoByHash(bytes32,address)",
    "allRewardInfo(address,address)",
    "campaignInfoByHash(bytes32)",
    "campaignInfo(string)",
    "tokenCampaigns(address)",
    "rewardInfo(string,address)",
]
```

### 7-3. 추적할 이벤트 목록

```python
required_events = [
    "Claimed(address,bytes32,uint120,uint256)",
    "RewardsAdded(bytes32,address,uint64,uint64)",
    "RewardsUpdated(bytes32,address)",
    "RewardsReclaimed(bytes32,address)",
    "ClaimantAdditionalVerificationUpdated(bytes32,address,bool)",
]
```

### 7-4. 호출 예시 (web3.py)

```python
from web3 import Web3

# 연결
w3 = Web3(Web3.HTTPProvider('https://your-rpc-url'))
contract = w3.eth.contract(address=contract_address, abi=abi)

# 캠페인 해시 생성
campaign_name = "SpaceCoin Airdrop 2024"
campaign_hash = Web3.keccak(text=campaign_name)

# 리워드 정보 조회
total_reward, bonus_reward, claimed, required_verification = contract.functions.rewardInfoByHash(
    campaign_hash,
    wallet_address
).call()

# 캠페인 정보 조회
token, start_date, deadline, reclaimed, total_amount, total_claimed = contract.functions.campaignInfoByHash(
    campaign_hash
).call()

# 특정 토큰의 모든 캠페인에서 지갑의 리워드 조회
campaign_hashes, total_rewards, bonus_rewards, claimed_list, verification_list = contract.functions.allRewardInfo(
    token_address,
    wallet_address
).call()
```

### 7-5. 이벤트 조회 예시 (web3.py)

```python
# Claimed 이벤트 조회
claimed_filter = contract.events.Claimed.create_filter(
    fromBlock=start_block,
    toBlock='latest',
    argument_filters={'user': wallet_address}  # 선택적 필터
)
claimed_events = claimed_filter.get_all_entries()

for event in claimed_events:
    print({
        'user': event['args']['user'],
        'campaignNameHash': event['args']['campaignNameHash'].hex(),
        'totalReward': event['args']['totalReward'],
        'fee': event['args']['fee'],
        'blockNumber': event['blockNumber'],
        'transactionHash': event['transactionHash'].hex()
    })
```

---

## 8. 통계 활용 예시

| 통계 항목 | 데이터 소스 |
|-----------|-------------|
| 캠페인별 총 에어드랍 수량 | `campaignInfoByHash` → `totalAmount` |
| 캠페인별 수령 완료 수량 | `campaignInfoByHash` → `totalClaimed` |
| 캠페인별 수령률 | `totalClaimed / totalAmount * 100` |
| 계정별 수령 내역 | `Claimed` 이벤트 수집 |
| 계정별 등록 리워드 | `rewardInfoByHash` 또는 `addRewards`/`addClaimants` calldata |
| 미수령 계정 목록 | `rewardInfoByHash` → `claimed == false` |
| 추가 인증 대기 계정 | `rewardInfoByHash` → `requiredAdditionalVerification == true` |

---

## 9. 주의사항

1. **updateRewards**는 기존 수량을 덮어씁니다 (누적 아님)
2. 이미 `claimed: true`인 계정은 updateRewards로 수정 불가
3. **reclaim된 캠페인**은 `tokenCampaigns` 목록에서 제거됨
4. 이벤트에는 개별 계정 수량이 기록되지 않으므로, 등록 수량 파악 시 **calldata 파싱 필요**
5. View 함수는 가스 비용이 없음 (읽기 전용)
