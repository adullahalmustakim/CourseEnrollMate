import re

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def validate_password(password):
    # At least 6 chars, 1 letter, 1 number
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$'
    return re.match(pattern, password)

def validate_name(name):
    return len(name.strip()) >= 3

def validate_credit_hours(credit):
    try:
        credit = int(credit)
        return 1 <= credit <= 6
    except:
        return False

def validate_course_code(code):
    return len(code.strip()) >= 3