from functools import partial

import numpy as np

from .benchmark import benchmark
from .solver import Solver
from .views import AbstractRunView, BenchmarkView, HideView, SilentRunView, SolveView
from .words import Word, WordLoader


class RunController:
    def __init__(self, loader: WordLoader, solver: Solver, view: AbstractRunView) -> None:
        self.loader = loader
        self.solver = solver
        self.view = view

    def run(self, solution: Word, best_guess: Word) -> int:

        MAX_ITERS = 10

        all_words, available_answers = self.loader({str(solution), str(best_guess)})

        # # Random rubbish
        # sliced = all_words[8:20]
        # word6 = sliced.iloc[6]
        #
        # for word in sliced:
        #     print(word)

        for i in range(MAX_ITERS):
            histogram = self.solver.scorer.get_solutions_by_score(available_answers, best_guess)
            observed_score = self.solver.scorer.score_word(solution, best_guess)
            available_answers = histogram[observed_score]
            self.view.report_score(
                str(solution),
                str(best_guess),
                np.base_repr(observed_score, base=3),
                available_answers,
            )
            if best_guess == solution:
                return i + 1

            best_guess = self.solver.get_best_guess(available_answers, all_words).word

        raise LookupError(f"Failed to converge after {MAX_ITERS} iterations.")


class SolveController:
    def __init__(self, loader: WordLoader, solver: Solver, view: SolveView) -> None:
        self.loader = loader
        self.solver = solver
        self.view = view

    def solve(self, best_guess: str) -> None:

        all_words = self.loader.all_words
        available_answers = self.loader.common_words

        while True:
            (observed_score, best_guess) = self.view.get_user_score(best_guess)
            if self.solver.scorer.is_perfect_score(observed_score):
                self.view.report_success()
                break

            histogram = self.solver.scorer.get_solutions_by_score(available_answers, best_guess)
            available_answers = histogram[observed_score]

            if not available_answers:
                self.view.report_no_solution()
                break

            best_guess = self.solver.get_best_guess(available_answers, all_words).word
            self.view.report_best_guess(best_guess)


class HideController:
    def __init__(self, loader: WordLoader, solver: Solver, view: HideView) -> None:
        self.loader = loader
        self.solver = solver
        self.view = view

    def hide(self, guess: str) -> None:

        available_answers = self.loader.common_words

        guess = guess or self.view.get_user_guess()

        while True:

            solns_by_score = self.solver.scorer.get_solutions_by_score(available_answers, guess)

            def rank_score(score: int) -> int:
                solutions = solns_by_score[score]
                return 0 if guess in solutions else len(solutions)

            highest_score = max(solns_by_score, key=rank_score)
            available_answers = solns_by_score[highest_score]
            self.view.update(guess, highest_score, available_answers)

            if self.solver.scorer.is_perfect_score(highest_score):
                self.view.report_success()
                break

            guess = self.view.get_user_guess()


class BenchmarkController:
    def __init__(self, loader: WordLoader, solver: Solver, view: BenchmarkView) -> None:
        self.loader = loader
        self.solver = solver
        self.view = view

    def run(self, initial_guess: str) -> None:

        solutions = self.loader.common_words
        controller = RunController(self.loader, self.solver, SilentRunView())
        f = partial(controller.run, best_guess=initial_guess)

        histogram = benchmark(f, solutions)

        self.view.display(histogram)
