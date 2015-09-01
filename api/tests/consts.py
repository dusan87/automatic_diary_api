
# User required fields
EMAIL = 'email'
FIRST_NAME = 'first_name'
LAST_NAME = 'last_name'
PASSWORD = 'password'
COUNTRY = 'country'
CITY = 'city'
GENDER = 'gender'
PHONE_NUMBER = 'phone'

# fields messages
REQUIRED_MESSAGE = 'This field is required.'
INVALID_EMAIL_MSG = 'Enter a valid email address.'

USER_REQUIRED_FIELDS = (EMAIL, FIRST_NAME, LAST_NAME, PHONE_NUMBER)

AUTH_ERROR_MESSAGE ='User is not authorized! Please, check username and password!'

# interaction types

PHYSICAL = 'physical'
CALL = 'call'
SMS = 'sms'

INTERACTIONS = (
    (PHYSICAL, PHYSICAL),
    (CALL, CALL),
    (SMS, SMS)
)
