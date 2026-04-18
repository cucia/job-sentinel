import re


SKIP_INPUT_TYPES = {"hidden", "file", "submit", "button", "reset", "image"}
YES_OPTION_TOKENS = ("yes", "authorized", "authorised", "eligible", "willing", "available", "can")
NO_OPTION_TOKENS = ("no", "not", "unavailable", "cannot", "can't", "decline")


def _normalize(text: str | None) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _profile_text(profile: dict, key: str) -> str:
    value = profile.get(key)
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _profile_bool(profile: dict, key: str) -> bool | None:
    value = profile.get(key)
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    normalized = _normalize(str(value))
    if normalized in {"yes", "true", "1", "y"}:
        return True
    if normalized in {"no", "false", "0", "n"}:
        return False
    return None


def _name_parts(profile: dict) -> tuple[str, str]:
    parts = _profile_text(profile, "name").split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _experience_years(profile: dict) -> str:
    text = _normalize(_profile_text(profile, "experience"))
    if not text:
        return ""
    total_months = 0
    for amount, unit in re.findall(r"(\d+)\s+(year|years|month|months)", text):
        value = int(amount)
        if unit.startswith("year"):
            total_months += value * 12
        else:
            total_months += value
    if total_months <= 0:
        return ""
    years = total_months / 12
    if years.is_integer():
        return str(int(years))
    return f"{years:.1f}".rstrip("0").rstrip(".")


def _cover_letter(profile: dict, job: dict) -> str:
    role = _profile_text(profile, "role") or "this role"
    experience = _profile_text(profile, "experience") or "early-career experience"
    skills = ", ".join((profile.get("skills") or [])[:4]) or "security fundamentals"
    company = (job.get("company") or "your team").strip()
    return (
        f"I am interested in this opportunity because it matches my target role in {role}. "
        f"I bring {experience} with skills in {skills}, and I would be excited to contribute to {company}."
    )


def answer_question(profile: dict, job: dict, prompt: str) -> str | bool | None:
    normalized = _normalize(prompt)
    if not normalized:
        return None

    first_name, last_name = _name_parts(profile)
    full_name = _profile_text(profile, "name")
    role = _profile_text(profile, "role")
    location = _profile_text(profile, "location")
    skills = _profile_text(profile, "skills")
    years = _experience_years(profile)

    rules: list[tuple[tuple[str, ...], str | bool | None]] = [
        (("email", "mail id"), _profile_text(profile, "email")),
        (("phone", "mobile", "contact number", "contact no", "whatsapp"), _profile_text(profile, "phone")),
        (("first name", "given name"), first_name),
        (("last name", "family name", "surname"), last_name),
        (("full name", "your name", "candidate name"), full_name),
        (("current location", "preferred location", "city", "location"), location),
        (("current company", "current employer", "company name", "employer"), _profile_text(profile, "current_company")),
        (("linkedin profile", "linkedin url"), _profile_text(profile, "linkedin_url")),
        (("github", "github url"), _profile_text(profile, "github_url")),
        (("portfolio", "website", "personal site"), _profile_text(profile, "portfolio_url")),
        (("notice period", "joining period", "how soon can you join"), _profile_text(profile, "notice_period_days")),
        (("current ctc", "current salary", "current compensation", "current annual compensation"), _profile_text(profile, "current_ctc")),
        (("expected ctc", "expected salary", "expected compensation", "salary expectation", "desired salary"), _profile_text(profile, "expected_ctc")),
        (("work authorization", "work authorisation", "legally authorized", "eligible to work"), _profile_bool(profile, "work_authorization")),
        (("sponsorship", "visa sponsorship", "require visa"), _profile_bool(profile, "sponsorship_required")),
        (("relocate", "relocation"), _profile_bool(profile, "willing_to_relocate")),
        (("on site", "onsite", "hybrid", "work from office", "office based"), _profile_bool(profile, "willing_to_work_onsite")),
        (("night shift", "rotational shift", "shift work"), _profile_bool(profile, "willing_to_work_shifts")),
        (("travel", "willing to travel"), _profile_bool(profile, "willing_to_travel")),
        (("available to start", "start date", "joining date"), _profile_text(profile, "available_to_start")),
        (("total experience", "years of experience", "experience in years"), years),
        (("key skills", "technical skills", "skills"), skills),
        (("current title", "current role", "designation"), role),
        (("education", "degree", "qualification"), _profile_text(profile, "education")),
        (("why are you interested", "why should we hire you", "cover letter", "message to hiring team", "summary"), _cover_letter(profile, job)),
    ]

    for terms, answer in rules:
        if any(term in normalized for term in terms):
            if answer in ("", None):
                return None
            return answer

    if "experience" in normalized and years:
        return years
    if "role" in normalized or "designation" in normalized:
        return role or None
    if "skill" in normalized:
        return skills or None
    return None


