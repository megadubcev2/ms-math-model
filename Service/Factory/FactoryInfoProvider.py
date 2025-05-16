import logging
from collections import defaultdict
from typing import Dict, Tuple, List
from uuid import UUID
import string

from Model.Step import Step
from Model.StepOrder import StepOrder

# Настройка базового конфигуратора логирования (можно настроить по необходимости)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FactoryInfoProvider:
    def __init__(self, factory, moved_steps):
        logging.info("FactoryInfoProvider initialized")
        self.factory = factory
        self.campaign_machine_to_task_machine = self.create_campaign_machine_to_task_machine()

        self.machine_to_name = self.create_machine_to_name()

        self.connectivity_components = self.find_connected_components(self.factory.steps, self.factory.stepsOrder)
        self.light_connectivity_components = self.find_light_connected_components(self.factory.steps,
                                                                                  self.factory.stepsOrder)
        self.allStepsOrder = self.create_all_steps_order()
        self.demands_to_steps = self.create_demand_to_steps(self.factory.steps)
        self.maxSetup = self.calculate_max_setup()
        self.step_to_step_orders = self.create_step_to_step_orders()

        self.moved_steps = moved_steps
        self.interval_to_name = self.create_interval_to_name()

        logging.info("FactoryInfoProvider initialized")

        #self.log_common_variables()

    def log_common_variables(self):
        """
        Метод для логирования переменных, присутствующих в обеих версиях класса.
        """
        logger.info("Logging common Factory variables:")
        logger.info(f"duration: {self.factory.duration}")
        logger.info(f"steps: {self.factory.steps}")
        logger.info(f"machinesSetup: {self.factory.machinesSetup}")
        logger.info(f"stepsOrder: {self.factory.stepsOrder}")
        logger.info(f"machines: {self.factory.machines}")
        logger.info(f"fixedSteps: {self.factory.fixedSteps}")
        logger.info(f"idlePeriods: {self.factory.idlePeriods}")
        logger.info(f"start: {self.factory.start}")
        logger.info(f"importantDemands: {self.factory.importantDemands}")
        logger.info(f"demands: {self.factory.demands}")
        logger.info(f"demands_to_steps: {self.demands_to_steps}")
        logger.info(f"maxSetup: {self.maxSetup}")
        logger.info(f"connectivity_components: {self.connectivity_components}")
        logger.info(f"allStepsOrder: {self.allStepsOrder}")

    def create_all_steps_order(self):
        all_steps_order = []
        for steps_order in self.factory.stepsOrder.values():
            for step_order in steps_order:
                all_steps_order.append(step_order)
        return all_steps_order

    def create_demand_to_steps(self, steps):
        demand_to_steps = {}
        for step in steps.values():
            demand_to_steps.setdefault(step.demandId, []).append(step)
        return demand_to_steps

    def find_connected_components(self, steps: Dict[UUID, Step], stepsOrder: Dict[Tuple[UUID, UUID], StepOrder]) -> \
            Dict[
                UUID, int]:

        logging.info("Creating connected components...")
        # Словарь для хранения графа
        graph = defaultdict(list)

        # Строим граф, где рёбрами являются связи между степами через StepOrder
        for (previousStepId, nextStepId) in stepsOrder.keys():
            graph[previousStepId].append(nextStepId)
            graph[nextStepId].append(previousStepId)

        # DFS для поиска компонент связности
        def dfs(stepId, component_id):
            stack = [stepId]
            visited[stepId] = component_id

            while stack:
                node = stack.pop()
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited[neighbor] = component_id
                        stack.append(neighbor)

        # Словарь для хранения номера компоненты связности для каждого stepId
        visited = {}
        component_id = 0

        # Проходим по всем степам, даже если они не участвуют в stepOrder
        for stepId in steps:
            if stepId not in visited:
                # Если степ не посещён, запускаем DFS для новой компоненты
                dfs(stepId, component_id)
                component_id += 1
        logging.info("Connected components created successfully.")

        return visited

    def find_light_connected_components(self, steps: Dict[UUID, Step],
                                        stepsOrder: Dict[Tuple[UUID, UUID], StepOrder]) -> Dict[UUID, int]:
        logging.info("Creating light connected components...")
        # Словарь для хранения графа
        graph = defaultdict(list)

        # Строим граф, где рёбрами являются связи между степами через StepOrder
        for (previousStepId, nextStepId) in stepsOrder.keys():
            graph[previousStepId].append(nextStepId)
            graph[nextStepId].append(previousStepId)

        # 2. Добавляем рёбра между степами, которые находятся на одной машине
        machine_steps = defaultdict(list)
        for step in steps.values():
            machine_steps[step.machineId].append(step.stepId)

        # Для каждой машины соединяем cсоединяем степы подряд
        for step_ids in machine_steps.values():
            n = len(step_ids)
            for i in range(n - 1):
                a = step_ids[i]
                b = step_ids[i + 1]
                # Добавляем двустороннюю связь, если её ещё нет
                if b not in graph[a]:
                    graph[a].append(b)
                if a not in graph[b]:
                    graph[b].append(a)

        # DFS для поиска компонент связности
        def dfs(stepId, component_id):
            stack = [stepId]
            visited[stepId] = component_id

            while stack:
                node = stack.pop()
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        visited[neighbor] = component_id
                        stack.append(neighbor)

        # Словарь для хранения номера компоненты связности для каждого stepId
        visited = {}
        component_id = 0

        # Проходим по всем степам, даже если они не участвуют в stepOrder
        for stepId in steps:
            if stepId not in visited:
                # Если степ не посещён, запускаем DFS для новой компоненты
                dfs(stepId, component_id)
                component_id += 1

        logging.info("Light connected components created successfully.")

        return visited

    def calculate_max_setup(self) -> int:
        """
        Метод для вычисления максимальной продолжительности настройки
        """
        return max([setup.duration for setup in self.factory.machinesSetup.values()], default=0)

    def create_campaign_machine_to_task_machine(self):
        create_campaign_machine_to_step_machine = {}
        for step_machine_id in self.factory.task_machine_to_campaign_machine.keys():
            campaign_machine_id = self.factory.task_machine_to_campaign_machine[step_machine_id]
            create_campaign_machine_to_step_machine[campaign_machine_id] = step_machine_id
        return create_campaign_machine_to_step_machine

    def create_step_to_step_orders(self) -> Dict[UUID, List[StepOrder]]:
        step_to_step_orders: Dict[UUID, List[StepOrder]] = {}
        for step in self.factory.steps.values():
            step_to_step_orders[step.stepId] = []

        for stepOrder in self.allStepsOrder:
            step_to_step_orders.setdefault(stepOrder.previousStepId, []).append(stepOrder)
            step_to_step_orders.setdefault(stepOrder.nextStepId, []).append(stepOrder)
        return step_to_step_orders

    def are_steps_connected(self, first_step_id, second_step_id):
        return self.connectivity_components[first_step_id] == self.connectivity_components[
            second_step_id]

    def is_step_connected_with_moved_steps(self, step_id: UUID):
        if step_id not in self.factory.steps:
            return False
        for moved_step in self.moved_steps.keys():
            if self.are_steps_connected(moved_step, step_id):
                return True

        return False

    def get_machines_connected_with_important_demands(self):
        important_demands_components = set()
        for step in self.factory.steps.values():
            if step.demandId in self.factory.importantDemands.keys():
                important_demands_components.add(self.light_connectivity_components[step.stepId])

        logging.info(f"important_demands_components: {important_demands_components}")

        machines_connected_with_important_demands = set()
        for step in self.factory.steps.values():
            if self.light_connectivity_components[step.stepId] in important_demands_components:
                machines_connected_with_important_demands.add(step.machineId)

        return machines_connected_with_important_demands

    def create_machine_to_name(self):
        machine_to_name = {}
        i = 0
        for campaign_machine_id, task_machine_id in self.campaign_machine_to_task_machine.items():
            machine_to_name[task_machine_id] = str(i // 26) + string.ascii_lowercase[i % 26]
            machine_to_name[campaign_machine_id] = str(i // 26) + string.ascii_lowercase[i % 26] + "_c"

            i += 1

        return machine_to_name

    def create_interval_to_name(self):
        interval_to_name = {}

        for machine_id in self.machine_to_name.keys():
            steps_on_machine = [step for step in self.factory.steps.values() if step.machineId == machine_id]
            steps_on_machine.sort(key=lambda x: x.start)
            for i, step in enumerate(steps_on_machine):
                interval_to_name[
                    step.stepId] = f"{self.machine_to_name[machine_id]}_num_{i}_comp_{self.connectivity_components[step.stepId]}"
                if step.fixed:
                    interval_to_name[step.stepId] += "_fixed"
                if step.stepId in self.moved_steps:
                    interval_to_name[step.stepId] += "_moved"
                else:
                    if self.is_step_connected_with_moved_steps(step.stepId):
                        interval_to_name[step.stepId] += "_moved_connected"

            idle_periods_on_machine = [period for period in self.factory.idlePeriods if
                                       period.machineId == machine_id]
            idle_periods_on_machine.sort(key=lambda x: x.start)
            for i, period in enumerate(idle_periods_on_machine):
                interval_to_name[period.idlePeriodId] = f"{self.machine_to_name[machine_id]}_num_{i}_idle"

        return interval_to_name
