from fastapi import APIRouter

router: APIRouter = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return the service liveness status."""
    return {"status": "healthy"}