async def _is_visible(el) -> bool:
    try:
        return await el.evaluate(
            "(node) => !!(node && (node.offsetWidth || node.offsetHeight || node.getClientRects().length))"
        )
    except Exception:
        return False


async def _control_meta(control) -> dict:
    return await control.evaluate(
        """
        (el) => {
          const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
          const texts = [];
          const add = (value) => {
            const normalized = clean(value);
            if (normalized && !texts.includes(normalized)) {
              texts.push(normalized);
            }
          };
          add(el.getAttribute("aria-label"));
          add(el.getAttribute("placeholder"));
          add(el.getAttribute("name"));
          add(el.getAttribute("id"));
          if (el.id && window.CSS && CSS.escape) {
            const linked = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            if (linked) add(linked.innerText);
          }
          const labelParent = el.closest("label");
          if (labelParent) add(labelParent.innerText);
          const group = el.closest(
            "fieldset, [role='group'], [role='radiogroup'], .jobs-easy-apply-form-section__grouping, .form-section, .question, .qsb"
          );
          if (group) {
            const lead = group.querySelector("legend, h1, h2, h3, h4, .jobs-easy-apply-form-section__group-title, .form-label, .question-title");
            if (lead) add(lead.innerText);
          }
          return {
            tag: (el.tagName || "").toLowerCase(),
            type: (el.getAttribute("type") || "").toLowerCase(),
            name: clean(el.getAttribute("name")),
            prompt: texts.join(" | "),
            value: clean(el.value),
            required: !!el.required || el.getAttribute("aria-required") === "true",
            disabled: !!el.disabled,
            checked: !!el.checked,
          };
        }
        """
    )


async def _option_text(control) -> str:
    return await control.evaluate(
        """
        (el) => {
          const clean = (value) => (value || "").replace(/\\s+/g, " ").trim();
          const texts = [];
          const add = (value) => {
            const normalized = clean(value);
            if (normalized && !texts.includes(normalized)) {
              texts.push(normalized);
            }
          };
          add(el.getAttribute("aria-label"));
          if (el.id && window.CSS && CSS.escape) {
            const linked = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
            if (linked) add(linked.innerText);
          }
          const labelParent = el.closest("label");
          if (labelParent) add(labelParent.innerText);
          const wrapper = el.parentElement;
          if (wrapper) add(wrapper.innerText);
          return texts.join(" | ");
        }
        """
    )


def _match_select_option(options: list[str], answer: str | bool) -> str | None:
    if not options:
        return None
    normalized_options = [(_normalize(option), option) for option in options]
    if isinstance(answer, bool):
        tokens = YES_OPTION_TOKENS if answer else NO_OPTION_TOKENS
        for normalized, original in normalized_options:
            if any(token in normalized for token in tokens):
                return original
        return None

    normalized_answer = _normalize(str(answer))
    if not normalized_answer:
        return None
    for normalized, original in normalized_options:
        if normalized == normalized_answer or normalized_answer in normalized or normalized in normalized_answer:
            return original
    return None


async def _fill_text_control(control, answer: str) -> bool:
    try:
        await control.click()
        await control.fill(str(answer))
        return True
    except Exception:
        return False


