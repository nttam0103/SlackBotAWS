def ec2_list_block(instances):
    if not instances:
        return [{
            "type": "section",
            "text": {"type": "mrkdwn", "text": "❌ No EC2 instances found."}
        }]
    
    # Group by region
    regions = {}
    for instance in instances:
        region = instance['region']
        if region not in regions:
            regions[region] = []
        regions[region].append(instance)
    
    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"*🖥️ EC2 Instances ({len(instances)} total):*"}
    }, {"type": "divider"}]
    
    for region, region_instances in regions.items():
        # Region header
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🌍 {region.upper()}* ({len(region_instances)} instances)"}
        })
        
        # Instances in this region (limit 5 per region)
        for instance in region_instances[:5]:
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
                    "value": f"{instance['id']}|{region}",
                    "action_id": "manage_instance"
                }
            })
        
        if len(region_instances) > 5:
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"... and {len(region_instances) - 5} more instances in {region}"
                }]
            })
    
    return blocks

def instance_control_block(instance_id, state, region):
    buttons = []
    
    if state == "stopped":
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "▶️ Start"},
            "style": "primary",
            "value": f"{instance_id}|{region}",
            "action_id": "start_instance"
        })
    elif state == "running":
        buttons.append({
            "type": "button",
            "text": {"type": "plain_text", "text": "⏹️ Stop"},
            "style": "danger",
            "value": f"{instance_id}|{region}",
            "action_id": "stop_instance"
        })
    
    buttons.append({
        "type": "button",
        "text": {"type": "plain_text", "text": "📊 Status"},
        "value": f"{instance_id}|{region}",
        "action_id": "instance_status"
    })
    
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Instance Control:* `{instance_id}`\n*Region:* {region}\n*Current State:* {state}"
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
                    "text": f"*Region:*\n{instance_info['region']}"
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
