import json
import logging
import traceback

from Controller.data_load import MovementRequestDto, ResponseDto, OptimizationRequestDto, OptimizationResponseDto, \
    SortingRequestDto
from Model.MovementType import MovementType
from Service.ScheduleSolver.ScheduleSolverMain import ScheduleSolverMain
from Controller.CustomJSONEncoder import CustomJSONEncoder
# from Controller.DTO.ResponseDto import ResponseDto
from Controller.ParserDTO import ParserDTO
from flask import Flask, request, jsonify
from marshmallow import ValidationError

from Controller.ResponseMetaDataDtoBuilder import ResponseMetaDataDtoBuilder

# from Controller.data_load import OptimizationRequestDtoSchema, OptimizationResponseDtoSchema, MovementRequestDtoSchema, \
#     SortingRequestDtoSchema, ResponseDtoSchema

parser = ParserDTO()

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


@app.route('/find-optimal', methods=['POST'])
def find_optimal():
    try:
        # Deserialize request data into DTO
        formatted_json = json.dumps(request.json, indent=4, ensure_ascii=False)  # JSON с двойными кавычками
        # app.logger.info(f"Received JSON data: {formatted_json}")

        logging.info("a")

        request_data = OptimizationRequestDto.model_validate(request.json)
        logging.info("a")

        # Use parser to convert DTO to Factory
        factory, max_search_time = parser.parse_Optimization_Request_Dto(request_data)

        # Create a ScheduleHandlerOptimal object
        schedule_handler = ScheduleSolverMain(factory, {})

        # Solve for optimal steps
        resolved_steps, status = schedule_handler.solve_optimal(max_search_time)
        if not (status == "OPTIMAL" or status == "FEASIBLE"):
            app.logger.info(f"Received JSON data: {formatted_json}")

            return jsonify(status + " проверка2"), 400

        # Serialize the resolved steps into the response format
        response_models = [OptimizationResponseDto.from_orm(item) for item in resolved_steps]
        response_json = [model.model_dump() for model in response_models]

        # app.logger.info(f"Received JSON data: {formatted_json}")

        return jsonify(response_json), 200

    except ValidationError as err:
        app.logger.info(f"Received JSON data: {formatted_json}")
        return jsonify(err.messages), 400
    except Exception as e:
        app.logger.info(f"Received JSON data: {formatted_json}")
        error_trace = traceback.format_exc()  # Получаем полную информацию о трассировке
        app.logger.error(f"Error occurred: {error_trace}")  # Логируем ошибку
        return jsonify({"error": str(e), "traceback": error_trace}), 500  # Возвращаем детальную ошибку


# Предполагается, что MovementRequestDto и ResponseDto – это ваши Pydantic модели,
# а parser.parse_Movement_Request_Dto, ScheduleSolverMain, ResponseMetaDataDtoBuilder определены в вашем коде.