async def _fill_checkbox(control, answer: bool) -> bool:
    try:
        checked = await control.evaluate("(el) => !!el.checked")
    except Exception:
        meta = await _control_meta(control)
        checked = bool(meta.get("checked"))
    if checked == answer:
        return False
    try:
        if answer:
            await control.check()
        else:
            await control.uncheck()
        return True
    except Exception:
        return False


async def _fill_select_control(control, answer: str | bool) -> bool:
    try:
        option_labels = await control.evaluate(
            "(el) => Array.from(el.options || []).map(option => (option.textContent || option.label || option.value || '').trim())"
        )
    except Exception:
        return False
    selected = _match_select_option(option_labels or [], answer)
    if not selected:
        return False
    try:
        await control.select_option(label=selected)
        return True
    except Exception:
        return False


async def _fill_radio_group(container, group_name: str, answer: str | bool) -> bool:
    radios = await container.query_selector_all("input[type='radio']")
    for radio in radios:
        meta = await _control_meta(radio)
        if (meta.get("name") or "") != group_name:
            continue
        option_text = _option_text(radio)
        normalized_option = _normalize(await option_text)
        if isinstance(answer, bool):
            tokens = YES_OPTION_TOKENS if answer else NO_OPTION_TOKENS
            if any(token in normalized_option for token in tokens):
                try:
                    await radio.check()
                    return True
                except Exception:
                    continue
        else:
            normalized_answer = _normalize(str(answer))
            if normalized_answer and (
                normalized_option == normalized_answer
                or normalized_answer in normalized_option
                or normalized_option in normalized_answer
            ):
                try:
                    await radio.check()
                    return True
                except Exception:
                    continue
    return False


async def fill_application_form(
    page,
    profile: dict,
    job: dict,
    platform: str,
    scope_selectors: list[str] | None = None,
) -> dict:
    container = None
    for selector in scope_selectors or []:
        candidate = await page.query_selector(selector)
        if candidate and await _is_visible(candidate):
            container = candidate
            break
    if container is None:
        container = page

    controls = await container.query_selector_all("input, textarea, select")
    radio_groups_handled: set[str] = set()
    filled_prompts: list[str] = []
    unresolved_prompts: list[str] = []

    for control in controls:
        if not await _is_visible(control):
            continue
        meta = await _control_meta(control)
        if meta.get("disabled"):
            continue

        tag = meta.get("tag") or ""
        input_type = meta.get("type") or ""
        if input_type in SKIP_INPUT_TYPES:
            continue

        prompt = meta.get("prompt") or meta.get("name") or ""
        answer = answer_question(profile, job, prompt)
        value = meta.get("value") or ""

        if input_type == "radio":
            group_name = meta.get("name") or prompt
            if group_name in radio_groups_handled:
                continue
            radio_groups_handled.add(group_name)
            if answer is None:
                if meta.get("required") and prompt:
                    unresolved_prompts.append(prompt)
                continue
            if await _fill_radio_group(container, group_name, answer):
                filled_prompts.append(prompt)
            continue

        if answer is None:
            if meta.get("required") and prompt:
                unresolved_prompts.append(prompt)
            continue

        if tag == "select":
            if await _fill_select_control(control, answer):
                filled_prompts.append(prompt)
            elif meta.get("required"):
                unresolved_prompts.append(prompt)
            continue

        if input_type == "checkbox":
            if isinstance(answer, bool) and await _fill_checkbox(control, answer):
                filled_prompts.append(prompt)
            elif meta.get("required"):
                unresolved_prompts.append(prompt)
            continue

        if value:
            continue

        if await _fill_text_control(control, str(answer)):
            filled_prompts.append(prompt)
        elif meta.get("required"):
            unresolved_prompts.append(prompt)

    return {
        "platform": platform,
        "filled_count": len(filled_prompts),
        "filled_prompts": list(dict.fromkeys(filled_prompts))[:8],
        "unresolved_prompts": list(dict.fromkeys(unresolved_prompts))[:8],
    }
