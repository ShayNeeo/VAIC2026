from threading import RLock
from typing import Dict, Optional
from datetime import datetime, timezone
from app.schemas.state import SharedCaseState

# Cơ sở dữ liệu In-Memory đơn giản giả lập cơ sở dữ liệu thật (như PostgreSQL hoặc MongoDB)
class SimpleDatabase:
    def __init__(self):
        self._cases: Dict[str, SharedCaseState] = {}
        self._lock = RLock()

    def save_case(self, case_state: SharedCaseState) -> None:
        case_state.updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._cases[case_state.case_id] = case_state.model_copy(deep=True)

    def get_case(self, case_id: str) -> Optional[SharedCaseState]:
        with self._lock:
            case = self._cases.get(case_id)
            return case.model_copy(deep=True) if case else None

    def list_cases(self) -> Dict[str, SharedCaseState]:
        with self._lock:
            return {key: value.model_copy(deep=True) for key, value in self._cases.items()}

    def clear(self) -> None:
        with self._lock:
            self._cases.clear()

# Khởi tạo instance toàn cục của Database
db = SimpleDatabase()
