from dataclasses import dataclass
from typing import Any

from conversation import ParseResult


@dataclass
class BubbleIntegrityResult:
    title: str
    composer_bubbles: int
    parsed: int
    skipped_empty: int
    missing: int
    is_valid: bool


class ConversationValidator:

    def conversation_statistics(
        self,
        conversation: dict[str, Any],
        empty_bubbles: int,
    ) -> str:
        messages = conversation["messages"]
        users = sum(1 for message in messages if message["role"] == "user")
        assistants = sum(1 for message in messages if message["role"] == "assistant")

        lines = [
            "Conversation",
            "--------------------------------",
            f"Title : {conversation['metadata']['title']}",
            "",
            f"Messages : {len(messages)}",
            "",
            f"User : {users}",
            "",
            f"Assistant : {assistants}",
            "",
            f"Empty : {empty_bubbles}",
        ]
        return "\n".join(lines)

    def check_bubble_integrity(
        self,
        composer: dict[str, Any],
        result: ParseResult,
    ) -> BubbleIntegrityResult:
        title = composer.get("name") or "Untitled"
        composer_bubbles = len(composer.get("fullConversationHeadersOnly") or [])
        parsed = len(result.conversation["messages"]) if result.conversation else 0
        skipped_empty = len(result.skipped_bubbles)
        missing = len(result.missing_bubbles)
        accounted_for = parsed + skipped_empty + missing

        return BubbleIntegrityResult(
            title=title,
            composer_bubbles=composer_bubbles,
            parsed=parsed,
            skipped_empty=skipped_empty,
            missing=missing,
            is_valid=composer_bubbles == accounted_for,
        )

    def format_bubble_integrity_issue(self, integrity: BubbleIntegrityResult) -> str:
        lines = [
            "Bubble Integrity Issue",
            "--------------------------------",
            f"Title : {integrity.title}",
            "",
            f"Composer bubbles : {integrity.composer_bubbles}",
            f"Parsed : {integrity.parsed}",
            f"Skipped empty : {integrity.skipped_empty}",
            f"Missing : {integrity.missing}",
            "",
            (
                f"Expected {integrity.composer_bubbles}, "
                f"got {integrity.parsed + integrity.skipped_empty + integrity.missing}"
            ),
        ]
        return "\n".join(lines)

    def recovery_summary(
        self,
        results: list[ParseResult],
    ) -> str:
        recovered_conversations = sum(1 for result in results if result.conversation)
        skipped_empty_conversations = sum(1 for result in results if not result.conversation)
        recovered_messages = sum(
            len(result.conversation["messages"])
            for result in results
            if result.conversation
        )
        missing_bubbles = sum(len(result.missing_bubbles) for result in results)
        empty_bubbles = sum(len(result.skipped_bubbles) for result in results)

        lines = [
            "Recovery Summary",
            "--------------------------------",
            f"Recovered Conversations : {recovered_conversations}",
            "",
            f"Skipped Empty Conversations : {skipped_empty_conversations}",
            "",
            f"Recovered Messages : {recovered_messages}",
            "",
            f"Missing Bubbles : {missing_bubbles}",
            "",
            f"Empty Bubbles : {empty_bubbles}",
        ]
        return "\n".join(lines)

    def print_report(
        self,
        composers: list[dict[str, Any]],
        results: list[ParseResult],
    ) -> None:
        for composer, result in zip(composers, results):
            if result.conversation is None:
                continue

            print(
                self.conversation_statistics(
                    result.conversation,
                    len(result.skipped_bubbles),
                )
            )
            print()

        integrity_issues = [
            self.check_bubble_integrity(composer, result)
            for composer, result in zip(composers, results)
        ]
        failed_integrity = [issue for issue in integrity_issues if not issue.is_valid]

        if failed_integrity:
            for issue in failed_integrity:
                print(self.format_bubble_integrity_issue(issue))
                print()

        print(self.recovery_summary(results))
