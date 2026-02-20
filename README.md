# fclean

오래된, 크고, 중복된 파일을 정리하는 CLI 도구입니다.

## 개요

**fclean**은 파이썬 기반의 강력한 파일 정리 도구로, 날짜, 크기, 패턴 매칭, 그리고 중복 파일 탐지를 기반으로 불필요한 파일들을 효율적으로 정리할 수 있습니다. 안전성을 최우선으로 설계되어 있으며, 기본적으로 드라이런 모드로 동작하고 휴지통으로 이동시킵니다.

## 주요 기능

- **날짜 기반 필터링**: 특정 기간보다 오래된 파일 찾기 (예: 30일 이상)
- **크기 기반 필터링**: 특정 크기보다 크거나 작은 파일 찾기
- **패턴 매칭**: 글롭 패턴으로 파일 이름 필터링 (예: `*.tmp`, `*.log`)
- **중복 파일 탐지**: xxhash를 이용한 고속 중복 파일 발견
- **시스템 정리 제안**: 알려진 임시 디렉토리의 크기 및 파일 수 제안
- **안전한 삭제**: 드라이런 기본값, 휴지통 이동, 시스템 파일 자동 보호
- **YAML 설정 파일**: 복잡한 정리 규칙을 설정 파일로 관리

## 설치

### 요구사항

- Python 3.10 이상

### pip를 이용한 설치

```bash
pip install fclean
```

### 개발 모드 설치

```bash
git clone <repository-url>
cd file_remover
pip install -e ".[dev]"
```

## 빠른 시작

### 디렉토리 스캔하기

지정한 디렉토리의 파일을 스캔하고 통계를 확인합니다:

```bash
fclean scan ~/Downloads
```

필터를 적용하여 특정 조건의 파일만 찾기:

```bash
# 30일 이상 된 파일 찾기
fclean scan ~/Downloads --older-than 30d

# 100MB 이상의 파일 찾기
fclean scan ~/Downloads --larger-than 100MB

# 특정 패턴의 파일 찾기
fclean scan ~/Downloads --pattern "*.tmp" --pattern "*.log"
```

### 파일 정리하기

**중요**: `clean` 명령은 기본적으로 드라이런 모드입니다. 실제 삭제를 위해서는 `--execute` 플래그를 사용해야 합니다.

```bash
# 드라이런: 30일 이상 된 파일이 무엇인지 확인만 하기
fclean clean ~/Downloads --older-than 30d

# 실제로 파일 정리하기 (휴지통으로 이동)
fclean clean ~/Downloads --older-than 30d --execute

# 실제로 파일 정리하기 (영구 삭제)
fclean clean ~/Downloads --older-than 30d --execute --permanent

# 확인 프롬프트 없이 실행하기 (자동화용)
fclean clean ~/Downloads --older-than 30d --execute --yes
```

### 중복 파일 찾기

```bash
# 1KB 이상의 중복 파일 찾기
fclean duplicates ~/Downloads --min-size 1024
```

### 시스템 정리 제안 보기

```bash
# 정리할 수 있는 시스템 디렉토리 제안 보기
fclean suggest
```

## 명령어 레퍼런스

### scan - 디렉토리 스캔

파일 시스템을 스캔하여 파일 정보를 수집하고 필터 조건에 맞는 파일을 표시합니다.

```bash
fclean scan <path> [options]
```

**옵션:**

| 옵션 | 약자 | 설명 | 예시 |
|------|------|------|------|
| `--older-than` | `-o` | 지정한 기간보다 오래된 파일 필터링 | `30d`, `6m`, `1y` |
| `--larger-than` | `-l` | 지정한 크기보다 큰 파일 필터링 | `100MB`, `1.5GB` |
| `--smaller-than` | `-s` | 지정한 크기보다 작은 파일 필터링 | `1KB`, `100MB` |
| `--pattern` | `-p` | 글롭 패턴으로 파일명 필터링 (반복 가능) | `*.tmp`, `*.log` |
| `--skip-hidden` | | 숨김 파일/디렉토리 제외 | |
| `--limit` | `-n` | 결과에서 보여줄 최대 파일 수 (기본값: 20) | `50` |

**예시:**

```bash
# 6개월 이상 된 파일 스캔
fclean scan ~/Downloads --older-than 6m

# 100MB 이상의 .zip 파일 스캔
fclean scan ~/Downloads --larger-than 100MB --pattern "*.zip"

# 숨김 파일 제외하고 스캔, 상위 50개만 표시
fclean scan ~/ --skip-hidden --limit 50
```

### clean - 파일 정리

조건에 맞는 파일을 찾아 삭제합니다. **기본값은 드라이런 모드입니다.**

