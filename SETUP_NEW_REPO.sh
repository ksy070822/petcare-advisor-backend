#!/bin/bash
# 새 GitHub 레포지토리 설정 스크립트

echo "🚀 PetCare Advisor Backend - 새 레포지토리 설정"
echo ""

# 현재 상태 확인
echo "📋 현재 Git 상태 확인..."
git status --short

echo ""
echo "⚠️  다음 단계를 진행하세요:"
echo ""
echo "1️⃣  GitHub에서 새 레포지토리 생성:"
echo "   - Repository name: petcare-advisor-backend"
echo "   - Public 또는 Private 선택"
echo "   - README 초기화 체크 해제"
echo ""
echo "2️⃣  레포지토리 생성 후 아래 명령 실행:"
echo ""
echo "   git remote set-url origin https://github.com/ksy070822/petcare-advisor-backend.git"
echo "   git push -u origin main"
echo ""
echo "3️⃣  Railway에서 새 프로젝트 생성:"
echo "   - Deploy from GitHub repo"
echo "   - petcare-advisor-backend 선택"
echo "   - Root Directory: (비워두기)"
echo ""
echo "4️⃣  Railway Settings:"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: PYTHONPATH=src python -m uvicorn petcare_advisor.main:app --host 0.0.0.0 --port \$PORT"
echo ""

