from services.ec2_service import EC2Service
from ui.ec2_blocks import ec2_list_block_with_pagination, instance_control_block, instance_status_block
import os 
import time

def register_ec2_handlers(app):
    ec2_service = EC2Service()
    
    instances_cache = []
    cache_timestamp = 0
    def get_cached_instances():
        nonlocal instances_cache, cache_timestamp
        
        current_time = time.time()
        # Cache for 60 seconds
        if current_time - cache_timestamp > 60:
            instances_cache = ec2_service.list_all_instances()
            cache_timestamp = current_time
        
        return instances_cache

    def is_authorized(user_id):
        authorized_users = os.environ.get("AUTHORIZED_USERS", "").split(",")
        return user_id.strip() in [u.strip() for u in authorized_users if u.strip()]
    
    @app.command("/ec2-list")
    def handle_ec2_list(ack, respond, command):
        ack()
        
        if not is_authorized(command['user_id']):
            respond("❌ You are not authorized to use this command.")
            return
        
        instances = ec2_service.list_instances()
        
        if isinstance(instances, dict) and 'error' in instances:
            respond(f"❌ Error: {instances['error']}")
        else:
            paginated_data = ec2_service.paginate_instances(instances, page=1, per_page=50)
            blocks = ec2_list_block_with_pagination(paginated_data)  # Use simple list block
            respond(text="EC2 Instances (Current Region)", blocks=blocks)

    @app.command("/ec2-list-all")
    def handle_ec2_list_all(ack, respond, command):
        ack()
        
        if not is_authorized(command['user_id']):
            respond("❌ You are not authorized to use this command.")
            return
        
        respond("🔍 Scanning all regions... This may take a moment.")
        
        # List instances from ALL regions
        instances = ec2_service.list_all_instances()
        
        if isinstance(instances, dict) and 'error' in instances:
            respond(f"❌ Error: {instances['error']}")
        else:
            # Use pagination for large lists
            paginated_data = ec2_service.paginate_instances(instances, page=1, per_page=20)
            blocks = ec2_list_block_with_pagination(paginated_data)
            respond(text=f"EC2 Instances (All Regions) - {len(instances)} found", blocks=blocks)
    
    @app.command("/ec2-list-page")
    def handle_ec2_list_page(ack, respond, command):
        ack()
        
        if not is_authorized(command['user_id']):
            respond("❌ You are not authorized to use this command.")
            return
        
        # Parse page number from command text
        try:
            page = int(command["text"].strip()) if command["text"].strip() else 1
        except ValueError:
            page = 1
        
        instances = ec2_service.list_all_instances()
        
        if isinstance(instances, dict) and 'error' in instances:
            respond(f"❌ Error: {instances['error']}")
        else:
            paginated_data = ec2_service.paginate_instances(instances, page=page, per_page=20)
            blocks = ec2_list_block_with_pagination(paginated_data)
            respond(text=f"EC2 Instances - Page {page}", blocks=blocks)

    @app.command("/ec2-start")
    def handle_ec2_start(ack, respond, command):
        ack()
        
        if not is_authorized(command['user_id']):
            respond("❌ You are not authorized to use this command.")
            return
        
        parts = command["text"].strip().split()
        
        if len(parts) < 1 or not parts[0].startswith('i-'):
            respond("❌ Usage: `/ec2-start i-xxxxxxxxx [region]`")
            return
        
        instance_id = parts[0]
        region = parts[1] if len(parts) > 1 else ec2_service.default_region

        result = ec2_service.start_instance(instance_id, region)
        
        if 'error' in result:
            respond(f"❌ Error: {result['error']}")
        else:
            respond(f"✅ {result['success']}")
    
    @app.command("/ec2-stop")
    def handle_ec2_stop(ack, respond, command):
        ack()
        
        if not is_authorized(command['user_id']):
            respond("❌ You are not authorized to use this command.")
            return
        
        parts = command["text"].strip().split()
        
        if len(parts) < 1 or not parts[0].startswith('i-'):
            respond("❌ Usage: `/ec2-stop i-xxxxxxxxx [region]`")
            return

        instance_id = parts[0]
        region = parts[1] if len(parts) > 1 else ec2_service.default_region
        result = ec2_service.stop_instance(instance_id, region)

        if 'error' in result:
            respond(f"❌ Error: {result['error']}")
        else:
            respond(f"✅ {result['success']}")
    
    # Pagination action handlers
    @app.action("ec2_next_page")
    def handle_next_page(ack, body, client):
        ack()
        
        page = int(body["actions"][0]["value"].split("_")[1])
        instances = get_cached_instances()
        
        paginated_data = ec2_service.paginate_instances(instances, page=page, per_page=20)
        blocks = ec2_list_block_with_pagination(paginated_data)
        try:
            client.chat_update(
                channel=body["channel"]["id"],
                ts=body["message"]["ts"],
                text=f"EC2 Instances - Page {page}",
                blocks=blocks
            )
        except:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                text=f"EC2 Instances - Page {page}",
                blocks=blocks,
                replace_original=True,
                respond_type="in_channel"
            )
        #say(text=f"EC2 Instances - Page {page}", blocks=blocks)
    
    @app.action("ec2_prev_page")
    def handle_prev_page(ack, body, client):
        ack()
        
        page = int(body["actions"][0]["value"].split("_")[1])
        instances = get_cached_instances()
        
        paginated_data = ec2_service.paginate_instances(instances, page=page, per_page=20)
        blocks = ec2_list_block_with_pagination(paginated_data)
        try:
            client.chat_update(
                channel=body["channel"]["id"],
                ts=body["message"]["ts"],
                text=f"EC2 Instances - Page {page}",
                blocks=blocks
            )
        except:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                text=f"EC2 Instances - Page {page}",
                blocks=blocks,
                replace_original=True,
                respond_type="in_channel"
            )
        #say(text=f"EC2 Instances - Page {page}", blocks=blocks)
    
    @app.action("refresh_ec2_list")
    def handle_refresh_list(ack, body, client):
        ack()
        
        global instances_cache, cache_timestamp
        instances = ec2_service.list_all_instances()
        cache_timestamp = time.time()
        paginated_data = ec2_service.paginate_instances(instances, page=1, per_page=20)
        blocks = ec2_list_block_with_pagination(paginated_data)
        try:
            client.chat_update(
                channel=body["channel"]["id"],
                ts=body["message"]["ts"],
                text=f"🔄 Refreshed EC2 Instances",
                blocks=blocks
            )
        except:
            client.chat_postMessage(
                channel=body["channel"]["id"],
                text=f"🔄 Refreshed EC2 Instances",
                blocks=blocks,
                replace_original=True,
                respond_type="in_channel"
            )
        #say(text="🔄 Refreshed EC2 Instances", blocks=blocks)
    
    @app.action("show_ec2_filters")
    def handle_show_filters(ack, body, say):
        ack()
        say("🔍 Filter feature coming soon! Use commands:\n"
            "• `/ec2-list` - Current region\n"
            "• `/ec2-list-all` - All regions")

    @app.action("page_info")
    def handle_page_info(ack, body):
        ack()

    @app.action("manage_instance")
    def handle_manage_instance(ack, body, say):
        ack()

        # Parse instance_id|region from button value    
        value = body["actions"][0]["value"]
        if '|' in value:
            instance_id, region = value.split('|', 1)
        else:
            instance_id = value
            region = ec2_service.default_region

        # Get instance info from specific region
        instances = ec2_service.list_instances_in_region(region)
        instance = next((i for i in instances if i['id'] == instance_id), None)
        
        if instance:
            blocks = instance_control_block(instance_id, instance['state'], region)
            say(text=f"Managing {instance_id} in {region}", blocks=blocks)
        else:
            say("❌ Instance not found.")
    
    @app.action("start_instance")
    def handle_start_instance_action(ack, body, say):
        ack()
        value = body["actions"][0]["value"]
        if '|' in value:
            instance_id, region = value.split('|', 1)
        else:
            instance_id = value
            region = ec2_service.default_region

        result = ec2_service.start_instance(instance_id, region)

        if 'error' in result:
            say(f"❌ Error: {result['error']}")
        else:
            say(f"✅ {result['success']}")
    
    @app.action("stop_instance")
    def handle_stop_instance_action(ack, body, say):
        ack()
        value = body["actions"][0]["value"]
        if '|' in value:
            instance_id, region = value.split('|', 1)
        else:
            instance_id = value
            region = ec2_service.default_region

        result = ec2_service.stop_instance(instance_id, region)

        if 'error' in result:
            say(f"❌ Error: {result['error']}")
        else:
            say(f"✅ {result['success']}")
    
    @app.action("instance_status")
    def handle_instance_status(ack, body, say):
        ack()
        value = body["actions"][0]["value"]
        if '|' in value:
            instance_id, region = value.split('|', 1)
        else:
            instance_id = value
            region = ec2_service.default_region

        status = ec2_service.get_instance_status(instance_id, region)
        
        if 'error' in status:
            say(f"❌ Error: {status['error']}")
        else:
            blocks = instance_status_block(status)
            say(text=f"Status for {instance_id} in {region}", blocks=blocks)
