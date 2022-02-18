from typing import Sequence

from .histogram import HistogramBuilder
from .scoring import Scorer
from .simulation import Benchmarker, Simulator
from .solver import (
    DeepEntropySolver,
    DeepMinimaxSolver,
    EntropySolver,
    MinimaxSolver,
    Solver,
    SolverType,
)
from .views import BenchmarkView, NullRunView, RunView
from .words import Word, WordSeries, load_dictionary


def create_simulator(
    size: int,
    *,
    solver_type: SolverType = SolverType.MINIMAX,
    depth: int = 1,
    extras: Sequence[Word | None] | None = None,
    reporter: RunView | None = None,
    lazy_eval: bool = True,
) -> Simulator:

    dictionary = load_dictionary(size, extras=extras)
    all_words, potential_solns = dictionary.words

    scorer = Scorer(size)
    histogram_builder = HistogramBuilder(scorer, potential_solns, all_words, lazy_eval)

    if solver_type == SolverType.MINIMAX:
        solver = MinimaxSolver(histogram_builder)
        for _ in range(1, depth):
            solver = DeepMinimaxSolver(histogram_builder, solver)

    elif solver_type == SolverType.ENTROPY:
        solver = EntropySolver(histogram_builder)
        for _ in range(1, depth):
            solver = DeepEntropySolver(histogram_builder, solver)

    else:
        raise ValueError(f"Solver type {solver_type} not recognised.")

    reporter = reporter or RunView(size)
    return Simulator(dictionary, scorer, histogram_builder, solver, reporter)


def create_benchmarker(
    size: int,
    *,
    solver_type: SolverType = SolverType.MINIMAX,
    depth: int = 1,
    extras: Sequence[Word | None] | None = None,
) -> Benchmarker:
    simulator = create_simulator(
        size,
        solver_type=solver_type,
        depth=depth,
        extras=extras,
        reporter=NullRunView(size),
        lazy_eval=False,
    )

    reporter = BenchmarkView()
    return Benchmarker(simulator, reporter)


def create_models(
    available_answers: WordSeries, all_words: WordSeries, depth: int
) -> tuple[Scorer, HistogramBuilder, Solver]:
    scorer = Scorer(all_words.word_length)
    histogram_builder = HistogramBuilder(scorer, available_answers, all_words)

    solver = MinimaxSolver(histogram_builder)
    for _ in range(1, depth):
        solver = DeepMinimaxSolver(histogram_builder, solver)

    if False:
        solver = EntropySolver(histogram_builder)
        for _ in range(1, depth):
            solver = DeepEntropySolver(histogram_builder, solver)

    return scorer, histogram_builder, solver
