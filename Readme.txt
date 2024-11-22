++--------------------------++

    To avoid any errors, please ensure that all required dependencies are installed from the requirements.txt file.

    1.) Open your Terminal or Command Prompt.

    2.) Navigate to the folder where the requirements.txt file is located.

    3.) Once you're in the correct folder, run the following command to install the dependencies:

    Copy this code
    pip install -r requirements.txt


    @ Admin Account Setup @

    Admin account credentials:

    Username: jb@a.com
    Password: admin
    
    Alternatively, if you'd like to create your own admin account, run the following command:

    Copy code
    python manage.py createsuperuser
    During this process, you'll be prompted to enter an email and password. You can use any email address, even if it doesn't exist.

    Update Your Settings
    After installing the dependencies, make the following changes in your settings.py file:

    In the INSTALLED_APPS section, add:

    python
    Copy code
    'django.contrib.humanize',
    Your INSTALLED_APPS section should look like this:

    python
    Copy code
    INSTALLED_APPS = [
        'django.contrib.humanize',
        # Other INSTALLED_APPS
    ]
    In the MIDDLEWARE section, add:

    python
    Copy code
    'whitenoise.middleware.WhiteNoiseMiddleware',
    Your MIDDLEWARE section should look like this:

    python
    Copy code
    MIDDLEWARE = [
        'whitenoise.middleware.WhiteNoiseMiddleware',
        # Other MIDDLEWARE entries
    ]

++--------------------------++