# -*- coding: utf-8 -*-
"""
Mini NPU Simulator
- 3x3 사용자 입력 모드
- data.json 분석 모드
- MAC(Multiply-Accumulate) 연산
- 라벨 정규화 및 epsilon 기반 동점 처리
- 성능 분석(평균 10회)
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

EPSILON = 1e-9
REPEAT_COUNT = 10
DATA_FILE = "data.json"

CROSS = "Cross"
X = "X"
UNDECIDED = "UNDECIDED"
PASS = "PASS"
FAIL = "FAIL"


# ---------------------------------------------------------------------------
# 데이터 구조: 2차원 패턴/필터
# ---------------------------------------------------------------------------
class Matrix:
    """n x n 2차원 숫자 행렬을 저장하고 접근하는 클래스"""

    def __init__(self, values: List[List[float]], name: str = "matrix") -> None:
        self.name = name

        if not values or not all(isinstance(row, list) for row in values):
            raise ValueError(f"{name}: 2차원 리스트 형식이어야 합니다.")

        row_count = len(values)
        col_count = len(values[0])

        if row_count == 0 or col_count == 0:
            raise ValueError(f"{name}: 빈 행렬은 사용할 수 없습니다.")

        for row_index, row in enumerate(values):
            if len(row) != col_count:
                raise ValueError(
                    f"{name}: {row_index + 1}번째 행의 열 개수가 일치하지 않습니다."
                )
            for value in row:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ValueError(f"{name}: 숫자가 아닌 값이 포함되어 있습니다.")

        self.values = values
        self.rows = row_count
        self.cols = col_count

    def get(self, row: int, col: int) -> float:
        """특정 위치의 값 읽기"""
        self._validate_index(row, col)
        return self.values[row][col]

    def set(self, row: int, col: int, value: float) -> None:
        """특정 위치에 값 저장"""
        self._validate_index(row, col)
        self.values[row][col] = value

    def _validate_index(self, row: int, col: int) -> None:
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            raise IndexError(
                f"{self.name}: 잘못된 위치입니다. ({row}, {col})"
            )

    def __str__(self) -> str:
        return "\n".join(
            " ".join(str(value) for value in row) for row in self.values
        )


# ---------------------------------------------------------------------------
# MAC 연산
# ---------------------------------------------------------------------------
def mac_score(pattern: Matrix, filter_matrix: Matrix) -> float:
    """
    입력 패턴과 필터를 위치별로 곱한 뒤 모두 더합니다.
    MAC = Multiply-Accumulate
    """
    if pattern.rows != filter_matrix.rows or pattern.cols != filter_matrix.cols:
        raise ValueError(
            f"MAC 연산 실패: 패턴 크기({pattern.rows}x{pattern.cols})와 "
            f"필터 크기({filter_matrix.rows}x{filter_matrix.cols})가 다릅니다."
        )

    score = 0.0

    for row in range(pattern.rows):
        for col in range(pattern.cols):
            score += pattern.get(row, col) * filter_matrix.get(row, col)

    return score


# ---------------------------------------------------------------------------
# 라벨 정규화
# ---------------------------------------------------------------------------
def normalize_label(raw_label: Any) -> Optional[str]:
    """
    다양한 표기를 표준 라벨 Cross 또는 X로 변환합니다.
    지원: '+', 'cross', 'Cross', 'CROSS' -> Cross
          'x', 'X', 'x_filter', 'X_FILTER' -> X
    """
    if not isinstance(raw_label, str):
        return None

    cleaned = raw_label.strip().lower()

    if cleaned in ("+", "cross"):
        return CROSS

    if cleaned in ("x", "x_filter"):
        return X

    return None


# ---------------------------------------------------------------------------
# 사용자 입력 처리
# ---------------------------------------------------------------------------
def read_matrix_from_console(
    size: int,
    title: str,
) -> Matrix:
    """콘솔에서 n x n 행렬을 한 줄씩 입력받습니다."""
    print(f"\n{title} ({size}줄 입력, 공백 구분)")

    while True:
        rows: List[List[float]] = []

        for row_index in range(size):
            raw = input(f"{row_index + 1}번째 줄: ").strip()

            if not raw:
                print("입력 형식 오류: 빈 줄은 입력할 수 없습니다. 처음부터 다시 입력하세요.")
                break

            tokens = raw.split()

            if len(tokens) != size:
                print(
                    f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요."
                )
                break

            try:
                row = [float(token) for token in tokens]
            except ValueError:
                print("입력 형식 오류: 숫자로 변환할 수 없는 값이 있습니다. 처음부터 다시 입력하세요.")
                break

            rows.append(row)

        if len(rows) == size:
            try:
                return Matrix(rows, title)
            except ValueError as error:
                print(f"입력 형식 오류: {error}")


# ---------------------------------------------------------------------------
# 모드 1: 사용자 입력 3x3
# ---------------------------------------------------------------------------
def run_user_input_mode() -> None:
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")

    filter_a = read_matrix_from_console(3, "필터 A")
    filter_b = read_matrix_from_console(3, "필터 B")

    print("\n#---------------------------------------")
    print("# 필터 저장 확인")
    print("#---------------------------------------")
    print("필터 A:")
    print(filter_a)
    print("\n필터 B:")
    print(filter_b)

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#----------------------------------------")
    pattern = read_matrix_from_console(3, "패턴")

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")

    score_a = mac_score(pattern, filter_a)
    score_b = mac_score(pattern, filter_b)

    start = time.perf_counter()
    for _ in range(REPEAT_COUNT):
        mac_score(pattern, filter_a)
        mac_score(pattern, filter_b)
    elapsed_ms = (time.perf_counter() - start) * 1000 / (REPEAT_COUNT * 2)

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT_COUNT}회): {elapsed_ms:.3f} ms")

    if abs(score_a - score_b) < EPSILON:
        print("판정: 판정 불가 (|A-B| < 1e-9)")
    elif score_a > score_b:
        print("판정: A")
    else:
        print("판정: B")

    print("\n#---------------------------------------")
    print("# [4] 성능 분석 (3x3)")
    print("#----------------------------------------")
    print_performance_table([3])


# ---------------------------------------------------------------------------
# 모드 2: JSON 분석
# ---------------------------------------------------------------------------
def load_json_data() -> Tuple[Dict[str, Any], List[str]]:
    """data.json을 로드하고 최상위 구조를 검사합니다."""
    errors: List[str] = []

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"{DATA_FILE} 파일을 찾을 수 없습니다. 실행 파일과 같은 폴더에 두세요."
        )

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"{DATA_FILE} JSON 파싱 오류: {error}") from error

    if not isinstance(data, dict):
        errors.append("최상위 JSON은 객체(dict)여야 합니다.")
        data = {}

    filters = data.get("filters")
    patterns = data.get("patterns")

    if not isinstance(filters, dict):
        errors.append("'filters' 키가 없거나 객체 형식이 아닙니다.")
        filters = {}

    if not isinstance(patterns, dict):
        errors.append("'patterns' 키가 없거나 객체 형식이 아닙니다.")
        patterns = {}

    return {"filters": filters, "patterns": patterns}, errors


def extract_filters(
    filters: Dict[str, Any],
) -> Tuple[Dict[int, Dict[str, Matrix]], List[str]]:
    """
    filters 데이터를 크기별 Cross/X 필터로 변환합니다.
    예: filters["size_5"]["cross"], filters["size_5"]["x"]
    """
    parsed: Dict[int, Dict[str, Matrix]] = {}
    errors: List[str] = []

    for key, value in filters.items():
        if not isinstance(key, str) or not key.startswith("size_"):
            errors.append(f"필터 키 '{key}'는 'size_N' 형식이어야 합니다.")
            continue

        try:
            size = int(key.replace("size_", ""))
        except ValueError:
            errors.append(f"필터 키 '{key}'에서 크기를 추출할 수 없습니다.")
            continue

        if not isinstance(value, dict):
            errors.append(f"필터 '{key}'의 값은 객체여야 합니다.")
            continue

        cross_raw = value.get("cross")
        x_raw = value.get("x")

        cross_label = normalize_label("cross")
        x_label = normalize_label("x")

        try:
            cross_matrix = Matrix(cross_raw, f"{key} Cross 필터")
            x_matrix = Matrix(x_raw, f"{key} X 필터")
        except (TypeError, ValueError) as error:
            errors.append(f"필터 '{key}' 로드 실패: {error}")
            continue

        if cross_matrix.rows != size or cross_matrix.cols != size:
            errors.append(
                f"필터 '{key}' Cross 크기 불일치: 기대 {size}x{size}, "
                f"실제 {cross_matrix.rows}x{cross_matrix.cols}"
            )
            continue

        if x_matrix.rows != size or x_matrix.cols != size:
            errors.append(
                f"필터 '{key}' X 크기 불일치: 기대 {size}x{size}, "
                f"실제 {x_matrix.rows}x{x_matrix.cols}"
            )
            continue

        parsed[size] = {
            cross_label: cross_matrix,
            x_label: x_matrix,
        }

    return parsed, errors


def analyze_pattern(
    case_id: str,
    pattern_data: Any,
    filters_by_size: Dict[int, Dict[str, Matrix]],
) -> Dict[str, Any]:
    """JSON 패턴 1개를 분석하고 PASS/FAIL 결과를 반환합니다."""
    result: Dict[str, Any] = {
        "case_id": case_id,
        "cross_score": None,
        "x_score": None,
        "verdict": UNDECIDED,
        "expected": None,
        "status": FAIL,
        "reason": "",
    }

    if not isinstance(pattern_data, dict):
        result["reason"] = "패턴 항목이 객체(dict) 형식이 아닙니다."
        return result

    input_data = pattern_data.get("input")
    expected_raw = pattern_data.get("expected")

    result["expected"] = normalize_label(expected_raw)

    if result["expected"] is None:
        result["reason"] = (
            f"expected 라벨 '{expected_raw}'을 Cross 또는 X로 정규화할 수 없습니다."
        )
        return result

    if not isinstance(input_data, list):
        result["reason"] = "'input' 값이 2차원 배열이 아닙니다."
        return result

    try:
        pattern = Matrix(input_data, f"{case_id} 패턴")
    except (TypeError, ValueError) as error:
        result["reason"] = f"패턴 생성 실패: {error}"
        return result

    size = pattern.rows

    if pattern.rows != pattern.cols:
        result["reason"] = (
            f"패턴은 정사각형이어야 합니다. 실제 크기: {pattern.rows}x{pattern.cols}"
        )
        return result

    size_filters = filters_by_size.get(size)

    if size_filters is None:
        result["reason"] = f"크기 {size}에 해당하는 필터가 없습니다."
        return result

    cross_filter = size_filters.get(CROSS)
    x_filter = size_filters.get(X)

    if cross_filter is None or x_filter is None:
        result["reason"] = f"크기 {size}의 Cross 또는 X 필터가 없습니다."
        return result

    if (
        pattern.rows != cross_filter.rows
        or pattern.cols != cross_filter.cols
        or pattern.rows != x_filter.rows
        or pattern.cols != x_filter.cols
    ):
        result["reason"] = (
            f"패턴 크기({pattern.rows}x{pattern.cols})와 필터 크기가 일치하지 않습니다."
        )
        return result

    try:
        cross_score = mac_score(pattern, cross_filter)
        x_score = mac_score(pattern, x_filter)
    except ValueError as error:
        result["reason"] = f"MAC 연산 실패: {error}"
        return result

    result["cross_score"] = cross_score
    result["x_score"] = x_score

    if abs(cross_score - x_score) < EPSILON:
        result["verdict"] = UNDECIDED
        result["reason"] = "동점 규칙: |Cross 점수 - X 점수| < 1e-9"
    elif cross_score > x_score:
        result["verdict"] = CROSS
    else:
        result["verdict"] = X

    if result["verdict"] == result["expected"]:
        result["status"] = PASS
    else:
        result["status"] = FAIL

    return result


def run_json_analysis_mode() -> None:
    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#----------------------------------------")

    try:
        data, top_level_errors = load_json_data()
    except (FileNotFoundError, ValueError) as error:
        print(f"데이터 로드 실패: {error}")
        print("data.json 분석을 종료합니다.")
        return

    filters_by_size, filter_errors = extract_filters(data["filters"])

    for size in sorted(filters_by_size):
        print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")

    for error in top_level_errors + filter_errors:
        print(f"⚠ {error}")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#----------------------------------------")

    results: List[Dict[str, Any]] = []

    for case_id, pattern_data in data["patterns"].items():
        result = analyze_pattern(case_id, pattern_data, filters_by_size)
        results.append(result)

        cross_score = result["cross_score"]
        x_score = result["x_score"]

        print(f"--- {case_id} ---")

        if cross_score is None or x_score is None:
            print(f"Cross 점수: N/A")
            print(f"X 점수: N/A")
            print(f"판정: {result['verdict']} | expected: {result['expected']} | {result['status']}")
            print(f"실패 사유: {result['reason']}")
        else:
            print(f"Cross 점수: {cross_score}")
            print(f"X 점수: {x_score}")
            print(
                f"판정: {result['verdict']} | "
                f"expected: {result['expected']} | {result['status']}"
            )

            if result["status"] == FAIL:
                print(f"실패 사유: {result['reason']}")

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#----------------------------------------")
    print_performance_table([3, 5, 13, 25])

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#----------------------------------------")

    total = len(results)
    passed = sum(1 for result in results if result["status"] == PASS)
    failed = total - passed

    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    failed_results = [result for result in results if result["status"] == FAIL]

    if failed_results:
        print("\n실패 케이스:")
        for result in failed_results:
            print(f"- {result['case_id']}: {result['reason'] or '판정 결과가 expected와 다릅니다.'}")
    else:
        print("\n실패 케이스가 없습니다.")
        print("라벨 정규화와 epsilon 기반 동점 처리가 정상 적용되었습니다.")


# ---------------------------------------------------------------------------
# 성능 분석
# ---------------------------------------------------------------------------
def create_cross_pattern(size: int) -> Matrix:
    """N x N 십자가 패턴을 생성합니다."""
    values = [[0.0 for _ in range(size)] for _ in range(size)]
    middle = size // 2

    for index in range(size):
        values[middle][index] = 1.0
        values[index][middle] = 1.0

    return Matrix(values, f"{size}x{size} Cross 패턴")


def create_x_pattern(size: int) -> Matrix:
    """N x N X 패턴을 생성합니다."""
    values = [[0.0 for _ in range(size)] for _ in range(size)]

    for index in range(size):
        values[index][index] = 1.0
        values[index][size - 1 - index] = 1.0

    return Matrix(values, f"{size}x{size} X 패턴")


def measure_mac_time(size: int) -> float:
    """크기 N의 Cross/X 패턴으로 MAC 연산을 10회씩 측정합니다."""
    cross_pattern = create_cross_pattern(size)
    x_pattern = create_x_pattern(size)

    cross_filter = create_cross_pattern(size)
    x_filter = create_x_pattern(size)

    start = time.perf_counter()

    for _ in range(REPEAT_COUNT):
        mac_score(cross_pattern, cross_filter)
        mac_score(x_pattern, x_filter)

    elapsed_ms = (time.perf_counter() - start) * 1000 / (REPEAT_COUNT * 2)
    return elapsed_ms


def print_performance_table(sizes: List[int]) -> None:
    print(f"{'크기':<10}{'평균 시간(ms)':>18}{'연산 횟수(N²)':>18}")
    print("-" * 46)

    for size in sizes:
        average_ms = measure_mac_time(size)
        operation_count = size * size
        print(f"{size}x{size:<7}{average_ms:>18.3f}{operation_count:>18}")


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------
def main() -> None:
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        choice = input("\n선택: ").strip()

        if choice == "1":
            run_user_input_mode()
            break

        if choice == "2":
            run_json_analysis_mode()
            break

        print("1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()