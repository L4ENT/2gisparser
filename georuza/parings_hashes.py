import hashlib

class HashingException(Exception):
    ...


def rubric_page_parsing_hash(data):
    # Do not change this function NEVER !!!!!!!!
    try:
        rubric_id = int(data['rubric_id'])
        page_size = int(data['page_size'])
        page = int(data['page'])
        key = f'rubric_page_parsing_{rubric_id}:{page_size}:{page}'
        hash = hashlib.md5(key.encode())
        result = hash.hexdigest()
    except:
        raise HashingException()
    return result
