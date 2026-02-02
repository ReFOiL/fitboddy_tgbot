from __future__ import annotations

from collections import defaultdict

from src.domain.entities.user import User
from src.domain.entities.user_answer import UserAnswer
from src.presentation.web_admin.user_schemas import AnswerGroupOut, OptionOut, UserDetailOut, UserOut


class UserPresenter:
    def to_out(self, user: User) -> UserOut:
        return UserOut(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            created_at=user.created_at,
            has_completed_profile=user.has_completed_profile,
            profile_completed_at=user.profile_completed_at,
        )

    def to_detail_out(self, user: User, answers: list[UserAnswer]) -> UserDetailOut:
        grouped: dict[int, list[UserAnswer]] = defaultdict(list)
        for ans in answers:
            if ans.question is None:
                continue
            grouped[ans.question.id].append(ans)
        order_by_qid: dict[int, int] = {
            qid: int(getattr(items[0].question, "order", 0) or 0)
            for qid, items in grouped.items()
            if items and items[0].question is not None
        }

        answer_groups: list[AnswerGroupOut] = []
        for question_id, items in grouped.items():
            q = items[0].question
            if q is None:
                continue
            # Prefer option-based representation if any option rows exist
            options = [
                OptionOut(value=item.option.value, label=item.option.label)
                for item in items
                if item.option is not None
            ]
            value = None
            if not options:
                # scalar stored in UserAnswer.value
                value = items[0].value
            answered_at = min((i.answered_at for i in items), default=None)
            updated_at = max((i.updated_at for i in items), default=None)
            answer_groups.append(
                AnswerGroupOut(
                    question_id=q.id,
                    question_key=q.key,
                    question_text=q.text,
                    answer_type=str(q.answer_type),
                    options=options or None,
                    value=value,
                    answered_at=answered_at,
                    updated_at=updated_at,
                )
            )

        # Prefer questionnaire order (system + custom), fallback to id
        answer_groups.sort(
            key=lambda a: (
                order_by_qid.get(a.question_id, 0) or 10**9,
                a.question_id,
            )
        )

        base = self.to_out(user)
        return UserDetailOut(**base.model_dump(), answers=answer_groups)