@app.route('/find-first-for-moved-step', methods=['POST'])
def find_first_for_moved_step():
    try:
        logging.info("Starting find-first-for-moved-step")
        # Логируем входные данные
        formatted_json = json.dumps(request.json, ensure_ascii=False, separators=(',', ':'))
        # logging.info(f"Received JSON: {formatted_json}")

        logging.info("a")
        # Десериализация входных данных в DTO с помощью Pydantic
        request_data = MovementRequestDto.model_validate(request.json)
        logging.info("b")

        # Преобразование DTO в необходимые объекты
        logging.info("Deserializing request data into DTO")
        factory, maxSearchTime, movedSteps, movementType = parser.parse_Movement_Request_Dto(request_data)
        logging.info("Deserialized request data into DTO")

        schedule_solver = ScheduleSolverMain(factory, movedSteps)

        # Решение задачи перемещения шагов
        resolved_steps, status = schedule_solver.solve_for_moved_steps(movedSteps, movementType)

        if status not in ("OPTIMAL", "FEASIBLE"):
            app.logger.info(f"Received JSON data: {formatted_json}")

            responseMetaDataDtoBuilder = ResponseMetaDataDtoBuilder()
            responseMetaDataDtoBuilder.add_conflicts_with_types(
                schedule_solver.schedule_handler_recursive.conflict_registry.get_all_conflicts_with_type()
            )
            responseDto = ResponseDto(metadata=responseMetaDataDtoBuilder.getResponseMetaDataDTO())
            # Сериализация с помощью метода dict() Pydantic модели
            response_json = responseDto.model_dump()
            logging.info(f"Response JSON (400): {response_json}")
            return jsonify(response_json), 400

        # Формирование успешного ответа
        responseDto = ResponseDto(payload=resolved_steps)
        response_json = responseDto.model_dump()
        logging.info("Finished find-first-for-moved-step")
        return jsonify(response_json), 200

    except ValidationError as err:
        error_response = jsonify(err.messages)
        app.logger.info(f"Response JSON (ValidationError 400): {err.messages}")  # Логируем ошибки валидации
        return error_response, 400

    except Exception as e:
        error_trace = traceback.format_exc()  # Получаем полную информацию о трассировке
        error_response = {"error": str(e), "traceback": error_trace}
        app.logger.error(f"Response JSON (500): {error_trace}")  # Логируем ошибку с трассировкой
        return jsonify(error_response), 500  # Возвращаем детальную ошибку


@app.route('/resolve-conflicts', methods=['POST'])
def resolve_conflicts():
    try:
        # Deserialize request data into DTO
        formatted_json = json.dumps(request.json, ensure_ascii=False, separators=(',', ':'))
        # app.logger.info(f"Received JSON data: {formatted_json}")

        request_data = OptimizationRequestDto.model_validate(request.json)

        # Use parser to convert DTO to Factory
        factory, max_search_time = parser.parse_Optimization_Request_Dto(request_data)

        schedule_solver = ScheduleSolverMain(factory, {})

        # Solve for moved steps
        resolved_steps, status = schedule_solver.resolve_conflicts(3)

        if not (status == "OPTIMAL" or status == "FEASIBLE"):
            app.logger.info(f"Received JSON data: {formatted_json}")

            responseMetaDataDtoBuilder = ResponseMetaDataDtoBuilder()
            responseMetaDataDtoBuilder.add_conflicts_with_types(
                schedule_solver.schedule_handler_recursive.conflict_registry.get_all_conflicts_with_type()
            )
            responseDto = ResponseDto(metadata=responseMetaDataDtoBuilder.getResponseMetaDataDTO())
            response_json = responseDto.model_dump()


            app.logger.info(f"Response JSON (400): {response_json}")  # Логируем ответ перед возвратом
            return jsonify(response_json), 400

        # Serialize the resolved steps into the response format
        responseDto = ResponseDto(payload=resolved_steps)
        response_json = responseDto.model_dump()

        # app.logger.info(f"Received JSON data: {formatted_json}")

        app.logger.info(f"Response JSON (200): {response_json}")  # Логируем ответ перед возвратом
        return jsonify(response_json), 200

    except ValidationError as err:
        error_response = jsonify(err.messages)
        app.logger.info(f"Response JSON (ValidationError 400): {err.messages}")  # Логируем ошибки валидации
        return error_response, 400

    except Exception as e:
        error_trace = traceback.format_exc()  # Получаем полную информацию о трассировке
        error_response = {"error": str(e), "traceback": error_trace}
        app.logger.error(f"Response JSON (500): {error_trace}")  # Логируем ошибку с трассировкой
        return jsonify(error_response), 500  # Возвращаем детальную ошибку


