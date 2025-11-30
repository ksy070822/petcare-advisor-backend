# 새 레포지토리 설정 가이드

## 목표
`petcare_advisor` 폴더를 루트로 하는 새 GitHub 레포지토리 생성 및 Railway 배포

## 단계별 가이드

### 1. GitHub에서 새 레포지토리 생성

1. https://github.com/new 접속
2. Repository name: `petcare-advisor-backend`
3. Description: `Multi-agent veterinary triage backend system`
4. Public 또는 Private 선택
5. **Initialize this repository with a README** 체크 해제 (이미 파일이 있으므로)
6. **Create repository** 클릭

### 2. 로컬에서 Git 초기화 및 푸시

```bash
cd ~/Desktop/해커톤/multi-agent/petcare_advisor

# Git 초기화 (이미 .git이 있으면 스킵)
git init

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: PetCare Advisor backend"

# GitHub 레포지토리 연결 (위에서 생성한 레포 URL 사용)
git remote add origin https://github.com/ksy070822/petcare-advisor-backend.git

# 메인 브랜치로 푸시
git branch -M main
git push -u origin main
```

### 3. Railway에서 새 프로젝트 생성

1. https://railway.app 접속
2. **New Project** → **Deploy from GitHub repo**
3. `petcare-advisor-backend` 레포지토리 선택
4. **Root Directory**: (비워두기 - 루트가 이미 `petcare_advisor`이므로)

### 4. Railway Settings 설정

#### Build Command
```
pip install -r requirements.txt
```

#### Start Command
```
PYTHONPATH=src python -m uvicorn petcare_advisor.main:app --host 0.0.0.0 --port $PORT
```

### 5. 환경 변수 설정

Variables 탭에서 추가:
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `API_HOST=0.0.0.0`
- `LOG_LEVEL=INFO`

### 6. 배포 확인

배포 완료 후:
```bash
curl https://your-app-name.up.railway.app/health
```

예상 응답:
```json
{"status":"healthy","service":"petcare-advisor"}
```

### 7. 프론트엔드 연결

프론트엔드 `.env` 파일에 추가:
```env
VITE_TRIAGE_API_BASE_URL=https://your-app-name.up.railway.app
```

또는 GitHub Secrets에 추가:
- Repository: `ksy070822/ai-factory`
- Settings → Secrets → `VITE_TRIAGE_API_BASE_URL`

