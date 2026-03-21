import random
from abc import ABC, abstractmethod
from typing import Union

from app.services.hint.logic_solver_types import LogicTaskSolverResult, LogicTaskSolverState, LogicNodeContent


class HintGenerator(ABC):
    @abstractmethod
    def generate(
            self,
            logic_result: LogicTaskSolverResult,
            attempt_count: int,
            mistake_count: int
    ) -> str:
        ...


class DeterministicHintGenerator(HintGenerator):
    @staticmethod
    def content_to_string(operator: LogicNodeContent) -> str:
        # For numbers, perhaps use library num2words (if it's lightweight enough)
        # i know it has cardinals, ordinals, and cases
        ...

    def generate(
            self,
            logic_result: LogicTaskSolverResult,
            attempt_count: int,
            mistake_count: int
    ) -> str:
        if logic_result.state == LogicTaskSolverState.SOLVED:
            if attempt_count == 0:
                return "Задачу уже решили до вас. Равенство уже верно."
            if mistake_count == 0:
                return "Задача решена без ошибок. Отличная работа, товарищ!"
            return "Задача решена. Хорошая работа, товарищ!"
        if logic_result.state == LogicTaskSolverState.UNSOLVABLE:
            return random.choice([
                "Задача не имеет решения.",
                "Невозможно решить задачу.",
                "Правильного ответа нет."
            ])
        if logic_result.state == LogicTaskSolverState.UNKNOWN_INCOMPLETE:
            return random.choice([
                "Задача слишком сложная даже для меня.",
                "Неизвестно, можно ли решить задачу.",
                "Мне трудно ответить, может, у вас получится?"
            ])
        ...
