from .ec2_handlers import register_ec2_handlers

def register_all_handlers(app):
    register_ec2_handlers(app)
