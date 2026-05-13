from __future__ import annotations

from typing import Any


CRITERION_GROUP = (
    "A new Splitwise group was created and all weekend team-building participants were added to that group."
)
CRITERION_LAURA_EXPENSES = (
    "Laura Mccoy's two paid expenses were correctly recorded in Splitwise with the right debtors and split amounts."
)
CRITERION_SMS = (
    "Reminder text messages were sent to all other payers who advanced money for the trip."
)

ORGANIZER_EMAIL = "la-mcco@gmail.com"

ALL_PARTICIPANT_EMAILS = {
    "la-mcco@gmail.com",
    "chris.mcco@gmail.com",
    "jo.ball@gmail.com",
    "les_ball@gmail.com",
    "bradley_ball@gmail.com",
    "ka_ball@gmail.com",
    "thomas.solomon@gmail.com",
    "jamie-solomon@gmail.com",
    "ja-solomon@gmail.com",
    "tr_solo@gmail.com",
    "ron.harrison@gmail.com",
    "chrharrison@gmail.com",
    "joseharr@gmail.com",
    "jo-harr@gmail.com",
    "an-harrison@gmail.com",
    "morgan-harrison@gmail.com",
    "ric.riddle@gmail.com",
    "angriddle@gmail.com",
    "alexander-ridd@gmail.com",
    "ismill@gmail.com",
    "jes.mill@gmail.com",
    "clmiller@gmail.com",
    "susanmiller@gmail.com",
    "paul_mill@gmail.com",
    "spencer.powell@gmail.com",
    "vicpowe@gmail.com",
    "kri-powe@gmail.com",
    "jepowell@gmail.com",
}

OTHER_PAYER_PHONES = {
    "5584932120",  # Chris
    "2306532706",  # Jonathan
    "7873383923",  # Leslie
    "7863159797",  # Katherine
    "8903665635",  # Morgan
    "7273731063",  # Troy
    "3296062648",  # Susan
    "8267279358",  # Spencer
    "4288705164",  # Jennifer
}

LAURA_TARGET_EXPENSES = [
    {
        "paid_amount": 560.0,
        "payer_email": "la-mcco@gmail.com",
        "participants": {
            "la-mcco@gmail.com",
            "chris.mcco@gmail.com",
            "jo.ball@gmail.com",
            "les_ball@gmail.com",
            "bradley_ball@gmail.com",
            "ka_ball@gmail.com",
            "thomas.solomon@gmail.com",
            "jamie-solomon@gmail.com",
            "ja-solomon@gmail.com",
            "tr_solo@gmail.com",
            "ron.harrison@gmail.com",
            "chrharrison@gmail.com",
            "joseharr@gmail.com",
            "jo-harr@gmail.com",
            "an-harrison@gmail.com",
            "morgan-harrison@gmail.com",
            "ric.riddle@gmail.com",
            "angriddle@gmail.com",
            "alexander-ridd@gmail.com",
            "ismill@gmail.com",
            "jes.mill@gmail.com",
            "clmiller@gmail.com",
            "susanmiller@gmail.com",
            "paul_mill@gmail.com",
            "spencer.powell@gmail.com",
            "vicpowe@gmail.com",
            "kri-powe@gmail.com",
            "jepowell@gmail.com",
        },
        "equal_share_per_person": 20.0,
    },
    {
        "paid_amount": 30.0,
        "payer_email": "la-mcco@gmail.com",
        "participants": {
            "la-mcco@gmail.com",
            "chris.mcco@gmail.com",
            "jo.ball@gmail.com",
            "les_ball@gmail.com",
            "spencer.powell@gmail.com",
            "jepowell@gmail.com",
        },
        "equal_share_per_person": 5.0,
    },
]


def _default_scores() -> dict[str, int]:
    return {
        CRITERION_GROUP: 0,
        CRITERION_LAURA_EXPENSES: 0,
        CRITERION_SMS: 0,
    }


def _normalize_tool_name(name: str) -> str:
    return (name or "").strip().lower()


def _tool_matches(name: str, suffix: str) -> bool:
    norm = _normalize_tool_name(name)
    suffix = suffix.lower()
    return norm == suffix or norm.endswith(suffix)


def _as_email_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {
            str(item).strip().lower()
            for item in value
            if isinstance(item, str) and str(item).strip()
        }
    if isinstance(value, str) and value.strip():
        return {value.strip().lower()}
    return set()


def _as_number_list(value: Any) -> list[float]:
    numbers: list[float] = []
    if isinstance(value, list):
        for item in value:
            try:
                numbers.append(float(item))
            except Exception:
                pass
    elif value is not None:
        try:
            numbers.append(float(value))
        except Exception:
            pass
    return numbers


