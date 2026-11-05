from copy import deepcopy

from test_automatic_calibration import observation

from football_pipeline.field_head_ensemble import choose_head_observation
from football_pipeline.field_motion import MOTION_RANK_SETTINGS


def test_teacher_valid_is_preserved_verbatim_even_when_student_disagrees():
    teacher, student = observation(), observation(inverse=[[400, 0, 70], [0, 250, 40], [0, 0, 1]])
    chosen, evidence = choose_head_observation(teacher, student, [640, 360], MOTION_RANK_SETTINGS)
    assert chosen is teacher
    assert evidence["selected"] == "teacher"


def test_missing_teacher_fit_requires_its_measured_peaks_to_agree():
    student = observation()
    teacher = deepcopy(student)
    teacher["points"] = teacher["points"][:2]
    teacher["lines"] = []
    before = deepcopy(teacher)
    chosen, evidence = choose_head_observation(teacher, student, [640, 360], MOTION_RANK_SETTINGS)
    assert evidence["selected"] == "student"
    assert chosen is not student
    assert chosen["head_ensemble"]["control_status"] == "teacher_peak_agreement"
    assert teacher == before
    teacher["points"][0]["y"] += 40
    rejected, evidence = choose_head_observation(teacher, student, [640, 360], MOTION_RANK_SETTINGS)
    assert rejected is teacher
    assert evidence["control_status"] == "teacher_disagreement"


def test_invalid_teacher_and_single_point_cannot_authorize_recovery():
    student = observation()
    for points in ([deepcopy(student["points"][0])], [dict(student["points"][0], x=-5)]):
        teacher = {**student, "points": points, "lines": []}
        chosen, evidence = choose_head_observation(teacher, student, [640, 360], MOTION_RANK_SETTINGS)
        assert chosen is teacher
        assert evidence["selected"] == "teacher"
