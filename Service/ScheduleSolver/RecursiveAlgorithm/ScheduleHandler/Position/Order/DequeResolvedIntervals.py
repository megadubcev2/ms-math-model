from typing import Dict, List
from uuid import UUID

from Model.IntervalType import IntervalType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Model.ResolvedInterval import ResolvedInterval
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.Order.OrderType import OrderType
from Service.ScheduleSolver.RecursiveAlgorithm.ScheduleHandler.Position.Order.ResolvedIntervalNode import \
    ResolvedIntervalNode


class DequeResolvedIntervals:
    """Класс для реализации двусвязного списка (deque)."""

    def __init__(self, resolvedIntervals: List[ResolvedInterval] = [], order_type: OrderType = OrderType.START):
        self.front = None  # Указатель на начало списка
        self.rear = None  # Указатель на конец списка
        self.resolved_interval_id_to_node: Dict[UUID, ResolvedIntervalNode] = {}
        self.order_type = order_type
        if order_type == OrderType.START:
            sorted_intervals = sorted(resolvedIntervals, key=lambda resolvedInterval: resolvedInterval.start)
        elif order_type == OrderType.END:
            sorted_intervals = sorted(resolvedIntervals, key=lambda resolvedInterval: resolvedInterval.end)

        # Заполняем двусвязный список и словарь
        for resolvedInterval in sorted_intervals:
            self.append_interval(resolvedInterval)

    def append_interval(self, resolvedInterval: ResolvedInterval):
        """Добавляет новый элемент в в нужное место в deque и обновляет словарь resolved_interval_id_to_node."""
        # Создаем новый узел для текущего интервала
        new_node = ResolvedIntervalNode(resolvedInterval)

        # Заполняем словарь
        self.resolved_interval_id_to_node[resolvedInterval.intervalId] = new_node

        # Добавляем узел в конец двусвязного списка
        if self.rear is None:  # Если список пустой
            self.front = self.rear = new_node
        else:
            self.rear.nextNode = new_node
            new_node.previousNode = self.rear
            self.rear = new_node
        self.update_interval_position(resolvedInterval.intervalId)

    def _swap_nodes(self, node1: ResolvedIntervalNode, node2: ResolvedIntervalNode):
        """Меняет местами два соседних узла node1 и node2, где node1 предшествует node2."""
        if node1.nextNode != node2 or node2.previousNode != node1:
            raise ValueError("Узлы не являются соседними или в неправильном порядке для обмена.")

        # Обновляем связи для node1 и node2
        node1.nextNode = node2.nextNode
        node2.previousNode = node1.previousNode
        node2.nextNode = node1
        node1.previousNode = node2

        # Обновляем предыдущий узел node1, если существует
        if node2.previousNode:
            node2.previousNode.nextNode = node2
        else:
            self.front = node2  # node2 теперь первый узел

        # Обновляем следующий узел node1, если существует
        if node1.nextNode:
            node1.nextNode.previousNode = node1
        else:
            self.rear = node1  # node1 теперь последний узел

    def _move_resolved_interval_node_right(self, resolved_interval_node: ResolvedIntervalNode):
        """Перемещает узел вправо, пока его start/end больше следующего узла."""
        current_node = resolved_interval_node
        if self.order_type == OrderType.START:
            while (current_node.nextNode and
                   current_node.resolvedInterval.start > current_node.nextNode.resolvedInterval.start):
                next_node = current_node.nextNode
                self._swap_nodes(current_node, next_node)
                #current_node = next_node  # Продолжаем с новым положением узла

        elif self.order_type == OrderType.END:
            while (current_node.nextNode and
                   current_node.resolvedInterval.end > current_node.nextNode.resolvedInterval.end):
                next_node = current_node.nextNode
                self._swap_nodes(current_node, next_node)
                #current_node = next_node  # Переходим к следующему узлу

    def _move_resolved_interval_node_left(self, resolved_interval_node: ResolvedIntervalNode):
        """Перемещает узел влево, пока его start меньше предыдущего узла."""
        current_node = resolved_interval_node
        if self.order_type == OrderType.START:
            while (current_node.previousNode
                   and current_node.resolvedInterval.start < current_node.previousNode.resolvedInterval.start):
                prev_node = current_node.previousNode
                self._swap_nodes(prev_node, current_node)
                #current_node = prev_node  # Продолжаем с новым положением узла

        elif self.order_type == OrderType.END:
            while (current_node.previousNode
                   and current_node.resolvedInterval.end < current_node.previousNode.resolvedInterval.end):
                prev_node = current_node.previousNode
                self._swap_nodes(prev_node, current_node)
                #current_node = prev_node  # Переходим к следующему узлу



    def update_interval_position(self, resolved_interval_id: UUID):
        """Определяет, нужно ли двигать узел влево или вправо, и выполняет перемещение.
        Возвращает список  интервалов, e которых могут быть измены переналадки из-за изменения позиции.
        таких мнтервалов может быть от 1 до 3
        """
        resolved_interval_node = self.resolved_interval_id_to_node.get(resolved_interval_id)

        if resolved_interval_node is None:
            raise ValueError(f"ResolvedInterval с ID {resolved_interval_id} не найден")

        intervals_with_possible_changed_setups = [resolved_interval_node.resolvedInterval]
        if resolved_interval_node.nextNode:
            nextNode = resolved_interval_node.nextNode
            intervals_with_possible_changed_setups.append(nextNode.resolvedInterval)

        # Перемещаем узел вправо
        self._move_resolved_interval_node_right(resolved_interval_node)

        # Перемещаем узел влево
        self._move_resolved_interval_node_left(resolved_interval_node)

        if resolved_interval_node.nextNode:
            nextNode = resolved_interval_node.nextNode
            intervals_with_possible_changed_setups.append(nextNode.resolvedInterval)

        return intervals_with_possible_changed_setups

    def get_previous_interval(self, resolved_interval_id: UUID):
        node = self.resolved_interval_id_to_node.get(resolved_interval_id)
        if node is None:
            raise ValueError(f"ResolvedInterval с ID {resolved_interval_id} не найден")
        if node.previousNode is None:
            return None
        return node.previousNode.resolvedInterval

    def get_next_interval(self, resolved_interval_id: UUID):
        node = self.resolved_interval_id_to_node.get(resolved_interval_id)
        if node is None:
            raise ValueError(f"ResolvedInterval с ID {resolved_interval_id} не найден")
        if node.nextNode is None:
            return None
        return node.nextNode.resolvedInterval

    def get_previous_step(self, resolved_interval_id: UUID):
        node = self.resolved_interval_id_to_node.get(resolved_interval_id)
        if node is None:
            raise ValueError(f"ResolvedInterval с ID {resolved_interval_id} не найден")

        if node.previousNode is None:
            return None
        if node.previousNode.resolvedInterval.type == IntervalType.IDLE_PERIOD:
            return self.get_previous_interval(node.previousNode.resolvedInterval.intervalId)

        return node.previousNode.resolvedInterval

    def get_next_step(self, resolved_interval_id: UUID):
        node = self.resolved_interval_id_to_node.get(resolved_interval_id)
        if node is None:
            raise ValueError(f"ResolvedInterval с ID {resolved_interval_id} не найден")

        if node.nextNode is None:
            return None
        if node.nextNode.resolvedInterval.type == IntervalType.IDLE_PERIOD:
            return self.get_next_step(node.nextNode.resolvedInterval.intervalId)

        return node.nextNode.resolvedInterval

    def get_sorted_intervals(self):
        """Возвращает список отсортированных интервалов в порядке возрастания start/end."""
        sorted_resolved_intervals = []
        current_node = self.front
        while current_node is not None:
            sorted_resolved_intervals.append(current_node.resolvedInterval)
            current_node = current_node.nextNode
        return sorted_resolved_intervals

    def get_sorted_steps(self):
        """Возвращает список отсортированных интервалов только степов в порядке возрастания start/end."""
        sorted_steps = []
        current_node = self.front
        while current_node is not None:
            if current_node.resolvedInterval.type == IntervalType.STEP:
                sorted_steps.append(current_node.resolvedInterval)
            current_node = current_node.nextNode
        return sorted_steps
