import copy
import random
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleSolverRecursive import ScheduleSolverRecursive
from Service.Utils.ResolvedStepsEvaluator import ResolvedStepsEvaluator


class ParallelScheduleSolverRecursive(ScheduleSolverRecursive):
    def __init__(self, *args, num_workers=4, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_workers = num_workers
        self.resolved_steps_evaluator = ResolvedStepsEvaluator()
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        self.logger.info(f"ProcessPoolExecutor initialized with {self.num_workers} workers")

    def solve_for_moved_steps(self, movementType, magnetic_constraints, max_search_time=3):
        """
        Parallelized version of solve_for_moved_steps:
        Runs multiple solvers with different random seeds and picks the best solution,
        then updates the provided magnetic_constraints dict to reflect the best result.
        """
        self.logger.info(
            f"Starting parallel solve_for_moved_steps: movementType={movementType}, max_search_time={max_search_time}, workers={self.num_workers}"
        )

        # Prepare independent copies of magnetic_constraints for each worker
        inputs = []
        for seed in range(self.num_workers):
            self.logger.info(f"Preparing input for worker seed={seed}")
            mp = copy.deepcopy(magnetic_constraints)
            if seed == 0:
                conflict_resolver_type = 1
            else:
                conflict_resolver_type = 2
            inputs.append((self.factory_info_provider, movementType, mp, conflict_resolver_type, max_search_time, seed))

        results = []
        futures = []
        for fi, mt, mp, conflict_resolver_type, ms, seed in inputs:
            self.logger.info(f"Submitting worker for seed={seed}")
            futures.append(
                self.executor.submit(
                    self._run_moved_steps_static,
                    fi, mt, mp, conflict_resolver_type, ms, seed
                )
            )

        for future in as_completed(futures):
            try:
                resolved_steps, status, score, constraints, seed = future.result()
                self.logger.info(f"Worker completed: status={status}, score={score}")
                results.append((resolved_steps, status, score, constraints, seed))
            except Exception as e:
                self.logger.error(f"Worker raised exception: {e}")

        if not results:
            self.logger.error("No results returned from workers")
            return None, "UNKNOWN"

        # Select the best result by evaluation score (lower is better)
        best_resolved_steps, best_status, best_score, best_constraints, best_seed =\
            min(results, key=lambda r: r[2])
        self.logger.info(f"Best worker {best_seed} score={best_score}, status={best_status}")

        # Update the passed-in magnetic_constraints dict to match the best solution
        magnetic_constraints.clear()
        magnetic_constraints.update(best_constraints)
        self.logger.info(
            f"magnetic_constraints updated with best worker constraints: {magnetic_constraints}"
        )

        self.logger.info("Parallel solve_for_moved_steps completed")
        return best_resolved_steps, best_status

    @staticmethod
    def _run_moved_steps_static(
            factory_info_provider, movementType, magnetic_constraints, conflict_resolver_type, max_search_time, seed
    ):
        logger = logging.getLogger(__name__)
        logger.info(f"Worker {seed}: initializing static run")
        # Seed randomness for diversity
        random.seed(seed)
        logger.info(f"Worker {seed}: random seed set to {seed}")

        solver = ScheduleSolverRecursive(factory_info_provider, conflict_resolver_type, max_search_time)
        logger.info(f"Worker {seed}: starting solver.solve_for_moved_steps")
        resolved_steps, status = solver.solve_for_moved_steps(
            movementType,
            magnetic_constraints,
            max_search_time
        )
        logger.info(f"Worker {seed}: solver completed with status={status}")

        evaluator = ResolvedStepsEvaluator()
        score = evaluator.evaluate(resolved_steps, factory_info_provider)
        logger.info(f"Worker {seed}: evaluation score={score}")

        # Return the mutated magnetic_constraints along with the solution
        return resolved_steps, status, score, magnetic_constraints, seed
