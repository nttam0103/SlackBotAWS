# handlers/home_handlers.py
from services.ec2_service import EC2Service
import os
import time
import threading
import logging
from concurrent.futures import ThreadPoolExecutor
import queue
from ui.home_blocks import (
    home_tab_blocks, ec2_modal_blocks, create_loading_modal, 
    create_error_modal, create_access_denied_modal,
    instance_status_modal, action_result_modal
)

def register_home_handlers(app):
    ec2_service = EC2Service()
    
    thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="ec2-loader")
    
    active_requests = {}
    request_lock = threading.Lock()
    
    def is_authorized(user_id):
        authorized_users = os.environ.get("AUTHORIZED_USERS", "").split(",")
        return user_id.strip() in [u.strip() for u in authorized_users if u.strip()]
    
    def load_ec2_data_async(client, view_id, user_id, request_id):
        """Load EC2 data in background thread with error handling"""
        try:
            # Check if request is still active (user hasn't closed modal)
            with request_lock:
                if request_id not in active_requests:
                    return  
            
            # Load EC2 instances
            instances = ec2_service.list_all_instances()
            
            # Check again before updating
            with request_lock:
                if request_id not in active_requests:
                    return
            
            if isinstance(instances, dict) and 'error' in instances:
                # Update modal with error
                error_modal = create_error_modal(instances['error'])
                client.views_update(view_id=view_id, view=error_modal)
            else:
                # Update modal with actual data
                paginated_data = ec2_service.paginate_instances(instances, page=1, per_page=50)
                modal_view = ec2_modal_blocks(paginated_data)
                client.views_update(view_id=view_id, view=modal_view)
                
                # Cache data for pagination
                with request_lock:
                    if request_id in active_requests:
                        active_requests[request_id]['instances'] = instances
        
        except Exception as e:
            logging.error(f"Error loading EC2 data: {e}")
            try:
                error_modal = create_error_modal(f"Unexpected error: {str(e)}")
                client.views_update(view_id=view_id, view=error_modal)
            except:
                pass  # Fail silently if can't update modal
        
        finally:
            # Cleanup request
            with request_lock:
                active_requests.pop(request_id, None)
    
    @app.event("app_home_opened")
    def handle_app_home_opened(client, event):
        """Handle home tab opened event"""
        try:
            client.views_publish(
                user_id=event["user"],
                view={
                    "type": "home",
                    "blocks": home_tab_blocks()
                }
            )
        except Exception as e:
            print(f"Error publishing home tab: {e}")
    
    @app.action("home_list_ec2")
    def handle_home_list_ec2(ack, body, client):
        """Handle EC2 list button - open modal loading and load data async"""
        ack()
        
        user_id = body["user"]["id"]
        if not is_authorized(user_id):
            try:
                client.views_open(
                    trigger_id=body["trigger_id"],
                    view=create_access_denied_modal()
                )
            except:
                pass
            return
        
        try:
            # open loading modal immediately
            loading_modal = create_loading_modal()
            response = client.views_open(
                trigger_id=body["trigger_id"],
                view=loading_modal
            )
            
            view_id = response["view"]["id"]
            request_id = f"{user_id}_{int(time.time())}"
            
            # Track request
            with request_lock:
                active_requests[request_id] = {
                    'view_id': view_id,
                    'user_id': user_id,
                    'instances': None
                }
            
            # Submit task to thread pool
            thread_pool.submit(load_ec2_data_async, client, view_id, user_id, request_id)
            
        except Exception as e:
            logging.error(f"Error opening modal: {e}")
    
    @app.action("retry_ec2_load")
    def handle_retry_ec2_load(ack, body, client):
        """Handle retry button trong error modal"""
        ack()
        
        user_id = body["user"]["id"]
        view_id = body["view"]["id"]
        request_id = f"{user_id}_{int(time.time())}"
        
        # Update modal to loading state
        loading_modal = create_loading_modal()
        client.views_update(view_id=view_id, view=loading_modal)
        
        # Track request
        with request_lock:
            active_requests[request_id] = {
                'view_id': view_id,
                'user_id': user_id,
                'instances': None
            }
        
        # Retry loading
        thread_pool.submit(load_ec2_data_async, client, view_id, user_id, request_id)
    
    @app.view_closed("ec2_loading_modal")
    @app.view_closed("ec2_list_modal")
    @app.view_closed("ec2_error_modal")
    @app.view_closed("instance_status_modal")
    @app.view_closed("action_result_modal")
    def handle_modal_closed(ack, body):
        """Cleanup khi user đóng modal"""
        ack()
        user_id = body["user"]["id"]
        
        # Cancel active requests for this user
        with request_lock:
            to_remove = [req_id for req_id, req_data in active_requests.items() 
                        if req_data['user_id'] == user_id]
            for req_id in to_remove:
                active_requests.pop(req_id, None)
    
    def get_user_instances(user_id):
        """Get cached instances for user"""
        with request_lock:
            for req_data in active_requests.values():
                if req_data['user_id'] == user_id and req_data['instances']:
                    return req_data['instances']
        return ec2_service.list_all_instances()  # Fallback
    
    # Modal pagination handlers
    @app.action("modal_ec2_next_page")
    def handle_modal_next_page(ack, body, client):
        ack()
        user_id = body["user"]["id"]
        page = int(body["actions"][0]["value"].split("_")[1])
        
        instances = get_user_instances(user_id)
        paginated_data = ec2_service.paginate_instances(instances, page=page, per_page=50)
        modal_view = ec2_modal_blocks(paginated_data)
        client.views_update(view_id=body["view"]["id"], view=modal_view)
    
    @app.action("modal_ec2_prev_page")
    def handle_modal_prev_page(ack, body, client):
        ack()
        user_id = body["user"]["id"]
        page = int(body["actions"][0]["value"].split("_")[1])
        
        instances = get_user_instances(user_id)
        paginated_data = ec2_service.paginate_instances(instances, page=page, per_page=50)
        modal_view = ec2_modal_blocks(paginated_data)
        client.views_update(view_id=body["view"]["id"], view=modal_view)
    
    @app.action("modal_page_info")
    def handle_modal_page_info(ack, body):
        ack()

    @app.action("instance_overflow_menu")
    def handle_instance_overflow(ack, body, client):
        ack()

        # Parse selected option value: "action|instance_id|region"
        selected_option = body["actions"][0]["selected_option"]["value"]
        action, instance_id, region = selected_option.split('|', 2)

        # Route to appropriate action based on selection
        if action == "start":
            result = ec2_service.start_instance(instance_id, region)
            if 'error' in result:
                modal = action_result_modal("Start Instance", result['error'], False)
            else:
                modal = action_result_modal("Start Instance", result['success'], True)
            client.views_push(view=modal)
            
        elif action == "stop":
            result = ec2_service.stop_instance(instance_id, region)
            if 'error' in result:
                modal = action_result_modal("Stop Instance", result['error'], False)
            else:
                modal = action_result_modal("Stop Instance", result['success'], True)
            client.views_push(view=modal)
            
        elif action == "status":
            status = ec2_service.get_instance_status(instance_id, region)
            if 'error' in status:
                modal = action_result_modal("Instance Status", status['error'], False)
            else:
                modal = instance_status_modal(status)
            client.views_push(view=modal)
