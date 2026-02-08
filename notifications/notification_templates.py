NOTIFICATION_TEMPLATES = {
    # CITIZEN TEMPLATES
    'citizen_issue_reported': {
        'title': "Issue Reported Successfully",
        'message': "Your issue '{issue_title}' has been registered. Tracking ID: {issue_id}",
        'priority': 'info'
    },
    
    'citizen_issue_accepted': {
        'title': "Issue Accepted for Action",
        'message': "Your issue has been accepted by {department}. Expected resolution time: {expected_days} days",
        'priority': 'success'
    },
    
    'citizen_issue_resolved': {
        'title': "Issue Resolved!",
        'message': "Great news! Your issue '{issue_title}' has been resolved. Please provide feedback.",
        'priority': 'success',
        'requires_feedback': True
    },
    
    # AUTHORITY TEMPLATES
    'authority_new_assignment': {
        'title': "New Issue Assigned",
        'message': "New issue in your area: {issue_title}. Please acknowledge within 24 hours.",
        'priority': 'high',
        'requires_response': True
    },
    
    'authority_deadline_warning': {
        'title': "Deadline Approaching",
        'message': "Issue #{issue_id} deadline is in {hours_left} hours. Current status: {status}",
        'priority': 'warning'
    },
    
    # COMMUNITY TEMPLATES
    'community_announcement': {
        'title': "Community Announcement",
        'message': "{announcement_text}",
        'priority': 'info'
    },
    
    'volunteer_opportunity': {
        'title': "Volunteer Opportunity",
        'message': "Join us for {event_name} on {event_date}. Location: {location}",
        'priority': 'info'
    },
}