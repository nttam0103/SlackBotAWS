def ec2_list_block(instances):
    if not instances:
        return [{
            "type": "section",
            "text": {"type": "mrkdwn", "text": "❌ No EC2 instances found."}
        }]
    
    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": "*🖥️ EC2 Instances:*"}
    }, {"type": "divider"}]
    
    for instance in instances[:100]:  # Limit to 100 instances
        state_emoji = {
            'running': '🟢',
            'stopped': '🔴',
            'stopping': '🟡',
            'starting': '🟡',
            'pending': '🟡'
        }.get(instance['state'], '⚪')
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{state_emoji} *{instance['name']}*\n`{instance['id']}` | {instance['type']} | {instance['state']}"
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Manage"},
                "value": instance['id'],
                "action_id": "manage_instance"
            }
        })
    
    return blocks

def instance_control_block(instance_id, state):
    buttons = []
    
    if state == "stopped":
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "▶️ Start"},
            "style": "primary",
            "value": instance_id,
            "action_id": "start_instance"
        })
    elif state == "running":
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "⏹️ Stop"},
            "style": "danger",
            "value": instance_id,
            "action_id": "stop_instance"
        })
    
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "📊 Status"},
        "value": instance_id,
        "action_id": "instance_status"
    })
    
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Instance Control:* `{instance_id}`\n*Current State:* {state}"
            }
        },
        {
            "type": "actions",
            "elements": buttons
        }
    ]

def instance_status_block(instance_info):
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*📊 Instance Status: `{instance_info['id']}`*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*State:*\n{instance_info['state']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Type:*\n{instance_info['type']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Public IP:*\n{instance_info['public_ip']}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Private IP:*\n{instance_info['private_ip']}"
                }
            ]
        }
    ]
