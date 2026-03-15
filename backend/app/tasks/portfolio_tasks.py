from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.portfolio import Portfolio
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.portfolio_tasks.check_all_portfolio_drift")
def check_all_portfolio_drift():
    """
    Daily task — checks all portfolios for drift from target allocation.
    Triggers rebalancing if drift exceeds 5% threshold.
    """
    logger.info("Starting portfolio drift check...")
    db = SessionLocal()
    try:
        portfolios = db.query(Portfolio).filter(Portfolio.is_active == True).all()
        rebalanced = 0
        alerts     = []

        for portfolio in portfolios:
            if not portfolio.target_allocation or not portfolio.current_allocation:
                continue

            drift = calculate_drift(
                portfolio.target_allocation,
                portfolio.current_allocation
            )

            if drift > 5.0:
                rebalance_portfolio.delay(portfolio.id)
                rebalanced += 1
                alerts.append({
                    "portfolio_id": portfolio.id,
                    "drift":        drift,
                    "action":       "rebalancing triggered",
                })

        logger.info(f"Drift check complete. {len(portfolios)} portfolios checked, {rebalanced} rebalanced.")
        return {
            "portfolios_checked": len(portfolios),
            "rebalanced":         rebalanced,
            "alerts":             alerts,
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.portfolio_tasks.rebalance_portfolio")
def rebalance_portfolio(portfolio_id: int):
    """
    Rebalances a single portfolio back to target allocation.
    """
    logger.info(f"Rebalancing portfolio {portfolio_id}...")
    db = SessionLocal()
    try:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            return {"error": "Portfolio not found"}

        # Placeholder — in production this would execute actual trades
        portfolio.current_allocation = portfolio.target_allocation
        db.commit()

        logger.info(f"Portfolio {portfolio_id} rebalanced successfully.")
        return {
            "portfolio_id": portfolio_id,
            "status":       "rebalanced",
            "new_allocation": portfolio.target_allocation,
        }
    finally:
        db.close()


def calculate_drift(target: dict, current: dict) -> float:
    """
    Calculates maximum drift between target and current allocation.
    """
    max_drift = 0.0
    for asset, target_weight in target.items():
        current_weight = current.get(asset, 0)
        drift          = abs(target_weight - current_weight)
        max_drift      = max(max_drift, drift)
    return max_drift