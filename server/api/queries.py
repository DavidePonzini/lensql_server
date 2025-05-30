'''This module handles query-related endpoints for the API.'''

from flask import Blueprint, request
import json
from flask_jwt_extended import jwt_required, get_jwt_identity

from server import db
from .util import responses

query_bp = Blueprint('query', __name__)


@query_bp.route('/run', methods=['POST'])
@jwt_required()
def run_query():
    '''
    Run a SQL query and return the results in a streaming response.
    This endpoint is used to execute user-submitted SQL queries against the database.
    '''
    username = get_jwt_identity()
    data = request.get_json()
    query = data['query']
    exercise_id = int(data['exercise_id'])

    batch_id = db.admin.queries.log_batch(
        username=username,
        exercise_id=exercise_id if exercise_id > 0 else None
    )

    def generate_results():
        for query_result in db.users.queries.execute(username=username, query_str=query):
            query_id = db.admin.queries.log(
                batch_id=batch_id,
                query=query_result.query,
                success=query_result.success,
                result_str=query_result.result
            )
            query_result.id = query_id

            yield json.dumps({
                'success': query_result.success,
                'builtin': False,
                'query': query_result.query,
                'type': query_result.type,
                'data': query_result.result,
                'id': query_id,
                'notices': query_result.notices,
            }) + '\n'  # Important: one JSON object per line

    return responses.streaming_response(generate_results())


@query_bp.route('/builtin/show-search-path', methods=['POST'])
@jwt_required()
def show_search_path():
    username = get_jwt_identity()
    data = request.get_json()
    exercise_id = int(data['exercise_id'])
    
    result = db.users.queries.builtin.show_search_path(username)

    batch_id = db.admin.queries.log_batch(
        username=username,
        exercise_id=exercise_id if exercise_id > 0 else None
    )

    query_id = db.admin.queries.log(
        batch_id=batch_id,
        query=result.query,
        success=result.success,
        result_str=result.result
    )

    result.id = query_id

    return responses.response_query(result, is_builtin=True)

@query_bp.route('/builtin/list-schemas', methods=['POST'])
@jwt_required()
def list_schemas():
    username = get_jwt_identity()
    data = request.get_json()
    exercise_id = int(data['exercise_id'])
    
    result = db.users.queries.builtin.list_schemas(username)

    batch_id = db.admin.queries.log_batch(
        username=username,
        exercise_id=exercise_id if exercise_id > 0 else None
    )

    query_id = db.admin.queries.log(
        batch_id=batch_id,
        query=result.query,
        success=result.success,
        result_str=result.result
    )

    result.id = query_id

    return responses.response_query(result, is_builtin=True)

@query_bp.route('/builtin/list-tables', methods=['POST'])
@jwt_required()
def list_tables():
    username = get_jwt_identity()
    data = request.get_json()
    exercise_id = int(data['exercise_id'])
    
    result = db.users.queries.builtin.list_tables(username)

    batch_id = db.admin.queries.log_batch(
        username=username,
        exercise_id=exercise_id if exercise_id > 0 else None
    )

    query_id = db.admin.queries.log(
        batch_id=batch_id,
        query=result.query,
        success=result.success,
        result_str=result.result
    )

    result.id = query_id

    return responses.response_query(result, is_builtin=True)

@query_bp.route('/builtin/list-all-tables', methods=['POST'])
@jwt_required()
def list_all_tables():
    username = get_jwt_identity()
    data = request.get_json()
    exercise_id = int(data['exercise_id'])
    
    result = db.users.queries.builtin.list_all_tables(username)

    batch_id = db.admin.queries.log_batch(
        username=username,
        exercise_id=exercise_id if exercise_id > 0 else None
    )

    query_id = db.admin.queries.log(
        batch_id=batch_id,
        query=result.query,
        success=result.success,
        result_str=result.result
    )

    result.id = query_id

    return responses.response_query(result, is_builtin=True)

@query_bp.route('/builtin/list-constraints', methods=['POST'])
@jwt_required()
def list_constraints():
    username = get_jwt_identity()
    data = request.get_json()
    exercise_id = int(data['exercise_id'])
    
    result = db.users.queries.builtin.list_constraints(username)

    batch_id = db.admin.queries.log_batch(
        username=username,
        exercise_id=exercise_id if exercise_id > 0 else None
    )

    query_id = db.admin.queries.log(
        batch_id=batch_id,
        query=result.query,
        success=result.success,
        result_str=result.result
    )

    result.id = query_id

    return responses.response_query(result, is_builtin=True)