---
name: Daily Standup Reminder
description: Send daily standup reminder message to Discord or Slack channel
id: custom.daily_standup
category: communication
parameters:
  - name: channel
    type: string
    description: The channel to send the reminder to
    required: true
  - name: time
    type: string
    description: Time to send the reminder (in HH:MM format)
    default: "09:00"
  - name: message
    type: string
    description: Custom message template
    default: "🌅 Good morning team! Time for our daily standup. Please share:\n• What you did yesterday\n• What you're working on today\n• Any blockers"
---

# Daily Standup Reminder

Sends a daily reminder message to the team for their standup meeting.

## Instructions

1. Connect to the specified channel (Discord or Slack)
2. Format the reminder message
3. Send the message at the configured time
4. Track successful delivery

## Message Customization

You can customize the message using the following placeholders:
- `{date}` - Current date
- `{day}` - Current day of the week
- `{team}` - Team name if configured

## Example Usage

Configure this skill to run daily at 9:00 AM to remind your team about standup meetings.