```bash
fclean clean <path> [options]
```

**옵션:**

| 옵션 | 약자 | 설명 | 기본값 |
|------|------|------|--------|
| `--older-than` | `-o` | 지정한 기간보다 오래된 파일 | 필수 (하나 이상) |
| `--larger-than` | `-l` | 지정한 크기보다 큰 파일 | 선택 |
| `--pattern` | `-p` | 글롭 패턴으로 파일명 필터링 (반복 가능) | 선택 |
| `--config` | `-c` | YAML 설정 파일 경로 | 선택 |
| `--execute` | `-x` | 실제 삭제 실행 (없으면 드라이런) | false |
| `--trash/--permanent` | | 휴지통 이동 또는 영구 삭제 | --trash |
| `--skip-hidden` | | 숨김 파일/디렉토리 제외 | false |
| `--yes` | `-y` | 확인 프롬프트 건너뛰기 (자동화용) | false |

**주의 사항:**

- **`--execute` 없이는 드라이런**으로 동작하여 실제 파일이 삭제되지 않습니다.
- **기본값은 휴지통 이동**입니다. 영구 삭제하려면 `--permanent` 플래그를 추가하세요.
- **`--execute` 없이는 `--yes` 플래그가 무시됩니다.**

**예시:**

```bash
# 드라이런: 30일 이상 된 파일 목록 확인
fclean clean ~/Downloads --older-than 30d

# 파일 정리 실행 (휴지통으로 이동)
fclean clean ~/Downloads --older-than 30d --execute

# 여러 조건 결합
fclean clean ~/Downloads --older-than 7d --larger-than 500MB --execute

# YAML 설정 파일로 정리
fclean clean --config rules.yaml --execute

# 영구 삭제 (복구 불가)
fclean clean ~/Downloads --older-than 1y --execute --permanent

# 자동화 스크립트용 (확인 프롬프트 제외)
fclean clean ~/Downloads --older-than 30d --execute --yes
```

### duplicates - 중복 파일 찾기

파일 내용 해시를 이용하여 중복된 파일들을 찾아 표시합니다.

```bash
fclean duplicates <path> [options]
```

**옵션:**

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--min-size` | 확인할 파일의 최소 크기 (바이트) | 1024 |
| `--skip-hidden` | 숨김 파일/디렉토리 제외 | false |

**중복 탐지 알고리즘:**

1. **단계 1 - 크기 비교**: 파일 크기가 다르면 중복 불가능 (빠른 필터링)
2. **단계 2 - 빠른 해시**: 파일의 처음 4KB를 xxhash로 비교 (성능 최적화)
3. **단계 3 - 전체 해시**: 전체 파일 내용을 xxhash로 비교하여 확실히 중복 판단

**예시:**

```bash
# 1KB 이상의 중복 파일 찾기
fclean duplicates ~/Downloads --min-size 1024

# 숨김 파일 제외하고 찾기
fclean duplicates ~/ --skip-hidden

# 전체 파일 시스템에서 중복 찾기 (시간이 걸릴 수 있음)
fclean duplicates ~/ --min-size 10485760
```

### suggest - 정리 제안

시스템에서 정리할 수 있는 알려진 디렉토리를 제안합니다.

```bash
fclean suggest
```

운영 체제에 따라 다음과 같은 디렉토리들이 제안될 수 있습니다:

**Windows:**
- 사용자 캐시 (User Cache)
- Windows 임시 파일 (Windows Temp)
- 썸네일 캐시 (Thumbnail Cache)
- 최근 파일 목록 (Recent Files)
- 브라우저 캐시 (Chrome Cache 등)

**Linux/macOS:**
- 사용자 캐시 (User Cache)
- 임시 파일 (Temp Files)
- 휴지통 (Trash)
- 썸네일 캐시 (Thumbnail Cache)
- 저널 로그 (Journal Logs)
- 브라우저 캐시 (Chrome Cache 등)

## 시간 단위 및 크기 단위

### 시간 필터 (`--older-than`)

| 단위 | 의미 | 예시 |
|------|------|------|
| `d` | 일 | `30d` = 30일 |
| `w` | 주 | `4w` = 4주 |
| `m` | 월 | `6m` = 6개월 (30일 기준) |
| `y` | 년 | `1y` = 1년 (365일 기준) |

### 크기 필터 (`--larger-than`, `--smaller-than`)

| 단위 | 의미 | 예시 |
|------|------|------|
| `B` | 바이트 | `1024B` |
| `KB` | 킬로바이트 | `512KB` |
| `MB` | 메가바이트 | `100MB` |
| `GB` | 기가바이트 | `1.5GB` |
| `TB` | 테라바이트 | `1TB` |

## YAML 설정 파일

복잡한 정리 규칙을 YAML 설정 파일로 관리할 수 있습니다.

### 기본 구조

```yaml
rules:
  - name: "규칙 이름"
    paths:
      - "~/Downloads"
      - "/tmp"
    older_than: "30d"          # 선택
    larger_than: "100MB"       # 선택
    smaller_than: "1KB"        # 선택
    patterns:                  # 선택
      - "*.tmp"
      - "*.log"
    extensions:                # 선택
      - ".o"
      - ".pyc"
    skip_hidden: false         # 선택 (기본값: false)
