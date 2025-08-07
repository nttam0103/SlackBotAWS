from services.ec2_service import EC2Service
from ui.ec2_blocks import ec2_list_block, instance_control_block, instance_status_block
import os

def register_ec2_handlers(app):
    ec2_service = EC2Service()
    
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
            blocks = ec2_list_block(instances)
            respond(text=f"EC2 Instances (Current Region)", blocks=blocks)

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
            blocks = ec2_list_block(instances)
            respond(text=f"EC2 Instances (All Regions) - {len(instances)} found", blocks=blocks)
     

    @app.command("/ec2-start")
    def handle_ec2_start(ack, respond, command):
        ack()
        
        if not is_authorized(command['user_id']):
            respond("❌ You are not authorized to use this command.")
            return
        
        parts = command["text"].strip().split()
        
        if len(parts) < 1 or not parts[0].startswith('i-'):
            respond("❌ Usage: `/ec2-start i-xxxxxxxxx`")
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
            respond("❌ Usage: `/ec2-stop i-xxxxxxxxx`")
            return

        instance_id = parts[0]
        region = parts[1] if len(parts) > 1 else ec2_service.default_region
        result = ec2_service.stop_instance(instance_id, region)

        if 'error' in result:
            respond(f"❌ Error: {result['error']}")
        else:
            respond(f"✅ {result['success']}")
    
    @app.action("manage_instance")
    def handle_manage_instance(ack, body, say):
        ack()

        # Parse instance_id | region from button value    
        value = body["actions"][0]["value"]
        if '|' in value:
            instance_id, region = value.split('|', 1)
        else:
            instance_id = value
            region = ec2_service.default_region

        # Get instance info form specific region
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
