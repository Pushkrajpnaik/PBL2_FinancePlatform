from fastapi import APIRouter, Depends, HTTPException
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
    return {
        "title": "Risk Profiling Questionnaire",
        "questions": [
            {"id": "financial_goal", "question": "What is your primary financial goal?", "options": {"1": "Preserve capital", "2": "Generate income", "3": "Grow wealth", "4": "Maximize returns aggressively"}},
            {"id": "time_horizon", "question": "How long do you plan to stay invested?", "options": {"1": "Less than 1 year", "2": "1-3 years", "3": "3-5 years", "4": "5-10 years", "5": "More than 10 years"}},
            {"id": "loss_reaction", "question": "If your portfolio dropped 20%, what would you do?", "options": {"1": "Sell everything", "2": "Sell some", "3": "Hold", "4": "Buy more"}},
            {"id": "income_stability", "question": "How stable is your income?", "options": {"1": "Very unstable", "2": "Somewhat stable", "3": "Stable", "4": "Very stable"}},
            {"id": "investment_experience", "question": "Your investment experience?", "options": {"1": "None", "2": "Beginner", "3": "Intermediate", "4": "Expert"}},
            {"id": "savings_rate", "question": "What % of income do you save?", "options": {"1": "Less than 10%", "2": "10-20%", "3": "20-30%", "4": "More than 30%"}},
            {"id": "emergency_fund", "question": "Do you have an emergency fund?", "options": {"1": "None", "2": "1-3 months", "3": "3-6 months", "4": "6+ months"}},
            {"id": "max_acceptable_loss", "question": "Maximum annual loss you can accept?", "options": {"1": "0-5%", "2": "5-10%", "3": "10-20%", "4": "20%+"}},
            {"id": "primary_motivation", "question": "What motivates you most?", "options": {"1": "Safety", "2": "Regular income", "3": "Wealth creation", "4": "High returns"}},
            {"id": "age_group", "question": "Your age group?", "options": {"1": "55+", "2": "45-55", "3": "35-45", "4": "25-35", "5": "Under 25"}}
        ]
    }

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
