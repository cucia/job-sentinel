"""
Multi-Agent Application Wrapper

Provides integration between the multi-agent orchestrator and existing controller.
"""

import asyncio
from typing import Optional, Tuple

from src.ai.agents import create_orchestrator
from src.ai.task_context import create_task_context, TaskStatus
from src.core.browser import open_context, close_context
from src.core.logger import log


async def apply_with_agents(
    job: dict,
    profile: dict,
    settings: dict,
    platform: str
) -> Tuple[str, Optional[bool]]:
    """
    Apply to a job using multi-agent coordination with tracking.

    This function integrates the multi-agent system with the existing
    controller flow. It handles navigation, form detection, filling,
    and recovery automatically.

    Args:
        job: Job dictionary
        profile: Candidate profile
        settings: Application settings
        platform: Platform name (linkedin, indeed, etc.)

    Returns:
        Tuple of (status, easy_apply_flag)
        status: "applied", "skipped", "review", "failed"
        easy_apply_flag: True if easy apply was used
    """
    from src.ai.application_tracker import log_application
    from src.ai.human_behavior import create_human_behavior

    # Create task context
    task_context = create_task_context(job, platform)

    # Create orchestrator
    orchestrator = create_orchestrator(profile, settings)

    # Create human behavior controller
    human_behavior = create_human_behavior(settings)

    # Get headless setting
    headless = settings.get("app", {}).get("headless", True)

    # Open browser context
    playwright, browser, context = await open_context(headless=headless)

    try:
        page = await context.new_page()

        # Add human-like delay before starting
        await human_behavior.wait_for_page_interaction(page)

        # Execute application through orchestrator
        result = await orchestrator.execute_application(task_context, page)

        # Increment application counter
        human_behavior.increment_application_count()

        # Log application to tracker
        log_application(
            job_id=job.get("id", ""),
            job_key=job.get("job_key", ""),
            company=job.get("company", "Unknown"),
            title=job.get("title", "Unknown"),
            platform=platform,
            status=result.get("status", "unknown"),
            task_context=task_context.to_dict(),
            failure_reason=result.get("reason"),
            metadata={
                "verification": result.get("verification"),
                "needs_review": result.get("needs_review", False)
            }
        )

        attempted = bool(task_context.attempts)
        final_status = result.get("status", "unknown")
        failure_reason = result.get("reason") or result.get("message") or "none"
        mapped_status = "review"
        mapped_easy_apply = task_context.easy_apply_available if task_context.easy_apply_available is not None else None

        if result.get("success"):
            if result.get("needs_review") or final_status == "needs_review":
                mapped_status = "review"
            else:
                mapped_status = "applied"
        elif final_status == "failed":
            mapped_status = "failed" if not attempted else "review"
        elif final_status == "skipped":
            mapped_status = "skipped" if not attempted else "review"
        elif final_status == "review":
            mapped_status = "review"

        log(
            f"[MultiAgent] Final outcome for {job.get('title')}: "
            f"raw_status={final_status} mapped_status={mapped_status} attempted={attempted} "
            f"reason={failure_reason} retries={task_context.retry_count}"
        )

        # Add pause between applications
        await human_behavior.pause_between_applications()

        return (mapped_status, mapped_easy_apply)

    except Exception as exc:
        log(f"[MultiAgent] Application error: {exc}")
        task_context.add_error(str(exc))

        # Log failed application
        log_application(
            job_id=job.get("id", ""),
            job_key=job.get("job_key", ""),
            company=job.get("company", "Unknown"),
            title=job.get("title", "Unknown"),
            platform=platform,
            status="failed",
            task_context=task_context.to_dict(),
            failure_reason=str(exc)
        )

        return ("failed", None)

    finally:
        await close_context(playwright, browser, context)


def apply_with_agents_sync(
    job: dict,
    profile: dict,
    settings: dict,
    platform: str
) -> Tuple[str, Optional[bool]]:
    """
    Synchronous wrapper for apply_with_agents.

    This allows the multi-agent system to be called from
    synchronous controller code.
    """
    return asyncio.run(apply_with_agents(job, profile, settings, platform))


async def test_navigation_only(
    job: dict,
    profile: dict,
    settings: dict,
    platform: str
) -> dict:
    """
    Test navigation and form detection without applying.

    Useful for debugging and testing the multi-agent flow.
    """
    task_context = create_task_context(job, platform)
    orchestrator = create_orchestrator(profile, settings)

    headless = settings.get("app", {}).get("headless", True)
    playwright, browser, context = await open_context(headless=headless)

    try:
        page = await context.new_page()

        # Only navigate and detect
        nav_result = await orchestrator.navigator.handle_navigation(task_context, page)

        if nav_result.get("success"):
            form_result = await orchestrator.form_detector.detect_form(task_context, page)
            return {
                "navigation": nav_result,
                "form_detection": form_result,
                "task_context": task_context.to_dict()
            }
        else:
            return {
                "navigation": nav_result,
                "task_context": task_context.to_dict()
            }

    finally:
        await close_context(playwright, browser, context)
