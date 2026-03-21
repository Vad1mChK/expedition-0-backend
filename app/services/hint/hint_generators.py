import random
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Union, Literal, Dict

from num2words import num2words

from app.services.hint.logic_models import LogicInterfaceType
from app.services.hint.logic_ops import TritUnOp, TritBinOp, NonBinOp
from app.services.hint.logic_solver_types import (
    LogicTaskSolverResult,
    LogicTaskSolverState,
    LogicNodeContent,
    LogicTaskSolverModification
)

HintText = namedtuple('HintText', ['unsanitized', 'sanitized'])
# Unsanitized text is used for returned text (e.g. to be displayed on screens)
# Sanitized text is passed to TTS (to ensure numbers and operators are pronounced correctly)


_OPERATOR_NAMES_RU: Dict[str, Dict[LogicNodeContent, str]] = {
    'n': {  # Nominative
        TritUnOp.IDENTITY: "тождество",
        TritUnOp.NOT: "инверсия",
        TritBinOp.AND: "конъюнкция",
        TritBinOp.OR: "дизъюнкция",
        TritBinOp.XOR: "исключающее ИЛИ",
        TritBinOp.IMPL_KLEENE: "импликация Клини",
        TritBinOp.IMPL_LUKASIEWICZ: "импликация Лукасевича",
        NonBinOp.NONARY_PLUS: "сложение",
        NonBinOp.NONARY_MINUS: "вычитание",
        NonBinOp.NONARY_CONCAT: "конкатенация"
    },
    'a': { # Accusative
        TritUnOp.NOT: "инверсию",
        TritBinOp.AND: "конъюнкцию",
        TritBinOp.OR: "дизъюнкцию",
        TritBinOp.IMPL_KLEENE: "импликацию Клини",
        TritBinOp.IMPL_LUKASIEWICZ: "импликацию Лукасевича",
        NonBinOp.NONARY_CONCAT: "конкатенацию"
    }
}


class HintTextGenerator(ABC):
    @abstractmethod
    def generate(
            self,
            logic_result: LogicTaskSolverResult,
            attempt_count: int = 0,
            mistake_count: int = 0,
            ternary_logic_balanced: bool = False,
            # Unbalanced: [0, 1, 2]; Balanced: [-1, 0, 1], it doesn't affect internal logic
    ) -> HintText:
        ...


class DeterministicHintTextGenerator(HintTextGenerator):
    @staticmethod
    def determine_quantity_of_number(number: int) -> Literal["singular", "dual", "plural"]:
        if number < 0:
            number = -number

        if (number % 10 == 0) or (number % 10 >= 5) or (10 < (number % 100) < 20):
            return "plural"
        if 2 <= (number % 10) <= 4:
            return "dual"
        return "singular"


    @staticmethod
    def _val_to_text(val: int, balanced: bool = False, case: str = 'n', gender: str = 'm') -> str:
        """Converts internal 0,1,2 to verbal representation based on balance."""
        actual_val = val
        if balanced:
            # Shift [0, 1, 2] -> [-1, 0, 1]
            actual_val = val - 1

        # num2words handles negative numbers (минус один)
        return num2words(actual_val, lang='ru', case=case, gender=gender, animate=False)

    def _format_mod(
            self,
            mod: LogicTaskSolverModification,
            sanitized: bool = False,
            balanced: bool = False
    ) -> str:
        """Creates a single instruction segment."""
        side_text = "левой" if mod.side == "left" else "правой"

        if mod.field == "val":
            if sanitized:
                old_val_text = self._val_to_text(mod.old_value, balanced, case='a')
                new_val_text = self._val_to_text(mod.new_value, balanced, case='a')
            else:
                old_val = mod.old_value
                new_val = mod.new_value

                if balanced:
                    old_val -= 1
                    new_val -= 1

                old_val_text = str(old_val)
                new_val_text = str(new_val)
            return f"на {side_text} консоли замените цифру {old_val_text} на {new_val_text}"

        if mod.field == "op":
            old_op_text = (
                _OPERATOR_NAMES_RU['a'].get(mod.old_value, None) or
                _OPERATOR_NAMES_RU['n'].get(mod.old_value, "неизвестный оператор")
            )
            new_op_text = (
                _OPERATOR_NAMES_RU['a'].get(mod.new_value, None) or
                _OPERATOR_NAMES_RU['n'].get(mod.new_value, "неизвестный оператор")
            )
            return f"на {side_text} консоли замените {old_op_text} на {new_op_text}"

        return "внесите изменения в задачу"

    def generate(
            self,
            logic_result: LogicTaskSolverResult,
            attempt_count: int = 0,
            mistake_count: int = 0,
            ternary_logic_balanced: bool = False
    ) -> HintText:
        if logic_result.state == LogicTaskSolverState.SOLVED:
            if attempt_count == 0:
                text = "Задачу уже решили до вас. Равенство уже верно."
            elif mistake_count == 0:
                text = "Задача решена без ошибок. Отличная работа, товарищ!"
            else:
                text = "Задача решена. Хорошая работа, товарищ!"
            return HintText(text, text)
        if logic_result.state == LogicTaskSolverState.UNSOLVABLE:
            text = random.choice([
                "Задача не имеет решения.",
                "Невозможно решить задачу.",
                "Правильного ответа нет."
            ])
            return HintText(text, text)
        if logic_result.state == LogicTaskSolverState.UNKNOWN_INCOMPLETE:
            text = random.choice([
                "Задача слишком сложная даже для меня.",
                "Неизвестно, можно ли решить задачу.",
                "Мне трудно ответить, может, у вас получится?"
            ])
            return HintText(text, text)
        if not logic_result.modifications:
            text = "Решение существует, но я его потерял, простите."
            return HintText(text, text)

        word_modification_quantities = {
            'singular': 'изменение',
            'dual': 'изменения',
            'plural': 'изменений'
        }

        modifications_len = len(logic_result.modifications)
        
        unsanitized_text = (
            f"Нужно {modifications_len} " +
            word_modification_quantities[self.determine_quantity_of_number(modifications_len)] +
            ": "
        )
        sanitized_text = (
            "Нужно " +
            self._val_to_text(modifications_len, case='a', gender='n') +
            " " +
            word_modification_quantities[self.determine_quantity_of_number(modifications_len)] +
            ": "
        )

        unsanitized_text += ', '.join(
            self._format_mod(mod, sanitized=False, balanced=ternary_logic_balanced)
            for mod in logic_result.modifications
        ) + '.'
        sanitized_text += ', '.join(
            self._format_mod(mod, sanitized=True, balanced=ternary_logic_balanced)
            for mod in logic_result.modifications
        ) + '.'

        return HintText(unsanitized_text, sanitized_text)
