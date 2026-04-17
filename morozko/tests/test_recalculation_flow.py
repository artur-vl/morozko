from morozko_bot.models import SessionData


def test_recalculation_counter_increments_on_confirmed_answer_change():
    session = SessionData(
        telegram_user_id=1,
        business_group="foodservice",
        answers={"Q1": "old_value"},
        recalculation_count=0,
        awaiting_question_code="Q1",
    )

    question_code = "Q1"
    option_code = "new_value"

    is_recalculation = session.awaiting_question_code == question_code
    session.answers[question_code] = option_code
    if is_recalculation:
        session.recalculation_count += 1
        session.awaiting_question_code = None

    assert session.answers["Q1"] == "new_value"
    assert session.recalculation_count == 1
    assert session.awaiting_question_code is None
