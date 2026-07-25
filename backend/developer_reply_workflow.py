import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.database import DeveloperReply, PlayStoreReview
from backend.developer_reply_generator import DeveloperReplyGenerator

logger = logging.getLogger(__name__)

class ReplyWorkflowManager:
    """
    Developer Reply Approval & Publishing Workflow Manager.
    
    Statuses:
    - DRAFT: AI generated initial draft.
    - APPROVED: Approved by CX Agent / Product Lead.
    - PUBLISHED: Successfully pushed to Google Play Console API.
    - REJECTED: Rejected by agent.
    """

    @classmethod
    async def approve_reply(cls, db: AsyncSession, reply_id: int) -> Dict[str, Any]:
        """Marks a developer reply as APPROVED."""
        stmt = select(DeveloperReply).where(DeveloperReply.id == reply_id)
        res = await db.execute(stmt)
        reply = res.scalar_one_or_none()

        if not reply:
            return {"status": "error", "message": f"DeveloperReply with id {reply_id} not found."}

        reply.status = "APPROVED"
        await db.commit()
        await db.refresh(reply)

        logger.info(f"Approved DeveloperReply #{reply_id}")
        return {
            "status": "success",
            "reply_id": reply.id,
            "new_status": "APPROVED",
            "draft_reply_text": reply.draft_reply_text
        }

    @classmethod
    async def reject_reply(cls, db: AsyncSession, reply_id: int) -> Dict[str, Any]:
        """Marks a developer reply as REJECTED."""
        stmt = select(DeveloperReply).where(DeveloperReply.id == reply_id)
        res = await db.execute(stmt)
        reply = res.scalar_one_or_none()

        if not reply:
            return {"status": "error", "message": f"DeveloperReply with id {reply_id} not found."}

        reply.status = "REJECTED"
        await db.commit()
        await db.refresh(reply)

        logger.info(f"Rejected DeveloperReply #{reply_id}")
        return {
            "status": "success",
            "reply_id": reply.id,
            "new_status": "REJECTED"
        }

    @classmethod
    async def edit_reply(cls, db: AsyncSession, reply_id: int, new_text: str) -> Dict[str, Any]:
        """Edits the text of a developer reply draft, ensuring <= 350 chars."""
        clean_text = new_text.strip()
        if len(clean_text) > DeveloperReplyGenerator.MAX_CHAR_LIMIT:
            return {
                "status": "error",
                "message": f"Text exceeds maximum character limit of {DeveloperReplyGenerator.MAX_CHAR_LIMIT} chars (Provided: {len(clean_text)} chars)."
            }

        stmt = select(DeveloperReply).where(DeveloperReply.id == reply_id)
        res = await db.execute(stmt)
        reply = res.scalar_one_or_none()

        if not reply:
            return {"status": "error", "message": f"DeveloperReply with id {reply_id} not found."}

        reply.draft_reply_text = clean_text
        reply.status = "APPROVED"  # Auto-approve edited text
        await db.commit()
        await db.refresh(reply)

        logger.info(f"Edited & Approved DeveloperReply #{reply_id}")
        return {
            "status": "success",
            "reply_id": reply.id,
            "new_status": "APPROVED",
            "updated_text": reply.draft_reply_text,
            "char_count": len(reply.draft_reply_text)
        }

    @classmethod
    async def publish_reply(cls, db: AsyncSession, reply_id: int) -> Dict[str, Any]:
        """Simulates publishing approved reply to Google Play Store Console API."""
        stmt = select(DeveloperReply).where(DeveloperReply.id == reply_id)
        res = await db.execute(stmt)
        reply = res.scalar_one_or_none()

        if not reply:
            return {"status": "error", "message": f"DeveloperReply with id {reply_id} not found."}

        reply.status = "PUBLISHED"
        reply.published_reply_text = reply.draft_reply_text
        reply.published_at = datetime.datetime.utcnow()
        await db.commit()
        await db.refresh(reply)

        logger.info(f"Published DeveloperReply #{reply_id} to Google Play Console")
        return {
            "status": "success",
            "reply_id": reply.id,
            "new_status": "PUBLISHED",
            "published_reply_text": reply.published_reply_text,
            "published_at": reply.published_at.isoformat()
        }
