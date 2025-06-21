set orgOutput to ""
log "starting"
tell application "Reminders"
    log "Getting list"
    set queueList to list "Queue"
    log "Iterating over reminders"
    set theReminders to reminders in queueList
    repeat with aReminder in theReminders
        log "processing a reminder"
        set orgOutput to orgOutput & "*" & name of aReminder
	set orgOutput to orgOutput & body of aReminder
    end repeat
end tell

-- Output the ORG to a file or stdout
return orgOutput
