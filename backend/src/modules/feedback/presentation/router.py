from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.infrastructure.configuration.settings import Settings
from src.modules.feedback.application.services import FeedbackService, FeedbackSubmissionError
from src.modules.feedback.infrastructure.repository import PostgresFeedbackRepository
from src.modules.feedback.infrastructure.smtp_mailer import SmtpFeedbackMailer

router = APIRouter(prefix="/api/v1/public", tags=["public feedback"])


class FeedbackRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    name: str | None = Field(default=None, max_length=180)
    contact: str | None = Field(default=None, max_length=320)
    honeypot: str = Field(default="", max_length=500)


def _service(request: Request) -> FeedbackService:
    application = getattr(request, "app", request)
    injected = getattr(application.state, "feedback_service", None)
    if injected is not None: return injected
    settings = Settings()
    return FeedbackService(PostgresFeedbackRepository(settings.database_url), SmtpFeedbackMailer(settings))


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(payload: FeedbackRequest, request: Request) -> JSONResponse:
    try:
        result = await _service(request).submit(**payload.dict())
    except FeedbackSubmissionError as error:
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"message": str(error)})
    if result.outcome == "delivery_failed":
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"message": "Feedback could not be delivered now. Please try again later."})
    if result.outcome == "already_received":
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"message": "Feedback was already received."})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Feedback received. Thank you."})
