# ui/home_blocks.py
def home_tab_blocks():
    """Home tab layout với EC2 management button"""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🏠 AWS SlackBot Dashboard*\nWelcome! Manage your AWS resources easily."
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*🖥️ EC2 Management*\nView and manage your EC2 instances across all regions."
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "📋 List EC2 Instances"},
                "style": "primary",
                "action_id": "home_list_ec2"
            }
        },
        {"type": "divider"},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 *Quick Commands:* `/ec2-list` | `/ec2-list-all` | `/hello-bot`"
                }
            ]
        }
    ]

def ec2_modal_blocks(paginated_data):
    """Modal list EC2 instance """
    instances = paginated_data['instances']
    pagination = paginated_data['pagination']

    if not instances:
        return {
            "type": "modal",
            "callback_id": "ec2_list_modal",
            "title": {
                "type": "plain_text",
                "text": "EC2 Instances"
            },
            "close": {
                "type": "plain_text",
                "text": "Close"
            },
            "blocks": [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": " ❌ No EC2 instances found."
                }
            }]
        }
    # Header 
    header_text = f"*🖥️ EC2 Instances* (Page {pagination['current_page']}/{pagination['total_pages']}) - {pagination['total_items']} total"
    
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
                'running': '🟢', 'stopped': '🔴', 'stopping': '🟡',
                'starting': '🟡', 'pending': '🟡'
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
                    "action_id": "modal_manage_instance"
                }
            })
    
    # Pagination controls
    if pagination['total_pages'] > 1:
        blocks.append({"type": "divider"})
        
        pagination_elements = []
        
        if pagination['has_prev']:
            pagination_elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "⬅️ Previous"},
                "value": f"page_{pagination['current_page'] - 1}",
                "action_id": "modal_ec2_prev_page"
            })
        
        pagination_elements.append({
            "type": "button",
            "text": {"type": "plain_text", "text": f"Page {pagination['current_page']}/{pagination['total_pages']}"},
            "value": "page_info",
            "action_id": "modal_page_info"
        })
        
        if pagination['has_next']:
            pagination_elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": "Next ➡️"},
                "value": f"page_{pagination['current_page'] + 1}",
                "action_id": "modal_ec2_next_page"
            })
        
        blocks.append({
            "type": "actions",
            "elements": pagination_elements
        })
    
    return {
        "type": "modal",
        "callback_id": "ec2_list_modal",
        "title": {"type": "plain_text", "text": "EC2 Instances"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": blocks
    }


def create_loading_modal():
    """Create loading modal with progress indicator"""
    return {
        "type": "modal",
        "callback_id": "ec2_loading_modal",
        "title": {"type": "plain_text", "text": "EC2 Instances"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn", 
                    "text": "🔍 *Loading EC2 instances...*\n⏳ Scanning all AWS regions, please wait..."
                }
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": "💡 This may take 5-10 seconds"
                }]
            }
        ]
    }

def create_error_modal(error_message):
    """Create error modal retry option"""
    return {
        "type": "modal",
        "callback_id": "ec2_error_modal",
        "title": {"type": "plain_text", "text": "Error"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"❌ *Error loading EC2 instances*\n{error_message}"}
            },
            {
                "type": "actions",
                "elements": [{
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🔄 Retry"},
                    "style": "primary",
                    "action_id": "retry_ec2_load"
                }]
            }
        ]
    }

def create_access_denied_modal():
    """Create access denied modal"""
    return {
        "type": "modal",
        "callback_id": "error_modal",
        "title": {"type": "plain_text", "text": "Access Denied"},
        "close": {"type": "plain_text", "text": "Close"},
        "blocks": [{
            "type": "section",
            "text": {"type": "mrkdwn", "text": "❌ You are not authorized to use this feature."}
        }]
    }