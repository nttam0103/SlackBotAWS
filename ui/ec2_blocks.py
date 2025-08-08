def ec2_list_block_with_pagination(paginated_data, filters=None):
    instances = paginated_data['instances']
    pagination = paginated_data['pagination']
    
    if not instances:
        return [{
            "type": "section",
            "text": {"type": "mrkdwn", "text": "❌ No EC2 instances found."}
        }]
    
    # Header with pagination info
    header_text = f"*🖥️ EC2 Instances* (Page {pagination['current_page']}/{pagination['total_pages']}) - {pagination['total_items']} total"
    
    if filters:
        filter_text = []
        if filters.get('state'): filter_text.append(f"State: {filters['state']}")
        if filters.get('region'): filter_text.append(f"Region: {filters['region']}")
        if filters.get('name_filter'): filter_text.append(f"Name: *{filters['name_filter']}*")
        if filter_text:
            header_text += f"\n🔍 Filters: {' | '.join(filter_text)}"
    
    blocks = [{
        "type": "section",
        "text": {"type": "mrkdwn", "text": header_text}
    }, {"type": "divider"}]
    
    # Group by region
    regions = {}
    for instance in instances:
        region = instance['region']
        if region not in regions:
            regions[region] = []
        regions[region].append(instance)
    
    # Display instances by region
    for region, region_instances in regions.items():
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*🌍 {region.upper()}* ({len(region_instances)} instances)"}
        })
        
        for instance in region_instances:
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
    
    # Pagination controls
    if pagination['total_pages'] > 1:
        blocks.append({"type": "divider"})
        
        pagination_elements = []
        
        # Previous button
        if pagination['has_prev']:
            pagination_elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "⬅️ Previous"},
                "value": f"page_{pagination['current_page'] - 1}",
                "action_id": "ec2_prev_page"
            })
        
        # Page info
        pagination_elements.append({
            "type": "button",
            "text": {"type": "plain_text", "text": f"Page {pagination['current_page']}/{pagination['total_pages']}"},
            "value": "page_info",
            "action_id": "page_info"
        })
        
        # Next button
        if pagination['has_next']:
            pagination_elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "Next ➡️"},
                "value": f"page_{pagination['current_page'] + 1}",
                "action_id": "ec2_next_page"
            })
        
        blocks.append({
            "type": "actions",
            "elements": pagination_elements
        })
    
    # Filter controls
    blocks.append({"type": "divider"})
    filter_elements = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "🔍 Filter"},
            "value": "show_filters",
            "action_id": "show_ec2_filters"
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "🔄 Refresh"},
            "value": "refresh",
            "action_id": "refresh_ec2_list"
        }
    ]
    
    blocks.append({
        "type": "actions",
        "elements": filter_elements
    })
    
    return blocks

def filter_modal_block():
    """Modal for filtering instances"""
    return {
        "type": "modal",
        "callback_id": "ec2_filter_modal",
        "title": {"type": "plain_text", "text": "Filter EC2 Instances"},
        "submit": {"type": "plain_text", "text": "Apply Filters"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Filter Options:*"}
            },
            {
                "type": "input",
                "block_id": "state_filter",
                "optional": True,
                "label": {"type": "plain_text", "text": "Instance State"},
                "element": {
                    "type": "static_select",
                    "action_id": "state_select",
                    "placeholder": {"type": "plain_text", "text": "Select state..."},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Running"}, "value": "running"},
                        {"text": {"type": "plain_text", "text": "Stopped"}, "value": "stopped"},
                        {"text": {"type": "plain_text", "text": "Starting"}, "value": "starting"},
                        {"text": {"type": "plain_text", "text": "Stopping"}, "value": "stopping"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "name_filter",
                "optional": True,
                "label": {"type": "plain_text", "text": "Instance Name (contains)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "name_input",
                    "placeholder": {"type": "plain_text", "text": "Enter name to search..."}
                }
            }
        ]
    }
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
