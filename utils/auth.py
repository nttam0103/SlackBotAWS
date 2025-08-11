import os
import logging

def is_authorized(user_id):
    """Centralized authorization check"""
    try:
        authorized_users = os.environ.get("AUTHORIZED_USERS", "").split(",")
        authorized_list = [u.strip() for u in authorized_users if u.strip()]
        
        if not authorized_list:
            logging.warning("No authorized users configured")
            return False
            
        return user_id.strip() in authorized_list
    except Exception as e:
        logging.error(f"Authorization check failed: {e}")
        return False
