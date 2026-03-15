content = """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.models.risk_profile import RiskProfile
from app.schemas.risk_profile import RiskProfileAnswers, RiskProfileResult
from app.services.risk_service import save_risk_profile, get_risk_result

router = APIRouter()

@router.get("/questionnaire")
def get_questionnaire():
    return {"title": "Risk Profiling Questionnaire", "questions": []}

@router.post("/assess", response_model=RiskProfileResult)
def assess_risk(answers: RiskProfileAnswers, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    profile = save_risk_profile(db, current_user.id, answers)
    return get_risk_result(profile.score, profile.profile_type)

@router.get("/me", response_model=RiskProfileResult)
def get_my_risk_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    profile = db.query(RiskProfile).filter(RiskProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No risk profile found.")
    return get_risk_result(profile.score, profile.profile_type)
"""

with open("backend/app/api/routes/risk_profile.py", "w") as f:
    f.write(content)
print("Done!")