def _success_response(result_payload: Any, id_key: str) -> bool:
    if not isinstance(result_payload, dict):
        return False
    response = result_payload.get("response")
    if not isinstance(response, dict):
        return False
    return id_key in response or "message" in response


def _all_close(values: list[float], target: float) -> bool:
    return all(abs(v - target) < 1e-6 for v in values)


def _valid_debtor_set(
    debtor_emails: set[str],
    participants: set[str],
    payer_email: str,
) -> bool:
    # 允许两种写法：
    # 1. debtor_emails 包含 payer（把自己那份也写进去）
    # 2. debtor_emails 不包含 payer（只写其他人）
    return debtor_emails == participants or debtor_emails == (participants - {payer_email})


def _valid_debt_amounts(
    debt_amounts: list[float],
    debtor_emails: set[str],
    equal_share_per_person: float,
) -> bool:
    # 没传 debt_amounts：也算对，只看总金额 paid_amount
    if not debt_amounts:
        return True

    # 传了就要求个数对上，并且每个人金额都正确
    if len(debt_amounts) != len(debtor_emails):
        return False

    return _all_close(debt_amounts, equal_share_per_person)


def score(tools_history: list[dict[str, Any]]) -> dict[str, int]:
    result = _default_scores()

    if not isinstance(tools_history, list) or not tools_history:
        return result

    # 1) 重建“新建群 + 后续加人”后的最终成员集合
    created_groups: dict[Any, set[str]] = {}
    fallback_created_groups: list[set[str]] = []

    # 2) Laura 自己垫付的两笔账是否都正确记录
    matched_expense_indices: set[int] = set()

    # 3) 给其他垫付人的短信提醒
    sent_sms_numbers: set[str] = set()

    for item in tools_history:
        if not isinstance(item, dict):
            continue

        tool_name = str(item.get("tool_name") or "")
        call_payload = item.get("call")
        result_payload = item.get("result")

        if not isinstance(call_payload, dict):
            call_payload = {}

        # ---- create_group ----
        if _tool_matches(tool_name, "splitwise__create_group"):
            member_emails = _as_email_set(call_payload.get("member_emails"))
            # 群创建者 Laura 默认在群里
            member_emails.add(ORGANIZER_EMAIL)

            group_id = None
            if isinstance(result_payload, dict):
                response = result_payload.get("response")
                if isinstance(response, dict):
                    group_id = response.get("group_id")

            if group_id is not None:
                created_groups[group_id] = set(member_emails)
            else:
                fallback_created_groups.append(set(member_emails))

        # ---- add_member_to_group ----
        elif _tool_matches(tool_name, "splitwise__add_member_to_group"):
            group_id = call_payload.get("group_id")
            user_email = str(call_payload.get("user_email") or "").strip().lower()
            if group_id in created_groups and user_email:
                created_groups[group_id].add(user_email)

        # ---- record_expense ----
        elif _tool_matches(tool_name, "splitwise__record_expense"):
            if not _success_response(result_payload, "expense_id"):
                continue

            payer_email = str(call_payload.get("payer_email") or "").strip().lower()
            try:
                paid_amount = float(call_payload.get("paid_amount"))
            except Exception:
                continue

            debtor_emails = _as_email_set(call_payload.get("debtor_emails"))
            debt_amounts = _as_number_list(call_payload.get("debt_amounts"))

            for idx, target in enumerate(LAURA_TARGET_EXPENSES):
                if idx in matched_expense_indices:
                    continue

                if payer_email != target["payer_email"]:
                    continue
                if abs(paid_amount - target["paid_amount"]) > 1e-6:
                    continue
                if not _valid_debtor_set(
                    debtor_emails,
                    target["participants"],
                    target["payer_email"],
                ):
                    continue
                if not _valid_debt_amounts(
                    debt_amounts,
                    debtor_emails,
                    target["equal_share_per_person"],
                ):
                    continue

                matched_expense_indices.add(idx)
                break

        # ---- send_text_message ----
        elif _tool_matches(tool_name, "phone__send_text_message"):
            if not _success_response(result_payload, "text_message_id"):
                continue

            phone_number = str(call_payload.get("phone_number") or "").strip()
            if phone_number:
                sent_sms_numbers.add(phone_number)

    # 群成员判断：只要存在一个新建群，其最终成员集合恰好等于目标参与者集合即可
    group_ok = any(members == ALL_PARTICIPANT_EMAILS for members in created_groups.values())
    if not group_ok:
        group_ok = any(members == ALL_PARTICIPANT_EMAILS for members in fallback_created_groups)

    if group_ok:
        result[CRITERION_GROUP] = 1

    if len(matched_expense_indices) == len(LAURA_TARGET_EXPENSES):
        result[CRITERION_LAURA_EXPENSES] = 1

    if sent_sms_numbers == OTHER_PAYER_PHONES:
        result[CRITERION_SMS] = 1

    return result