```

### 설정 파일 예시

```yaml
rules:
  - name: "오래된 다운로드 파일"
    paths:
      - "~/Downloads"
    older_than: "30d"

  - name: "큰 임시 파일"
    paths:
      - "~/Downloads"
      - "/tmp"
    larger_than: "100MB"
    older_than: "7d"

  - name: "불필요한 파일"
    paths:
      - "~"
    patterns:
      - "*.tmp"
      - "*.temp"
      - "*.log"
      - "*.bak"
      - "~$*"
      - "Thumbs.db"
      - ".DS_Store"
    skip_hidden: true

  - name: "오래된 빌드 산출물"
    paths:
      - "~/Projects"
    extensions:
      - ".o"
      - ".obj"
      - ".pyc"
      - ".class"
    older_than: "14d"
```

### 설정 파일로 정리 실행

```bash
# 드라이런: 설정 파일에 정의된 규칙 미리보기
fclean clean --config rules.yaml

# 실제 정리 실행 (휴지통으로 이동)
fclean clean --config rules.yaml --execute

# 자동화 스크립트용 (확인 프롬프트 제외)
fclean clean --config rules.yaml --execute --yes

# 영구 삭제
fclean clean --config rules.yaml --execute --permanent --yes
```

## 안전 기능

fclean은 다음과 같은 안전 메커니즘을 갖추고 있습니다:

### 1. 드라이런 기본값

`--execute` 플래그 없이는 실제 파일이 삭제되지 않습니다:

```bash
# 안전함: 무엇이 삭제될지만 보여줌
fclean clean ~/Downloads --older-than 30d

# 실제 삭제: 명시적으로 --execute 지정 필요
fclean clean ~/Downloads --older-than 30d --execute
```

### 2. 휴지통 이동 기본값

기본적으로 파일은 휴지통으로 이동되어 복구 가능합니다:

```bash
# 휴지통으로 이동 (복구 가능)
fclean clean ~/Downloads --older-than 30d --execute

# 영구 삭제 (복구 불가)
fclean clean ~/Downloads --older-than 30d --execute --permanent
```

### 3. 시스템 파일 자동 보호

다음과 같은 시스템 파일/디렉토리는 자동으로 보호됩니다:

**Windows:**
- `C:\Windows\`
- `C:\Program Files\`
- `System32`, `SysWOW64` 등 시스템 디렉토리
- 부트로더 파일 (`bootmgr`, `ntldr` 등)
- 페이징 파일 (`pagefile.sys`, `hiberfil.sys` 등)

**Linux/macOS:**
- `/bin`, `/sbin`, `/lib`, `/usr` 등 시스템 디렉토리
- `/boot`, `/proc`, `/sys`, `/dev` 등 특수 파일 시스템
- 설정 파일 (`.bashrc`, `.zshrc`, `.gitconfig` 등)

**사용자 민감 디렉토리:**
- `~/.ssh` (SSH 키)
- `~/.gnupg` (GPG 키)
- `~/.aws` (AWS 자격증명)
- `~/.config` (설정 파일)

### 4. 확인 프롬프트

파일 정리 전에 항상 확인 프롬프트가 나타납니다:

```bash
$ fclean clean ~/Downloads --older-than 30d --execute

Files to Delete
... (파일 목록)

trash 150 files (2.3 GB)?
```

확인 없이 진행하려면 `--yes` 플래그를 사용하세요:

```bash
fclean clean ~/Downloads --older-than 30d --execute --yes
```

## 일반적인 사용 예시

### 1. 오래된 다운로드 파일 정리

```bash
# 6개월 이상 된 파일 확인
fclean scan ~/Downloads --older-than 6m

# 파일 정리 (휴지통으로 이동)
fclean clean ~/Downloads --older-than 6m --execute
```

### 2. 큰 파일 정리

```bash
# 1GB 이상의 파일 찾기
fclean scan ~/ --larger-than 1GB

# 2GB 이상의 오래된 파일 정리
fclean clean ~/ --larger-than 2GB --older-than 30d --execute
```

### 3. 임시 파일 정리

```bash
# 임시 파일 패턴 확인
fclean scan ~/ --pattern "*.tmp" --pattern "*.temp" --pattern "*.log"

