set htmlOutput to "<html><body><ul>"
log "starting"
tell application "Reminders"
    log "Getting list"
    set zoteroList to list "Zotero"
    log "Iterating over reminders"
    set theReminders to reminders in zoteroList
    repeat with aReminder in theReminders
        log "processing a reminder"
        set htmlOutput to htmlOutput & "<li>" & name of aReminder & ":" & body of aReminder & "</li>"
    end repeat
end tell

set htmlOutput to htmlOutput & "</ul></body></html>"

-- Output the HTML to a file or stdout
return htmlOutput
