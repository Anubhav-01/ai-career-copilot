import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.schemas.common import MessageResponse
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationOut:
    return ApplicationOut.model_validate(ApplicationService(db).create(user, payload))


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ApplicationOut]:
    return [
        ApplicationOut.model_validate(a) for a in ApplicationService(db).list(user)
    ]


@router.put("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApplicationOut:
    return ApplicationOut.model_validate(
        ApplicationService(db).update(user, application_id, payload)
    )


@router.delete("/{application_id}", response_model=MessageResponse)
def delete_application(
    application_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    ApplicationService(db).delete(user, application_id)
    return MessageResponse(message="Application deleted.")