# 임시 파일 정리
fclean clean ~/ --pattern "*.tmp" --pattern "*.temp" --pattern "*.log" --execute
```

### 4. 중복 파일 찾기 및 정리

```bash
# 중복 파일 찾기
fclean duplicates ~/Downloads --min-size 1024

# 수동으로 선택하여 정리 (한 번에 하나씩)
fclean clean ~/Downloads --pattern "file1.txt" --execute
```

### 5. 시스템 정리 제안 확인

```bash
# 정리 가능한 시스템 디렉토리 확인
fclean suggest

# 캐시 디렉토리 정리 (예시)
fclean clean ~/.cache --older-than 30d --execute
```

### 6. 자동화 스크립트 (cron 작업)

```bash
#!/bin/bash
# 매주 정리 작업 스크립트

# 30일 이상 된 다운로드 파일 정리
fclean clean ~/Downloads --older-than 30d --execute --yes

# 임시 파일 정리
fclean clean /tmp --older-than 7d --execute --yes

# 500MB 이상의 로그 파일 정리
fclean clean ~/logs --pattern "*.log" --larger-than 500MB --execute --yes
```

이를 crontab에 추가하면 자동으로 정기적으로 정리됩니다:

```bash
# 매주 토요일 오전 2시에 실행
0 2 * * 6 bash /path/to/cleanup.sh
```

### 7. YAML 설정 파일로 복잡한 정리

```bash
# 설정 파일 작성
cat > cleanup.yaml << 'EOF'
rules:
  - name: "Downloads"
    paths:
      - "~/Downloads"
    older_than: "30d"

  - name: "Temp files"
    paths:
      - "/tmp"
      - "~/AppData/Local/Temp"
    older_than: "7d"

  - name: "Build artifacts"
    paths:
      - "~/Projects"
    extensions:
      - ".o"
      - ".pyc"
    older_than: "14d"
EOF

# 드라이런으로 미리보기
fclean clean --config cleanup.yaml

# 실제 정리 실행
fclean clean --config cleanup.yaml --execute --yes
```

## 명령어 옵션 요약

### 공통 옵션

| 옵션 | 설명 |
|------|------|
| `--version` | 버전 정보 표시 |
| `-v` | 버전 정보 표시 (약자) |

### 필터 옵션

| 옵션 | 약자 | 설명 |
|------|------|------|
| `--older-than` | `-o` | 지정한 기간보다 오래된 파일 |
| `--larger-than` | `-l` | 지정한 크기보다 큰 파일 |
| `--smaller-than` | `-s` | 지정한 크기보다 작은 파일 |
| `--pattern` | `-p` | 글롭 패턴 필터링 (반복 가능) |

### 정리 옵션

| 옵션 | 약자 | 설명 |
|------|------|------|
| `--execute` | `-x` | 실제 삭제 실행 |
| `--trash/--permanent` | | 휴지통 이동 또는 영구 삭제 |
| `--yes` | `-y` | 확인 프롬프트 제외 |
| `--config` | `-c` | YAML 설정 파일 |

### 기타 옵션

| 옵션 | 약자 | 설명 |
|------|------|------|
| `--skip-hidden` | | 숨김 파일/디렉토리 제외 |
| `--limit` | `-n` | 결과에서 보여줄 최대 파일 수 |
| `--min-size` | | 중복 탐지 최소 파일 크기 |

## 트러블슈팅

### Q: 파일이 정말 삭제되지 않나요?

A: `--execute` 플래그를 사용하지 않으면 드라이런 모드로 동작하여 실제 파일이 삭제되지 않습니다. 이는 의도된 안전 기능입니다.

### Q: 삭제한 파일을 복구할 수 있나요?

A: 기본적으로 파일은 휴지통으로 이동되므로 복구 가능합니다. `--permanent` 플래그를 사용하면 영구 삭제되어 복구 불가능합니다.

### Q: "Permission denied" 오류가 발생합니다.

A: 해당 디렉토리에 대한 읽기 권한이 필요합니다. `sudo`로 실행하거나 권한을 확인하세요.

### Q: 특정 파일은 정리 대상에서 제외하고 싶습니다.

A: YAML 설정 파일을 사용하여 구체적인 경로와 패턴을 지정할 수 있습니다. 시스템 파일은 자동으로 보호됩니다.

### Q: 큰 디렉토리 스캔이 느립니다.

A: `--limit` 옵션으로 결과 표시 수를 제한하거나, `--pattern` 옵션으로 범위를 좁혀보세요. 네트워크 드라이브는 로컬 스토리지보다 느릴 수 있습니다.

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다.

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트는 환영합니다.