@app.route('/sort-steps', methods=['POST'])
def sort_steps():
    try:
        # Deserialize request data into DTO
        formatted_json = json.dumps(request.json, indent=4, ensure_ascii=False)  # JSON с двойными кавычками
        app.logger.info(f"Received JSON data: {formatted_json}")


        request_data = SortingRequestDto.model_validate(request.json)

        # Use parser to convert DTO to Factory
        factory, max_search_time, sorted_steps = parser.parse_Sorting_Request_Dto(request_data)

        schedule_solver = ScheduleSolverMain(factory, {})

        # Solve for moved steps
        resolved_steps, status = schedule_solver.solve_for_sorted_steps(sorted_steps, 3)


        if not (status == "OPTIMAL" or status == "FEASIBLE"):
            app.logger.info(f"Received JSON data: {formatted_json}")

            responseMetaDataDtoBuilder = ResponseMetaDataDtoBuilder()
            responseMetaDataDtoBuilder.add_conflicts_with_types(
                schedule_solver.schedule_handler_recursive.conflict_registry.get_all_conflicts_with_type()
            )
            responseDto = ResponseDto(metadata=responseMetaDataDtoBuilder.getResponseMetaDataDTO())
            response_json = responseDto.model_dump()


            app.logger.info(f"Response JSON (400): {response_json}")  # Логируем ответ перед возвратом
            return jsonify(response_json), 400

        # Serialize the resolved steps into the response format
        responseDto = ResponseDto(payload=resolved_steps)
        response_json = responseDto.model_dump()

        # app.logger.info(f"Received JSON data: {formatted_json}")

        app.logger.info(f"Response JSON (200): {response_json}")  # Логируем ответ перед возвратом
        return jsonify(response_json), 200

    except ValidationError as err:
        error_response = jsonify(err.messages)
        app.logger.info(f"Response JSON (ValidationError 400): {err.messages}")  # Логируем ошибки валидации
        return error_response, 400

    except Exception as e:
        error_trace = traceback.format_exc()  # Получаем полную информацию о трассировке
        error_response = {"error": str(e), "traceback": error_trace}
        app.logger.error(f"Response JSON (500): {error_trace}")  # Логируем ошибку с трассировкой
        return jsonify(error_response), 500  # Возвращаем детальную ошибку


@app.route('/recalculate-by-heuristics', methods=['POST'])
def recalculate_by_heuristics():
    try:
        # Deserialize request data into DTO
        formatted_json = json.dumps(request.json, ensure_ascii=False, separators=(',', ':'))
        app.logger.info(f"Received JSON data: {formatted_json}")

        request_data = OptimizationRequestDto.model_validate(request.json)

        # Use parser to convert DTO to Factory
        factory, max_search_time = parser.parse_Optimization_Request_Dto(request_data)

        schedule_solver = ScheduleSolverMain(factory, {})

        # Solve for moved steps
        resolved_steps, status = schedule_solver.solve_optimal_for_demands(3)


        if not (status == "OPTIMAL" or status == "FEASIBLE"):
            responseMetaDataDtoBuilder = ResponseMetaDataDtoBuilder()
            responseMetaDataDtoBuilder.add_conflicts_with_types(
                schedule_solver.schedule_handler_recursive.conflict_registry.get_all_conflicts_with_type()
            )
            app.logger.info(f"Received JSON data: {formatted_json}")

            responseDto = ResponseDto(metadata=responseMetaDataDtoBuilder.getResponseMetaDataDTO())
            response_json = responseDto.model_dump()

            app.logger.info(f"Response JSON (400): {response_json}")  # Логируем ответ перед возвратом
            return jsonify(response_json), 400

        # Serialize the resolved steps into the response format
        responseDto = ResponseDto(payload=resolved_steps)
        response_json = responseDto.model_dump()

        app.logger.info(f"Received JSON data: {formatted_json}")

        app.logger.info(f"Response JSON (200): {response_json}")  # Логируем ответ перед возвратом
        return jsonify(response_json), 200

    except ValidationError as err:
        error_response = jsonify(err.messages)
        app.logger.info(f"Response JSON (ValidationError 400): {err.messages}")  # Логируем ошибки валидации
        return error_response, 400

    except Exception as e:
        error_trace = traceback.format_exc()  # Получаем полную информацию о трассировке
        error_response = {"error": str(e), "traceback": error_trace}
        app.logger.error(f"Response JSON (500): {error_trace}")  # Логируем ошибку с трассировкой
        return jsonify(error_response), 500  # Возвращаем детальную ошибку


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
