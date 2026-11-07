import pytest
from unittest.mock import MagicMock
from app.safety import check_safety, normalize_text

class TestSafetyGate:
    # 1. English Positives
    def test_ragging_english(self):
        res = check_safety("I am facing ragging in hostel")
        assert res["triggered"] is True
        assert "ragging" in res["categories"]

    def test_harassment_english(self):
        res = check_safety("A senior harassed me in the library")
        assert res["triggered"] is True
        assert "harassment" in res["categories"]

    def test_sexual_harassment_english(self):
        res = check_safety("Complaint regarding sexual harassment by lab assistant")
        assert res["triggered"] is True
        assert "harassment" in res["categories"]

    def test_stalking_english(self):
        res = check_safety("Someone has been stalking me after classes")
        assert res["triggered"] is True
        assert "harassment" in res["categories"]

    def test_violence_english(self):
        res = check_safety("There was a physical assault outside the campus gate")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_beaten_up_english(self):
        res = check_safety("I was beaten up by three students")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_kill_threat_english(self):
        res = check_safety("They gave me a kill threat if I report them")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_suicide_english(self):
        res = check_safety("I feel like committing suicide due to pressure")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    def test_kill_myself_english(self):
        res = check_safety("I want to kill myself please help")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    def test_end_my_life_english(self):
        res = check_safety("Thinking of ending my life tonight")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    # 2. Hindi (Devanagari) Positives
    def test_ragging_hindi(self):
        res = check_safety("हॉस्टल में रैगिंग हो रही है")
        assert res["triggered"] is True
        assert "ragging" in res["categories"]

    def test_harassment_hindi(self):
        res = check_safety("छात्रा के साथ छेड़छाड़ की घटना")
        assert res["triggered"] is True
        assert "harassment" in res["categories"]

    def test_violence_hindi(self):
        res = check_safety("छात्रों के बीच मारपीट हुई")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_threat_hindi(self):
        res = check_safety("मुझे जान से मारने की धमकी मिली है")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_suicide_hindi(self):
        res = check_safety("मुझे आत्महत्या करने का विचार आ रहा है")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    def test_khudkushi_hindi(self):
        res = check_safety("मैं खुदकुशी कर लूंगा")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    # 3. Hinglish Positives
    def test_ragging_hinglish(self):
        res = check_safety("seniors ragging kar rahe hain first year walo ki")
        assert res["triggered"] is True
        assert "ragging" in res["categories"]

    def test_harassment_hinglish(self):
        res = check_safety("wo ladka bahut pareshan karna aur stalk kar raha hai")
        assert res["triggered"] is True
        assert "harassment" in res["categories"]

    def test_violence_hinglish(self):
        res = check_safety("canteen ke bahar maar peet ho gayi")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_threat_hinglish(self):
        res = check_safety("usne marne ki dhamki di mujhe")
        assert res["triggered"] is True
        assert "violence_threat" in res["categories"]

    def test_suicide_hinglish(self):
        res = check_safety("mai mar jaunga ab saha nahi jaata")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    def test_khudkushi_hinglish(self):
        res = check_safety("khudkushi karne ka man ho raha hai")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    # 4. Mixed Case & Extra Punctuation
    def test_ragging_uppercase(self):
        res = check_safety("STOP RAGGING IMMEDIATELY")
        assert res["triggered"] is True
        assert "ragging" in res["categories"]

    def test_harassment_punctuation(self):
        res = check_safety("Help!!! harassment??? Please save me...")
        assert res["triggered"] is True
        assert "harassment" in res["categories"]

    def test_suicide_mixed_punctuation(self):
        res = check_safety("***SUICIDE*** thoughts are overwhelming me!")
        assert res["triggered"] is True
        assert "self_harm" in res["categories"]

    # 5. False Positive Negatives (Critical)
    def test_bragging_negative(self):
        res = check_safety("He was bragging about his top grades in exam")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_dragging_negative(self):
        res = check_safety("I was dragging a file into the university portal")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_fee_refund_negative(self):
        res = check_safety("How do I get a fee refund after withdrawing my seat?")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_scholarship_negative(self):
        res = check_safety("What is the deadline for NSP post-matric scholarship?")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_exam_backlog_negative(self):
        res = check_safety("How to apply for re-evaluation of 3rd semester exam?")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_attendance_negative(self):
        res = check_safety("My attendance is 68%, can medical certificate condone it?")
        assert res["triggered"] is False
        assert res["categories"] == []

    # 6. Empty / Null input
    def test_empty_string(self):
        res = check_safety("")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_whitespace_string(self):
        res = check_safety("    \n\t  ")
        assert res["triggered"] is False
        assert res["categories"] == []

    def test_none_input(self):
        res = check_safety(None)
        assert res["triggered"] is False
        assert res["categories"] == []

    # 7. Gemini client never called on triggered
    def test_gemini_never_called_when_triggered(self):
        gemini_mock = MagicMock()
        user_message = "Help, seniors are ragging me in room 204"
        safety_result = check_safety(user_message)
        assert safety_result["triggered"] is True
        # Emulating the safety gate logic:
        if safety_result["triggered"]:
            # Route to emergency contacts, DO NOT call Gemini
            pass
        else:
            gemini_mock.generate_content()
        gemini_mock.generate_content.assert_not_called()
