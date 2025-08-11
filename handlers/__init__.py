from .ec2_handlers import register_ec2_handlers
from .home_handlers import register_home_handlers

def register_all_handlers(app):
    register_ec2_handlers(app)
    register_home_handlers(app)