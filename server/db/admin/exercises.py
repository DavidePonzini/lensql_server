from dav_tools import database
from .connection import db, SCHEMA

# TODO: is this needed?
def list_all() -> list[dict]:
    '''Get all exercises in the database'''

    query = database.sql.SQL(
    '''
        SELECT
            e.id,
            e.title,
            e.request,
            e.dataset_id,
            d.name,
            e.expected_answer,
            e.is_ai_generated
        FROM
            {schema}.exercises e
            LEFT JOIN {schema}.datasets d ON e.dataset_id = d.id
        ORDER BY
            e.title,
            e.id
    ''').format(
        schema=database.sql.Identifier(SCHEMA)
    )

    result = db.execute_and_fetch(query)

    return [
        {
            'id': row[0],
            'title': row[1],
            'request': row[2],
            'dataset_id': row[3],
            'dataset_name': row[4] if row[3] else 'None',
            'expected_answer': row[5],
            'is_ai_generated': row[6]
        }
        for row in result
    ]


def get(exercise_id: int, username: str) -> dict:
    '''Get the exercise for a given ID, if the user is assigned to it'''

    query = database.sql.SQL(
    '''
        SELECT
            e.request,
            e.dataset_id
        FROM
            {schema}.exercises e
            JOIN {schema}.assignments a ON e.id = a.exercise_id
        WHERE
            e.id = {exercise_id}
            AND a.username = {username} 
    ''').format(
        schema=database.sql.Identifier(SCHEMA),
        exercise_id=database.sql.Placeholder('exercise_id'),
        username=database.sql.Placeholder('username'),
    )
    result = db.execute_and_fetch(query, {
        'exercise_id': exercise_id,
        'username': username,
    })
    if len(result) == 0:
        return None
    return {
        'request': result[0][0],
        'dataset_id': result[0][1]
    }

def get_dataset(exercise_id: int) -> str:
    '''Get the dataset for a given exercise ID'''

    query = database.sql.SQL(
        '''
        SELECT dataset
        FROM {schema}.exercises e
            JOIN {schema}.datasets d ON e.dataset_id = d.id                     
        WHERE e.id = {exercise_id}
    ''').format(
        schema=database.sql.Identifier(SCHEMA),
        exercise_id=database.sql.Placeholder('exercise_id')
    )

    result = db.execute_and_fetch(query, {
        'exercise_id': exercise_id
    })

    if len(result) == 0:
        return '-- No dataset provided'

    return result[0][0]

def create(title: str, request: str, dataset_id: int | None, expected_answer: str, is_ai_generated: bool) -> int:
    '''Create a new exercise'''

    result = db.insert(SCHEMA, 'exercises', {
        'title': title,
        'request': request,
        'dataset_id': dataset_id,
        'expected_answer': expected_answer,
        'is_ai_generated': is_ai_generated
    }, ['id'])

    exercise_id = result[0][0]

    return exercise_id

def update(exercise_id: int, title: str, request: str, dataset_id: int | None, expected_answer: str) -> None:
    '''Update an existing exercise'''

    query = database.sql.SQL('''
        UPDATE {schema}.exercises
        SET title = {title},
            request = {request},
            dataset_id = {dataset_id},
            expected_answer = {expected_answer}
        WHERE id = {exercise_id}
    ''').format(
        schema=database.sql.Identifier(SCHEMA),
        title=database.sql.Placeholder('title'),
        request=database.sql.Placeholder('request'),
        dataset_id=database.sql.Placeholder('dataset_id'),
        expected_answer=database.sql.Placeholder('expected_answer'),
        exercise_id=database.sql.Placeholder('exercise_id')
    )
    db.execute(query, {
        'title': title,
        'request': request,
        'dataset_id': dataset_id,
        'expected_answer': expected_answer,
        'exercise_id': exercise_id
    })

def delete(exercise_id: int) -> None:
    '''Delete an exercise'''

    try:
        query = database.sql.SQL('''
            DELETE FROM {schema}.exercises
            WHERE id = {exercise_id}
        ''').format(
            schema=database.sql.Identifier(SCHEMA),
            exercise_id=database.sql.Placeholder('exercise_id')
        )
        db.execute(query, {
            'exercise_id': exercise_id
        })
    except Exception as e:
        return 

def assign(teacher: str, exercise_id: int, student: str) -> None:
    '''Assign an exercise to a student'''

    # TODO: Check if teacher is allowed to assign exercises to the student

    # Check if already assigned, skip if exists (optional safeguard)
    query_check = database.sql.SQL('''
        SELECT 1 FROM {schema}.assignments
        WHERE username = {student} AND exercise_id = {exercise_id}
    ''').format(
        schema=database.sql.Identifier(SCHEMA),
        student=database.sql.Placeholder('student'),
        exercise_id=database.sql.Placeholder('exercise_id')
    )
    exists = db.execute_and_fetch(query_check, {
        'student': student,
        'exercise_id': exercise_id
    })
    if exists:
        return

    db.insert(SCHEMA, 'assignments', {
        'username': student,
        'exercise_id': exercise_id
    })

def unassign(teacher: str, exercise_id: int, student: str) -> None:
    '''Unassign an exercise from a student'''

    # TODO: Check if teacher is allowed to unassign exercises from the student

    query = database.sql.SQL('''
        DELETE FROM {schema}.assignments
        WHERE username = {student}
        AND exercise_id = {exercise_id}
    ''').format(
        schema=database.sql.Identifier(SCHEMA),
        student=database.sql.Placeholder('student'),
        exercise_id=database.sql.Placeholder('exercise_id')
    )
    db.execute(query, {
        'student': student,
        'exercise_id': exercise_id
    })
