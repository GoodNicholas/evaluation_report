from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.core.config import settings
from app.core.redis import get_redis
from app.models.course import Course, Enrolment, EnrolmentStatus
from app.models.role import Role
from app.models.user import User
from app.schemas.telegram import TelegramBindToken

# Conversation states
WAITING_TOKEN = 1

# Rate limiting
GLOBAL_RATE_LIMIT = 100  # requests per minute
USER_RATE_LIMIT = 20  # requests per minute
TOKEN_TTL = 15 * 60  # 15 minutes in seconds


class TelegramBot:
    """Telegram bot service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up command handlers."""
        # Bind conversation
        bind_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self._start_command)],
            states={
                WAITING_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_token)],
            },
            fallbacks=[CommandHandler("cancel", self._cancel)],
        )
        self.application.add_handler(bind_handler)

        # Other commands
        self.application.add_handler(CommandHandler("pending", self._pending_command))
        self.application.add_handler(CommandHandler("summary", self._summary_command))
        self.application.add_handler(CommandHandler("mygrades", self._mygrades_command))
        self.application.add_handler(CommandHandler("deadlines", self._deadlines_command))

    async def _check_rate_limit(self, user_id: Optional[int] = None) -> bool:
        """Check rate limits."""
        redis = await get_redis()

        # Global rate limit
        global_key = "telegram:rate_limit:global"
        global_count = await redis.incr(global_key)
        if global_count == 1:
            await redis.expire(global_key, 60)
        if global_count > GLOBAL_RATE_LIMIT:
            return False

        # User rate limit
        if user_id:
            user_key = f"telegram:rate_limit:user:{user_id}"
            user_count = await redis.incr(user_key)
            if user_count == 1:
                await redis.expire(user_key, 60)
            if user_count > USER_RATE_LIMIT:
                return False

        return True

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command."""
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text("Rate limit exceeded. Please try again later.")
            return ConversationHandler.END

        await update.message.reply_text(
            "Welcome! To bind your Telegram account, please enter the token from your profile page."
        )
        return WAITING_TOKEN

    async def _handle_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle token input."""
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text("Rate limit exceeded. Please try again later.")
            return ConversationHandler.END

        token = update.message.text
        redis = await get_redis()

        # Get token data
        token_key = f"telegram:bind_token:{token}"
        token_data = await redis.get(token_key)
        if not token_data:
            await update.message.reply_text("Invalid or expired token. Please try again.")
            return ConversationHandler.END

        # Parse token data
        try:
            token_data = TelegramBindToken.parse_raw(token_data)
        except Exception:
            await update.message.reply_text("Invalid token format. Please try again.")
            return ConversationHandler.END

        # Check token TTL
        if datetime.utcnow() > token_data.expires_at:
            await update.message.reply_text("Token has expired. Please generate a new one.")
            return ConversationHandler.END

        # Get user
        stmt = select(User).where(User.id == token_data.user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("User not found. Please try again.")
            return ConversationHandler.END

        # Update user's Telegram ID
        user.telegram_id = update.effective_user.id
        await self.db.commit()

        # Delete used token
        await redis.delete(token_key)

        await update.message.reply_text(
            "Your Telegram account has been successfully bound to your profile!"
        )
        return ConversationHandler.END

    async def _cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END

    async def _pending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pending command."""
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text("Rate limit exceeded. Please try again later.")
            return

        # Get user
        stmt = select(User).where(User.telegram_id == update.effective_user.id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("Please bind your Telegram account first using /start.")
            return

        # Get pending assignments
        stmt = select(Course).join(Enrolment).where(
            Enrolment.user_id == user.id,
            Enrolment.status == EnrolmentStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        if not courses:
            await update.message.reply_text("You have no pending assignments.")
            return

        # Format response
        response = "Your pending assignments:\n\n"
        for course in courses:
            response += f"*{course.title}*\n"
            # TODO: Add actual pending assignments
            response += "No pending assignments\n\n"

        await update.message.reply_text(response, parse_mode="Markdown")

    async def _summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /summary command."""
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text("Rate limit exceeded. Please try again later.")
            return

        # Get user
        stmt = select(User).where(User.telegram_id == update.effective_user.id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("Please bind your Telegram account first using /start.")
            return

        # Get courses
        stmt = select(Course).join(Enrolment).where(
            Enrolment.user_id == user.id,
            Enrolment.status == EnrolmentStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        if not courses:
            await update.message.reply_text("You are not enrolled in any courses.")
            return

        # Format response
        response = "Your course summary:\n\n"
        for course in courses:
            response += f"*{course.title}*\n"
            # TODO: Add actual course summary
            response += "No data available\n\n"

        await update.message.reply_text(response, parse_mode="Markdown")

    async def _mygrades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /mygrades command."""
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text("Rate limit exceeded. Please try again later.")
            return

        # Get user
        stmt = select(User).where(User.telegram_id == update.effective_user.id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("Please bind your Telegram account first using /start.")
            return

        # Get courses
        stmt = select(Course).join(Enrolment).where(
            Enrolment.user_id == user.id,
            Enrolment.status == EnrolmentStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        if not courses:
            await update.message.reply_text("You are not enrolled in any courses.")
            return

        # Format response
        response = "Your grades:\n\n"
        for course in courses:
            response += f"*{course.title}*\n"
            # TODO: Add actual grades
            response += "No grades available\n\n"

        await update.message.reply_text(response, parse_mode="Markdown")

    async def _deadlines_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /deadlines command."""
        if not await self._check_rate_limit(update.effective_user.id):
            await update.message.reply_text("Rate limit exceeded. Please try again later.")
            return

        # Get user
        stmt = select(User).where(User.telegram_id == update.effective_user.id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            await update.message.reply_text("Please bind your Telegram account first using /start.")
            return

        # Get courses
        stmt = select(Course).join(Enrolment).where(
            Enrolment.user_id == user.id,
            Enrolment.status == EnrolmentStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        courses = result.scalars().all()

        if not courses:
            await update.message.reply_text("You are not enrolled in any courses.")
            return

        # Format response
        response = "Upcoming deadlines:\n\n"
        for course in courses:
            response += f"*{course.title}*\n"
            # TODO: Add actual deadlines
            response += "No upcoming deadlines\n\n"

        await update.message.reply_text(response, parse_mode="Markdown")

    async def start(self) -> None:
        """Start the bot."""
        await self.application.initialize()
        await self.application.start()
        await self.application.run_polling()

    async def stop(self) -> None:
        """Stop the bot."""
        await self.application.stop()
        await self.application.shutdown() 